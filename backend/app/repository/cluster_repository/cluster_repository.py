import json
import re
import base64
from sqlalchemy import func, case, cast, Numeric
from sqlalchemy.orm import Session
from domain import ClusterModel, ClusterDetails, GetClustersDetails, ClusterPatientModel, ClusterRunModel, PcaPoint, GetClusterStatistics, ChartEntry, FeatureChartData, GetNumericalFeaturesStatistics, CategoricalClusterEntry, CategoricalFeatureChartData, GetCategoricalFeaturesStatistics, AiAnalysisResponse
from service.lllm_sql_agent_service.llm_models import ask_ai


def _avg_feat(feature, decimals=1):
    return func.round(
        func.avg(cast(ClusterPatientModel.features[feature].astext, Numeric)),
        decimals,
    )


def _flag_pct(feature, value):
    return func.round(
        100.0 * func.sum(case(
            (ClusterPatientModel.features[feature].astext == value, 1),
            else_=0,
        )) / func.nullif(func.count(), 0),
        1,
    )


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
        stats_rows = (
            self.db.query(
                ClusterPatientModel.cluster_label,
                func.round(func.avg(cast(ClusterPatientModel.features["age"].astext, Numeric)), 1).label("avg_age"),
                func.round(func.avg(cast(ClusterPatientModel.features["qaly"].astext, Numeric)), 1).label("avg_qaly"),
                func.round(func.avg(cast(ClusterPatientModel.features["total_medications"].astext, Numeric)), 1).label("avg_meds"),
                func.round(
                    100.0 * func.count(case(
                        (ClusterPatientModel.features["condition_burden"].astext.in_(["moderate", "high", "very_high"]), 1)
                    )) / func.nullif(func.count(), 0),
                    1,
                ).label("chronic_illness_pct"),
            )
            .filter(ClusterPatientModel.run_id == latest_run_id)
            .group_by(ClusterPatientModel.cluster_label)
            .all()
        )

        stats_map = {}
        for row in stats_rows:
            stats_map[row.cluster_label] = {
                "avg_age": float(row.avg_age or 0),
                "avg_qaly": float(row.avg_qaly or 0),
                "avg_meds": float(row.avg_meds or 0),
                "chronic_illness_pct": float(row.chronic_illness_pct or 0),
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

        rows = (
            self.db.query(
                ClusterPatientModel.pca_x,
                ClusterPatientModel.pca_y,
                ClusterPatientModel.cluster_label,
                ClusterPatientModel.is_outlier,
            )
            .filter(
                ClusterPatientModel.run_id == latest_run_id,
                ClusterPatientModel.pca_x.isnot(None),
                ClusterPatientModel.pca_y.isnot(None),
            )
            .all()
        )

        points = [
            PcaPoint(x=row.pca_x, y=row.pca_y, cluster=row.cluster_label, is_outlier=row.is_outlier)
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

        select_exprs = []
        for f in numerical_features:
            col = cast(ClusterPatientModel.features[f].astext, Numeric)
            select_exprs.append(func.avg(col).label(f"{f}_mean"))
            select_exprs.append(
                func.percentile_cont(0.5).within_group(col).label(f"{f}_median")
            )

        rows = (
            self.db.query(ClusterPatientModel.cluster_label, *select_exprs)
            .filter(
                ClusterPatientModel.run_id == latest_run_id,
                ClusterPatientModel.is_outlier == False,
            )
            .group_by(ClusterPatientModel.cluster_label)
            .order_by(ClusterPatientModel.cluster_label)
            .all()
        )

        result = []
        for feature in numerical_features:
            data = []
            for row in rows:
                mean_val = round(float(getattr(row, f"{feature}_mean") or 0), 2)
                median_val = round(float(getattr(row, f"{feature}_median") or 0), 2)
                label = row.cluster_label
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
            rows = (
                self.db.query(
                    ClusterPatientModel.cluster_label,
                    ClusterPatientModel.features[feature].astext.label("cat_val"),
                    func.count().label("cnt"),
                )
                .filter(
                    ClusterPatientModel.run_id == latest_run_id,
                    ClusterPatientModel.is_outlier == False,
                )
                .group_by(
                    ClusterPatientModel.cluster_label,
                    ClusterPatientModel.features[feature].astext,
                )
                .order_by(ClusterPatientModel.cluster_label)
                .all()
            )

            # compute proportions per cluster
            totals: dict[int, int] = {}
            counts: dict[int, dict[str, int]] = {}
            for row in rows:
                cl = row.cluster_label
                cat = row.cat_val or "unknown"
                cnt = int(row.cnt)
                totals[cl] = totals.get(cl, 0) + cnt
                counts.setdefault(cl, {})[cat] = cnt

            all_categories = sorted({row.cat_val or "unknown" for row in rows})

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

        if is_outlier_cluster:
            cluster_filters = [ClusterPatientModel.is_outlier == True]
        else:
            cluster_filters = [
                ClusterPatientModel.cluster_label == cluster_id,
                ClusterPatientModel.is_outlier == False,
            ]

        # Per-cluster stats (single cluster)
        stats_row = (
            self.db.query(
                func.count().label("patient_count"),
                _avg_feat("age").label("avg_age"),
                _avg_feat("qaly", 2).label("avg_qaly"),
                _avg_feat("total_medications").label("avg_meds"),
                _avg_feat("total_procedures").label("avg_procedures"),
                _avg_feat("emergency_count").label("avg_emergency"),
                _avg_feat("wellness_count").label("avg_wellness"),
                _avg_feat("ambulatory_count").label("avg_ambulatory"),
                _avg_feat("outpatient_count").label("avg_outpatient"),
                _avg_feat("active_conditions_count").label("avg_conditions"),
                _flag_pct("has_diabetes", "Yes").label("diabetes_pct"),
                _flag_pct("has_hypertension", "Yes").label("hypertension_pct"),
                _flag_pct("has_heart_disease", "Yes").label("heart_disease_pct"),
                _flag_pct("has_obesity", "Yes").label("obesity_pct"),
                _flag_pct("smoking_status", "current").label("current_smoker_pct"),
                _flag_pct("gender", "F").label("female_pct"),
                _flag_pct("gender", "M").label("male_pct"),
                _flag_pct("age_group", "child").label("age_child_pct"),
                _flag_pct("age_group", "young_adult").label("age_young_adult_pct"),
                _flag_pct("age_group", "middle_aged").label("age_middle_aged_pct"),
                _flag_pct("age_group", "senior").label("age_senior_pct"),
                _flag_pct("age_group", "elderly").label("age_elderly_pct"),
                _flag_pct("bmi_category", "Normal").label("bmi_normal_pct"),
                _flag_pct("bmi_category", "Overweight").label("bmi_overweight_pct"),
                _flag_pct("bmi_category", "Obese").label("bmi_obese_pct"),
                _flag_pct("bmi_category", "Underweight").label("bmi_underweight_pct"),
                _flag_pct("condition_burden", "low").label("burden_low_pct"),
                _flag_pct("condition_burden", "moderate").label("burden_moderate_pct"),
                _flag_pct("condition_burden", "high").label("burden_high_pct"),
                _flag_pct("condition_burden", "very_high").label("burden_very_high_pct"),
                _flag_pct("medication_intensity", "low").label("med_low_pct"),
                _flag_pct("medication_intensity", "moderate").label("med_moderate_pct"),
                _flag_pct("medication_intensity", "high").label("med_high_pct"),
                _flag_pct("medication_intensity", "very_high").label("med_very_high_pct"),
                func.mode().within_group(
                    ClusterPatientModel.features["dominant_encounter_class"].astext
                ).label("dominant_encounter"),
            )
            .filter(
                ClusterPatientModel.run_id == latest_run_id,
                *cluster_filters,
            )
            .first()
        )

        s = stats_row._asdict() if stats_row else {}

        # Population averages (across all non-outlier patients)
        pop_row = (
            self.db.query(
                _avg_feat("age").label("pop_avg_age"),
                _avg_feat("qaly", 2).label("pop_avg_qaly"),
                _avg_feat("total_medications").label("pop_avg_meds"),
                _avg_feat("total_procedures").label("pop_avg_procedures"),
                _avg_feat("emergency_count").label("pop_avg_emergency"),
                _avg_feat("wellness_count").label("pop_avg_wellness"),
                _avg_feat("ambulatory_count").label("pop_avg_ambulatory"),
                _avg_feat("outpatient_count").label("pop_avg_outpatient"),
                _flag_pct("has_diabetes", "Yes").label("pop_diabetes_pct"),
                _flag_pct("has_hypertension", "Yes").label("pop_hypertension_pct"),
                _flag_pct("has_obesity", "Yes").label("pop_obesity_pct"),
            )
            .filter(
                ClusterPatientModel.run_id == latest_run_id,
                ClusterPatientModel.is_outlier == False,
            )
            .first()
        )

        count = s.get("patient_count", 0)
        ref_population = total_patients if not is_outlier_cluster else (
            self.db.query(ClusterPatientModel).filter(
                ClusterPatientModel.run_id == latest_run_id
            ).count()
        )
        pct = round(count / ref_population * 100, 1) if ref_population > 0 else 0
        metrics = run.metrics or {}

        pop = pop_row._asdict() if pop_row else None

        def p(key):
            return pop[key] if pop else "N/A"

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
        self.db.query(ClusterModel).filter(ClusterModel.id == cluster.id).update(
            {"ai_analysis": analysis}, synchronize_session="fetch"
        )
        self.db.commit()

        return AiAnalysisResponse(**analysis)


def _parse_ai_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?\s*(.*?)\s*```", r"\1", text, flags=re.DOTALL)
    return json.loads(text.strip())
