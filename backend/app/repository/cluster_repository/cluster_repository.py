import json
import re
import base64
from sqlalchemy import func, case, cast, Numeric
from sqlalchemy.orm import Session
from domain import ClusterModel, ClusterDetails, GetClustersDetails, ClusterPatientModel, ClusterMetaModel, PcaPoint, GetClusterStatistics, ChartEntry, FeatureChartData, GetNumericalFeaturesStatistics, CategoricalClusterEntry, CategoricalFeatureChartData, GetCategoricalFeaturesStatistics, AiAnalysisResponse
from service.lllm_sql_agent_service.llm_models import ask_ai
from repository.cluster_repository.cluster_feature_helpers import (
    cluster_size,
    get_avg_age, get_avg_bmi, get_avg_systolic_bp, get_avg_glucose,
    get_avg_qaly, get_avg_daly,
    get_avg_active_conditions, get_avg_medications, get_avg_procedures,
    get_avg_days_since_encounter,
    get_diabetes_pct, get_hypertension_pct, get_heart_disease_pct,
    get_cancer_pct, get_polypharmacy_pct,
    get_smoking_distribution, get_gender_distribution,
    get_dominant_encounter_class, get_dominant_careplan, get_dominant_marital,
    get_population_stats,
)


PROMPT_AI_ANALYSIS = """You are a senior clinical data analyst reviewing a specific patient group identified through K-Prototypes population segmentation in a hospital analytics system.

IMPORTANT RULES:
- Base every claim strictly on the numbers provided. Do not infer traits not supported by the data.
- Gender: describe as "balanced" if 40-60%, "more female/male" if 60-70%, "predominantly female/male" only if >70%.
- Comparisons: use the "vs population avg" deltas to say whether this cluster is above or below average on each metric.
- Translate vitals into plain risk language (e.g. systolic BP >=140 = hypertensive range, glucose >=126 mg/dL = diabetic range, BMI >=30 = obese).
- Let the dominant careplan category guide the clinical framing (Cardiac, Respiratory, Metabolic, Maternal, Musculoskeletal, Psychiatric, Other, none).
- If a value is "N/A" or 0 with no clinical meaning, do not mention that metric.
- Do NOT use em dashes (—) anywhere in your response. Use commas or plain sentence structure instead.

POPULATION CONTEXT:
- {n_patients} patients across {n_clusters} clusters | Silhouette: {silhouette} | Davies-Bouldin: {davies_bouldin}
- Population averages: Age {pop_avg_age} yrs | BMI {pop_avg_bmi} | Systolic BP {pop_avg_systolic_bp} mmHg | Glucose {pop_avg_glucose} mg/dL | QALY {pop_avg_qaly} | DALY {pop_avg_daly} | Active conditions {pop_avg_conditions} | Meds {pop_avg_meds} | Procedures {pop_avg_procedures} | Days since last encounter {pop_avg_days_since}
- Population disease rates: Diabetes {pop_diabetes_pct}% | Hypertension {pop_hypertension_pct}% | Heart disease {pop_heart_pct}% | Cancer {pop_cancer_pct}% | Polypharmacy {pop_polypharmacy_pct}%

THIS CLUSTER - "{title}" ({cluster_type}, {count} patients, {pct}% of population):
Pre-assigned description: {description}

DEMOGRAPHICS:
- Mean age: {avg_age} yrs (vs pop avg {pop_avg_age} yrs)
- Gender: Female {female_pct}% / Male {male_pct}%
- Marital mix (mode): {dominant_marital}

VITALS & QUALITY OF LIFE (mean per patient):
- BMI: {avg_bmi} (vs pop avg {pop_avg_bmi})
- Systolic BP: {avg_systolic_bp} mmHg (vs pop avg {pop_avg_systolic_bp})
- Glucose: {avg_glucose} mg/dL (vs pop avg {pop_avg_glucose})
- QALY: {avg_qaly} (vs pop avg {pop_avg_qaly})
- DALY: {avg_daly} (vs pop avg {pop_avg_daly})

UTILIZATION & BURDEN (mean per patient):
- Active conditions: {avg_conditions} (vs pop avg {pop_avg_conditions})
- Medications: {avg_meds} (vs pop avg {pop_avg_meds})
- Total procedures: {avg_procedures} (vs pop avg {pop_avg_procedures})
- Days since last encounter: {avg_days_since} (vs pop avg {pop_avg_days_since})
- Dominant encounter class: {dominant_encounter}
- Dominant careplan category: {dominant_careplan}

DISEASE PREVALENCE:
- Diabetes: {diabetes_pct}% (vs pop {pop_diabetes_pct}%)
- Hypertension: {hypertension_pct}% (vs pop {pop_hypertension_pct}%)
- Heart disease: {heart_disease_pct}% (vs pop {pop_heart_pct}%)
- Cancer: {cancer_pct}% (vs pop {pop_cancer_pct}%)
- Polypharmacy (>=5 active meds): {polypharmacy_pct}% (vs pop {pop_polypharmacy_pct}%)
- Current smokers: {current_smoker_pct}% | Former: {former_smoker_pct}% | Never: {never_smoker_pct}%

---
TASK: Analyse this patient group for TWO audiences simultaneously:
1. CLINICIANS - 2-3 sentences: what defines this group clinically (anchor on dominant careplan + top prevalence deltas), the main risks, and the most actionable care gaps. Reference specific numbers and deltas.
2. GENERAL PUBLIC - 1-2 sentences: who are these patients in plain everyday language, no medical terms.

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

    def _get_meta(self) -> ClusterMetaModel | None:
        return self.db.query(ClusterMetaModel).first()

    def get_all_clusters(self):
        db_clusters = self.db.query(ClusterModel).all()
        if not db_clusters:
            return GetClustersDetails(total_patients=0, clusters=[])

        total_patients = self.db.query(ClusterPatientModel).count()
        if total_patients == 0:
            return GetClustersDetails(total_patients=0, clusters=[])

        stats_rows = (
            self.db.query(
                ClusterPatientModel.cluster_label,
                func.round(func.avg(cast(ClusterPatientModel.features["age"].astext, Numeric)), 1).label("avg_age"),
                func.round(func.avg(cast(ClusterPatientModel.features["qaly"].astext, Numeric)), 1).label("avg_qaly"),
                func.round(func.avg(cast(ClusterPatientModel.features["total_medications"].astext, Numeric)), 1).label("avg_meds"),
                func.round(func.avg(cast(ClusterPatientModel.features["active_conditions_count"].astext, Numeric)), 1).label("avg_active_conditions"),
                func.round(
                    100.0 * func.count(case(
                        (ClusterPatientModel.features["condition_burden"].astext.in_(["moderate", "high", "very_high"]), 1)
                    )) / func.nullif(func.count(), 0),
                    1,
                ).label("chronic_illness_pct"),
            )
            .group_by(ClusterPatientModel.cluster_label)
            .all()
        )

        stats_map = {}
        for row in stats_rows:
            stats_map[row.cluster_label] = {
                "avg_age": float(row.avg_age or 0),
                "avg_qaly": float(row.avg_qaly or 0),
                "avg_meds": float(row.avg_meds or 0),
                "avg_active_conditions": float(row.avg_active_conditions or 0),
                "chronic_illness_pct": float(row.chronic_illness_pct or 0),
            }

        count_rows = (
            self.db.query(
                ClusterPatientModel.cluster_label,
                func.count().label("cnt"),
            )
            .group_by(ClusterPatientModel.cluster_label)
            .all()
        )
        count_map = {row.cluster_label: row.cnt for row in count_rows}

        parsed_clusters = []

        for cluster in db_clusters:
            c_count = count_map.get(cluster.cluster_label, 0)

            cluster_dict = cluster.model_dump()
            cluster_dict["count"] = c_count
            cluster_dict["percentage"] = round((c_count / total_patients) * 100, 2)

            stats = stats_map.get(cluster.cluster_label, {})
            cluster_dict["avg_age"] = stats.get("avg_age", 0)
            cluster_dict["avg_qaly"] = stats.get("avg_qaly", 0)
            cluster_dict["avg_meds"] = stats.get("avg_meds", 0)
            cluster_dict["avg_active_conditions"] = stats.get("avg_active_conditions", 0)
            cluster_dict["chronic_illness_pct"] = stats.get("chronic_illness_pct", 0)

            parsed_clusters.append(ClusterDetails.model_validate(cluster_dict))

        return GetClustersDetails(total_patients=total_patients, clusters=parsed_clusters)

    def _get_cluster_colors(self) -> dict:
        clusters = self.db.query(ClusterModel.cluster_label, ClusterModel.color).all()
        return {c.cluster_label: c.color for c in clusters}

    def get_cluster_statistics(self) -> GetClusterStatistics:
        rows = (
            self.db.query(
                ClusterPatientModel.pca_x,
                ClusterPatientModel.pca_y,
                ClusterPatientModel.cluster_label,
                ClusterPatientModel.is_outlier,
            )
            .filter(
                ClusterPatientModel.pca_x.isnot(None),
                ClusterPatientModel.pca_y.isnot(None),
            )
            .all()
        )

        if not rows:
            return GetClusterStatistics(points=[])

        points = [
            PcaPoint(x=row.pca_x, y=row.pca_y, cluster=row.cluster_label, is_outlier=row.is_outlier)
            for row in rows
        ]

        meta = self._get_meta()
        heatmap_b64 = base64.b64encode(meta.heatmap).decode() if meta and meta.heatmap else None
        cluster_colors = self._get_cluster_colors()

        return GetClusterStatistics(points=points, heatmap=heatmap_b64, cluster_colors=cluster_colors)

    def get_numerical_features_statistics(self) -> GetNumericalFeaturesStatistics:
        meta = self._get_meta()
        if not meta or not meta.numerical_features:
            return GetNumericalFeaturesStatistics(features=[])

        numerical_features = meta.numerical_features

        select_exprs = []
        for f in numerical_features:
            col = cast(ClusterPatientModel.features[f].astext, Numeric)
            select_exprs.append(func.avg(col).label(f"{f}_mean"))
            select_exprs.append(
                func.percentile_cont(0.5).within_group(col).label(f"{f}_median")
            )

        rows = (
            self.db.query(ClusterPatientModel.cluster_label, *select_exprs)
            .filter(ClusterPatientModel.is_outlier == False)
            .group_by(ClusterPatientModel.cluster_label)
            .order_by(ClusterPatientModel.cluster_label)
            .all()
        )

        result = []
        for feature in numerical_features:
            data = []
            for row in rows:
                mean_val = round(float(getattr(row, f"{feature}_mean") or 0), 2)
                label = row.cluster_label
                data.append(ChartEntry(
                    name=f"Cluster {label}",
                    value=mean_val,
                    tooltip=f"Cluster {label} · Mean: {mean_val}",
                ))
            result.append(FeatureChartData(feature=feature, data=data))

        cluster_colors = self._get_cluster_colors()
        return GetNumericalFeaturesStatistics(features=result, cluster_colors=cluster_colors)

    def get_categorical_features_statistics(self) -> GetCategoricalFeaturesStatistics:
        meta = self._get_meta()
        if not meta or not meta.categorical_features:
            return GetCategoricalFeaturesStatistics(features=[])

        categorical_features = meta.categorical_features
        result = []

        for feature in categorical_features:
            rows = (
                self.db.query(
                    ClusterPatientModel.cluster_label,
                    ClusterPatientModel.features[feature].astext.label("cat_val"),
                    func.count().label("cnt"),
                )
                .filter(ClusterPatientModel.is_outlier == False)
                .group_by(
                    ClusterPatientModel.cluster_label,
                    ClusterPatientModel.features[feature].astext,
                )
                .order_by(ClusterPatientModel.cluster_label)
                .all()
            )

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

        cluster_colors = self._get_cluster_colors()
        return GetCategoricalFeaturesStatistics(features=result, cluster_colors=cluster_colors)

    def get_ai_analysis(self, cluster_id: int) -> AiAnalysisResponse:
        meta = self._get_meta()
        if not meta:
            raise ValueError("No clustering data found")

        cluster = self.db.query(ClusterModel).filter(
            ClusterModel.cluster_label == cluster_id,
        ).first()
        if not cluster:
            raise ValueError(f"Cluster {cluster_id} not found")

        if cluster.ai_analysis:
            return AiAnalysisResponse(**cluster.ai_analysis)

        is_outlier_cluster = cluster_id == -1
        cluster_type = "outlier group" if is_outlier_cluster else "regular cluster"

        size = cluster_size(self.db, cluster_id)
        count = size["count"]
        pct = size["percentage"]

        gender = get_gender_distribution(self.db, cluster_id)
        smoking = get_smoking_distribution(self.db, cluster_id)
        pop = get_population_stats(self.db)
        metrics = meta.metrics or {}

        prompt = PROMPT_AI_ANALYSIS.format(
            n_patients=meta.n_patients,
            n_clusters=meta.n_clusters,
            silhouette=round(metrics.get("silhouette", 0), 3),
            davies_bouldin=round(metrics.get("davies_bouldin", 0), 3),
            pop_avg_age=pop.get("pop_avg_age", "N/A"),
            pop_avg_bmi=pop.get("pop_avg_bmi", "N/A"),
            pop_avg_systolic_bp=pop.get("pop_avg_systolic_bp", "N/A"),
            pop_avg_glucose=pop.get("pop_avg_glucose", "N/A"),
            pop_avg_qaly=pop.get("pop_avg_qaly", "N/A"),
            pop_avg_daly=pop.get("pop_avg_daly", "N/A"),
            pop_avg_meds=pop.get("pop_avg_meds", "N/A"),
            pop_avg_procedures=pop.get("pop_avg_procedures", "N/A"),
            pop_avg_conditions=pop.get("pop_avg_conditions", "N/A"),
            pop_avg_days_since=pop.get("pop_avg_days_since", "N/A"),
            pop_diabetes_pct=pop.get("pop_diabetes_pct", "N/A"),
            pop_hypertension_pct=pop.get("pop_hypertension_pct", "N/A"),
            pop_heart_pct=pop.get("pop_heart_pct", "N/A"),
            pop_cancer_pct=pop.get("pop_cancer_pct", "N/A"),
            pop_polypharmacy_pct=pop.get("pop_polypharmacy_pct", "N/A"),
            title=cluster.title,
            cluster_type=cluster_type,
            count=count,
            pct=pct,
            description=cluster.description,
            avg_age=get_avg_age(self.db, cluster_id),
            avg_bmi=get_avg_bmi(self.db, cluster_id),
            avg_systolic_bp=get_avg_systolic_bp(self.db, cluster_id),
            avg_glucose=get_avg_glucose(self.db, cluster_id),
            avg_qaly=get_avg_qaly(self.db, cluster_id),
            avg_daly=get_avg_daly(self.db, cluster_id),
            avg_meds=get_avg_medications(self.db, cluster_id),
            avg_procedures=get_avg_procedures(self.db, cluster_id),
            avg_conditions=get_avg_active_conditions(self.db, cluster_id),
            avg_days_since=get_avg_days_since_encounter(self.db, cluster_id),
            female_pct=gender["F"],
            male_pct=gender["M"],
            diabetes_pct=get_diabetes_pct(self.db, cluster_id),
            hypertension_pct=get_hypertension_pct(self.db, cluster_id),
            heart_disease_pct=get_heart_disease_pct(self.db, cluster_id),
            cancer_pct=get_cancer_pct(self.db, cluster_id),
            polypharmacy_pct=get_polypharmacy_pct(self.db, cluster_id),
            current_smoker_pct=smoking["current"],
            former_smoker_pct=smoking["former"],
            never_smoker_pct=smoking["never"],
            dominant_encounter=get_dominant_encounter_class(self.db, cluster_id),
            dominant_careplan=get_dominant_careplan(self.db, cluster_id),
            dominant_marital=get_dominant_marital(self.db, cluster_id),
        )

        raw_response = ask_ai(prompt)
        analysis = _parse_ai_json(raw_response)

        self.db.query(ClusterModel).filter(ClusterModel.id == cluster.id).update(
            {"ai_analysis": analysis}, synchronize_session="fetch"
        )
        self.db.commit()

        return AiAnalysisResponse(**analysis)


def _parse_ai_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?\s*(.*?)\s*```", r"\1", text, flags=re.DOTALL)
    return json.loads(text.strip())
