import json
import re
import base64
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from domain import ClusterModel, ClusterDetails, GetClustersDetails, ClusterPatientModel, ClusterRunModel, PcaPoint, GetClusterStatistics, ChartEntry, FeatureChartData, GetNumericalFeaturesStatistics, CategoricalClusterEntry, CategoricalFeatureChartData, GetCategoricalFeaturesStatistics, AiAnalysisResponse
from service.lllm_sql_agent_service.llm_models import ask_ai


PROMPT_AI_ANALYSIS = """You are a senior clinical data analyst reviewing a specific patient group identified through K-Prototypes population segmentation in a hospital analytics system.

IMPORTANT RULES:
- Base every claim strictly on the numbers provided. Do not infer traits not supported by the data.
- Gender: describe as "balanced" if 40-60%, "more female/male" if 60-70%, "predominantly female/male" only if >70%.
- Age: describe age groups by actual percentages, do not reduce to a single descriptor if multiple groups are significant.
- Comparisons: use the "vs population avg" deltas to say whether this cluster is above or below average on each metric.
- If a value is "N/A", do not mention that metric.
- Do NOT use em dashes (—) anywhere in your response. Use commas or plain sentence structure instead.

POPULATION CONTEXT:
- {n_patients} patients across {n_clusters} clusters | Silhouette: {silhouette} | Davies-Bouldin: {davies_bouldin}
- Population averages: Age {pop_avg_age} yrs | QALY {pop_avg_qaly} | Meds {pop_avg_meds} | Emergency visits {pop_avg_emergency} | Wellness visits {pop_avg_wellness} | Procedures {pop_avg_procedures} | Ambulatory {pop_avg_ambulatory} | Outpatient {pop_avg_outpatient}
- Population disease rates: Diabetes {pop_diabetes_pct}% | Hypertension {pop_hypertension_pct}% | Obesity {pop_obesity_pct}%

THIS CLUSTER - "{title}" ({cluster_type}, {count} patients, {pct}% of population):
Pre-assigned description: {description}

DEMOGRAPHICS:
- Mean age: {avg_age} yrs (vs pop avg {pop_avg_age} yrs)
- Gender: Female {female_pct}% / Male {male_pct}%
- Age groups: child {age_child_pct}% | young_adult {age_young_adult_pct}% | middle_aged {age_middle_aged_pct}% | senior {age_senior_pct}% | elderly {age_elderly_pct}%
- BMI: normal {bmi_normal_pct}% | overweight {bmi_overweight_pct}% | obese {bmi_obese_pct}% | underweight {bmi_underweight_pct}%

UTILIZATION (mean per patient):
- Medications: {avg_meds} (vs pop avg {pop_avg_meds})
- Total procedures: {avg_procedures} (vs pop avg {pop_avg_procedures})
- Emergency visits: {avg_emergency} (vs pop avg {pop_avg_emergency})
- Wellness visits: {avg_wellness} (vs pop avg {pop_avg_wellness})
- Ambulatory visits: {avg_ambulatory} (vs pop avg {pop_avg_ambulatory})
- Outpatient visits: {avg_outpatient} (vs pop avg {pop_avg_outpatient})
- Active conditions: {avg_conditions}
- QALY: {avg_qaly} (vs pop avg {pop_avg_qaly})
- Dominant encounter type: {dominant_encounter}

DISEASE BURDEN:
- Diabetes: {diabetes_pct}% (vs pop {pop_diabetes_pct}%) | Hypertension: {hypertension_pct}% (vs pop {pop_hypertension_pct}%) | Heart disease: {heart_disease_pct}% | Obesity (BMI≥30): {obesity_pct}% (vs pop {pop_obesity_pct}%)
- Condition burden: low {burden_low_pct}% | moderate {burden_moderate_pct}% | high {burden_high_pct}% | very_high {burden_very_high_pct}%
- Medication intensity: low {med_low_pct}% | moderate {med_moderate_pct}% | high {med_high_pct}% | very_high {med_very_high_pct}%
- Current smokers: {current_smoker_pct}%

---
TASK: Analyse this patient group for TWO audiences simultaneously:
1. CLINICIANS — 2-3 sentences: what defines this group clinically, what are the main risks, and what care gaps are most actionable. Reference specific numbers from the data above. Highlight what is notably above or below the population average.
2. GENERAL PUBLIC — 1-2 sentences: who are these patients in plain everyday language, no medical terms.

Respond ONLY with valid JSON (no markdown, no extra text):
{{
  "risk_level": "high or moderate or low",
  "medical_interpretation": "...",
  "layperson_summary": "...",
  "key_characteristics": ["data-grounded characteristic 1", "data-grounded characteristic 2", "data-grounded characteristic 3", "data-grounded characteristic 4"],
  "priority_interventions": ["specific actionable clinical intervention 1", "specific actionable clinical intervention 2", "specific actionable clinical intervention 3"],
  "care_recommendations": ["longer-term system-level recommendation 1", "longer-term system-level recommendation 2", "longer-term system-level recommendation 3"]
}}
"""


class ClusterRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_clusters(self):
        latest_run_id = self.db.query(func.max(ClusterModel.run_id)).scalar()

        if not latest_run_id:
            return GetClustersDetails(total_patients=0, clusters=[])

        total_patients = self.db.query(ClusterPatientModel).filter(
            ClusterPatientModel.run_id == latest_run_id
        ).count()

        if total_patients == 0:
            return GetClustersDetails(total_patients=0, clusters=[])

        db_clusters = self.db.query(ClusterModel).filter(
            ClusterModel.run_id == latest_run_id
        ).all()

        # Compute stats per cluster in one query
        stats_query = self.db.execute(text("""
            SELECT
                cluster_label,
                ROUND(AVG((features->>'age')::numeric), 1) AS avg_age,
                ROUND(AVG((features->>'qaly')::numeric), 1) AS avg_qaly,
                ROUND(AVG((features->>'total_medications')::numeric), 1) AS avg_meds,
                ROUND(
                    100.0 * COUNT(*) FILTER (
                        WHERE features->>'condition_burden' IN ('moderate', 'high', 'very_high')
                    ) / NULLIF(COUNT(*), 0),
                    1
                ) AS chronic_illness_pct
            FROM cluster_patient
            WHERE run_id = :run_id
            GROUP BY cluster_label
        """), {"run_id": latest_run_id})

        stats_map = {}
        for row in stats_query.mappings():
            stats_map[row["cluster_label"]] = {
                "avg_age": float(row["avg_age"] or 0),
                "avg_qaly": float(row["avg_qaly"] or 0),
                "avg_meds": float(row["avg_meds"] or 0),
                "chronic_illness_pct": float(row["chronic_illness_pct"] or 0),
            }

        parsed_clusters = []

        for cluster in db_clusters:
            c_count = self.db.query(ClusterPatientModel).filter(
                ClusterPatientModel.cluster_label == cluster.cluster_label,
                ClusterPatientModel.run_id == latest_run_id
            ).count()

            cluster_dict = cluster.model_dump()
            cluster_dict["count"] = c_count
            cluster_dict["percentage"] = round((c_count / total_patients) * 100, 2)

            stats = stats_map.get(cluster.cluster_label, {})
            cluster_dict["avg_age"] = stats.get("avg_age", 0)
            cluster_dict["avg_qaly"] = stats.get("avg_qaly", 0)
            cluster_dict["avg_meds"] = stats.get("avg_meds", 0)
            cluster_dict["chronic_illness_pct"] = stats.get("chronic_illness_pct", 0)

            parsed_clusters.append(ClusterDetails.model_validate(cluster_dict))

        return GetClustersDetails(total_patients=total_patients, clusters=parsed_clusters)

    def _get_cluster_colors(self, run_id: int) -> dict:
        clusters = self.db.query(ClusterModel.cluster_label, ClusterModel.color).filter(
            ClusterModel.run_id == run_id
        ).all()
        return {c.cluster_label: c.color for c in clusters}

    def get_cluster_statistics(self) -> GetClusterStatistics:
        latest_run_id = self.db.query(func.max(ClusterModel.run_id)).scalar()

        if not latest_run_id:
            return GetClusterStatistics(points=[])

        rows = self.db.execute(text("""
            SELECT pca_x, pca_y, cluster_label, is_outlier
            FROM cluster_patient
            WHERE run_id = :run_id
              AND pca_x IS NOT NULL
              AND pca_y IS NOT NULL
        """), {"run_id": latest_run_id}).mappings().all()

        points = [
            PcaPoint(x=row["pca_x"], y=row["pca_y"], cluster=row["cluster_label"], is_outlier=row["is_outlier"])
            for row in rows
        ]

        run = self.db.query(ClusterRunModel.heatmap).filter(ClusterRunModel.id == latest_run_id).first()
        heatmap_b64 = base64.b64encode(run[0]).decode() if run and run[0] else None

        cluster_colors = self._get_cluster_colors(latest_run_id)

        return GetClusterStatistics(points=points, heatmap=heatmap_b64, cluster_colors=cluster_colors)

    def get_numerical_features_statistics(self) -> GetNumericalFeaturesStatistics:
        latest_run_id = self.db.query(func.max(ClusterModel.run_id)).scalar()
        if not latest_run_id:
            return GetNumericalFeaturesStatistics(features=[])

        run = self.db.query(ClusterRunModel.numerical_features).filter(ClusterRunModel.id == latest_run_id).first()
        if not run or not run[0]:
            return GetNumericalFeaturesStatistics(features=[])

        numerical_features = run[0]

        select_parts = ", ".join(
            f"AVG((features->>'{f}')::numeric) AS {f}_mean, "
            f"PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (features->>'{f}')::numeric) AS {f}_median"
            for f in numerical_features
        )

        rows = self.db.execute(text(f"""
            SELECT cluster_label, {select_parts}
            FROM cluster_patient
            WHERE run_id = :run_id AND NOT is_outlier
            GROUP BY cluster_label
            ORDER BY cluster_label
        """), {"run_id": latest_run_id}).mappings().all()

        result = []
        for feature in numerical_features:
            data = []
            for row in rows:
                mean_val = round(float(row[f"{feature}_mean"] or 0), 2)
                median_val = round(float(row[f"{feature}_median"] or 0), 2)
                label = row["cluster_label"]
                data.append(ChartEntry(
                    name=f"Cluster {label}",
                    value=mean_val,
                    tooltip=f"Cluster {label} · Mean: {mean_val}",
                ))
            result.append(FeatureChartData(feature=feature, data=data))

        cluster_colors = self._get_cluster_colors(latest_run_id)

        return GetNumericalFeaturesStatistics(features=result, cluster_colors=cluster_colors)

    def get_categorical_features_statistics(self) -> GetCategoricalFeaturesStatistics:
        latest_run_id = self.db.query(func.max(ClusterModel.run_id)).scalar()
        if not latest_run_id:
            return GetCategoricalFeaturesStatistics(features=[])

        run = self.db.query(ClusterRunModel.categorical_features).filter(ClusterRunModel.id == latest_run_id).first()
        if not run or not run[0]:
            return GetCategoricalFeaturesStatistics(features=[])

        categorical_features = run[0]
        result = []

        for feature in categorical_features:
            rows = self.db.execute(text(f"""
                SELECT cluster_label, features->>'{feature}' AS cat_val, COUNT(*) AS cnt
                FROM cluster_patient
                WHERE run_id = :run_id AND NOT is_outlier
                GROUP BY cluster_label, features->>'{feature}'
                ORDER BY cluster_label
            """), {"run_id": latest_run_id}).mappings().all()

            # compute proportions per cluster
            totals: dict[int, int] = {}
            counts: dict[int, dict[str, int]] = {}
            for row in rows:
                cl = row["cluster_label"]
                cat = row["cat_val"] or "unknown"
                cnt = int(row["cnt"])
                totals[cl] = totals.get(cl, 0) + cnt
                counts.setdefault(cl, {})[cat] = cnt

            all_categories = sorted({row["cat_val"] or "unknown" for row in rows})

            data = []
            for cl in sorted(totals.keys()):
                total = totals[cl]
                proportions = {
                    cat: round(counts[cl].get(cat, 0) / total, 4)
                    for cat in all_categories
                }
                data.append(CategoricalClusterEntry(cluster_id=cl, proportions=proportions))

            result.append(CategoricalFeatureChartData(feature=feature, categories=all_categories, data=data))

        cluster_colors = self._get_cluster_colors(latest_run_id)
        return GetCategoricalFeaturesStatistics(features=result, cluster_colors=cluster_colors)

    def get_ai_analysis(self, cluster_id: int) -> AiAnalysisResponse:
        latest_run_id = self.db.query(func.max(ClusterRunModel.id)).scalar()
        if not latest_run_id:
            raise ValueError("No clustering run found")

        cluster = self.db.query(ClusterModel).filter(
            ClusterModel.run_id == latest_run_id,
            ClusterModel.cluster_label == cluster_id,
        ).first()
        if not cluster:
            raise ValueError(f"Cluster {cluster_id} not found")

        # Return cached result if available
        if cluster.ai_analysis:
            d = cluster.ai_analysis
            return AiAnalysisResponse(**d)

        run = self.db.query(ClusterRunModel).filter(ClusterRunModel.id == latest_run_id).first()

        total_patients = self.db.query(ClusterPatientModel).filter(
            ClusterPatientModel.run_id == latest_run_id,
            ClusterPatientModel.is_outlier == False,
        ).count()

        is_outlier_cluster = cluster_id == -1
        cluster_type = "outlier group" if is_outlier_cluster else "regular cluster"
        # For outlier cluster use is_outlier = TRUE, for regular clusters use the specific cluster_label
        if is_outlier_cluster:
            cluster_filter = "is_outlier = TRUE"
        else:
            cluster_filter = f"cluster_label = {cluster_id} AND NOT is_outlier"

        # Per-cluster stats (single cluster)
        stats_row = self.db.execute(text(f"""
            SELECT
                COUNT(*) AS patient_count,
                ROUND(AVG((features->>'age')::numeric), 1) AS avg_age,
                ROUND(AVG((features->>'qaly')::numeric), 2) AS avg_qaly,
                ROUND(AVG((features->>'total_medications')::numeric), 1) AS avg_meds,
                ROUND(AVG((features->>'total_procedures')::numeric), 1) AS avg_procedures,
                ROUND(AVG((features->>'emergency_count')::numeric), 1) AS avg_emergency,
                ROUND(AVG((features->>'wellness_count')::numeric), 1) AS avg_wellness,
                ROUND(AVG((features->>'ambulatory_count')::numeric), 1) AS avg_ambulatory,
                ROUND(AVG((features->>'outpatient_count')::numeric), 1) AS avg_outpatient,
                ROUND(AVG((features->>'active_conditions_count')::numeric), 1) AS avg_conditions,
                ROUND(100.0 * SUM(CASE WHEN features->>'has_diabetes' = 'Yes' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS diabetes_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'has_hypertension' = 'Yes' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS hypertension_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'has_heart_disease' = 'Yes' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS heart_disease_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'has_obesity' = 'Yes' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS obesity_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'smoking_status' = 'current' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS current_smoker_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'gender' = 'F' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS female_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'gender' = 'M' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS male_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'age_group' = 'child' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS age_child_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'age_group' = 'young_adult' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS age_young_adult_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'age_group' = 'middle_aged' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS age_middle_aged_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'age_group' = 'senior' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS age_senior_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'age_group' = 'elderly' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS age_elderly_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'bmi_category' = 'Normal' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS bmi_normal_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'bmi_category' = 'Overweight' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS bmi_overweight_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'bmi_category' = 'Obese' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS bmi_obese_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'bmi_category' = 'Underweight' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS bmi_underweight_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'condition_burden' = 'low' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS burden_low_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'condition_burden' = 'moderate' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS burden_moderate_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'condition_burden' = 'high' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS burden_high_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'condition_burden' = 'very_high' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS burden_very_high_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'medication_intensity' = 'low' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS med_low_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'medication_intensity' = 'moderate' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS med_moderate_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'medication_intensity' = 'high' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS med_high_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'medication_intensity' = 'very_high' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS med_very_high_pct,
                MODE() WITHIN GROUP (ORDER BY features->>'dominant_encounter_class') AS dominant_encounter
            FROM cluster_patient
            WHERE run_id = :run_id AND {cluster_filter}
        """), {"run_id": latest_run_id}).mappings().first()

        s = dict(stats_row) if stats_row else {}

        # Population averages (across all non-outlier patients)
        pop_row = self.db.execute(text("""
            SELECT
                ROUND(AVG((features->>'age')::numeric), 1) AS pop_avg_age,
                ROUND(AVG((features->>'qaly')::numeric), 2) AS pop_avg_qaly,
                ROUND(AVG((features->>'total_medications')::numeric), 1) AS pop_avg_meds,
                ROUND(AVG((features->>'total_procedures')::numeric), 1) AS pop_avg_procedures,
                ROUND(AVG((features->>'emergency_count')::numeric), 1) AS pop_avg_emergency,
                ROUND(AVG((features->>'wellness_count')::numeric), 1) AS pop_avg_wellness,
                ROUND(AVG((features->>'ambulatory_count')::numeric), 1) AS pop_avg_ambulatory,
                ROUND(AVG((features->>'outpatient_count')::numeric), 1) AS pop_avg_outpatient,
                ROUND(100.0 * SUM(CASE WHEN features->>'has_diabetes' = 'Yes' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS pop_diabetes_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'has_hypertension' = 'Yes' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS pop_hypertension_pct,
                ROUND(100.0 * SUM(CASE WHEN features->>'has_obesity' = 'Yes' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS pop_obesity_pct
            FROM cluster_patient
            WHERE run_id = :run_id AND NOT is_outlier
        """), {"run_id": latest_run_id}).mappings().first()

        count = s.get("patient_count", 0)
        ref_population = total_patients if not is_outlier_cluster else (
            self.db.query(ClusterPatientModel).filter(
                ClusterPatientModel.run_id == latest_run_id
            ).count()
        )
        pct = round(count / ref_population * 100, 1) if ref_population > 0 else 0
        metrics = run.metrics or {}

        def p(key):
            return pop_row[key] if pop_row else "N/A"

        prompt = PROMPT_AI_ANALYSIS.format(
            n_patients=total_patients,
            n_clusters=run.n_clusters,
            silhouette=round(metrics.get("silhouette", 0), 3),
            davies_bouldin=round(metrics.get("davies_bouldin", 0), 3),
            pop_avg_age=p("pop_avg_age"),
            pop_avg_qaly=p("pop_avg_qaly"),
            pop_avg_meds=p("pop_avg_meds"),
            pop_avg_procedures=p("pop_avg_procedures"),
            pop_avg_emergency=p("pop_avg_emergency"),
            pop_avg_wellness=p("pop_avg_wellness"),
            pop_avg_ambulatory=p("pop_avg_ambulatory"),
            pop_avg_outpatient=p("pop_avg_outpatient"),
            pop_diabetes_pct=p("pop_diabetes_pct"),
            pop_hypertension_pct=p("pop_hypertension_pct"),
            pop_obesity_pct=p("pop_obesity_pct"),
            title=cluster.title,
            cluster_type=cluster_type,
            count=count,
            pct=pct,
            description=cluster.description,
            avg_age=s.get("avg_age", "N/A"),
            female_pct=s.get("female_pct", "N/A"),
            male_pct=s.get("male_pct", "N/A"),
            age_child_pct=s.get("age_child_pct", "N/A"),
            age_young_adult_pct=s.get("age_young_adult_pct", "N/A"),
            age_middle_aged_pct=s.get("age_middle_aged_pct", "N/A"),
            age_senior_pct=s.get("age_senior_pct", "N/A"),
            age_elderly_pct=s.get("age_elderly_pct", "N/A"),
            bmi_normal_pct=s.get("bmi_normal_pct", "N/A"),
            bmi_overweight_pct=s.get("bmi_overweight_pct", "N/A"),
            bmi_obese_pct=s.get("bmi_obese_pct", "N/A"),
            bmi_underweight_pct=s.get("bmi_underweight_pct", "N/A"),
            avg_qaly=s.get("avg_qaly", "N/A"),
            avg_meds=s.get("avg_meds", "N/A"),
            avg_procedures=s.get("avg_procedures", "N/A"),
            avg_emergency=s.get("avg_emergency", "N/A"),
            avg_wellness=s.get("avg_wellness", "N/A"),
            avg_ambulatory=s.get("avg_ambulatory", "N/A"),
            avg_outpatient=s.get("avg_outpatient", "N/A"),
            avg_conditions=s.get("avg_conditions", "N/A"),
            diabetes_pct=s.get("diabetes_pct", "N/A"),
            hypertension_pct=s.get("hypertension_pct", "N/A"),
            heart_disease_pct=s.get("heart_disease_pct", "N/A"),
            obesity_pct=s.get("obesity_pct", "N/A"),
            burden_low_pct=s.get("burden_low_pct", "N/A"),
            burden_moderate_pct=s.get("burden_moderate_pct", "N/A"),
            burden_high_pct=s.get("burden_high_pct", "N/A"),
            burden_very_high_pct=s.get("burden_very_high_pct", "N/A"),
            med_low_pct=s.get("med_low_pct", "N/A"),
            med_moderate_pct=s.get("med_moderate_pct", "N/A"),
            med_high_pct=s.get("med_high_pct", "N/A"),
            med_very_high_pct=s.get("med_very_high_pct", "N/A"),
            current_smoker_pct=s.get("current_smoker_pct", "N/A"),
            dominant_encounter=s.get("dominant_encounter", "N/A"),
        )

        raw_response = ask_ai(prompt)
        analysis = _parse_ai_json(raw_response)

        # Cache in cluster row
        self.db.execute(
            text("UPDATE cluster SET ai_analysis = :data WHERE id = :id"),
            {"data": json.dumps(analysis), "id": cluster.id}
        )
        self.db.commit()

        return AiAnalysisResponse(**analysis)


def _parse_ai_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?\s*(.*?)\s*```", r"\1", text, flags=re.DOTALL)
    return json.loads(text.strip())
