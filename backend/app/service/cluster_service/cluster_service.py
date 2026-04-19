from domain import AiAnalysisResponse
from repository import ClusterRepository
from service._helpers import parse_ai_json
from service.lllm_sql_agent_service.llm_models import ask_ai


PROMPT_AI_ANALYSIS = """You are a senior clinical data analyst reviewing a specific patient group identified through K-Prototypes population segmentation in a hospital analytics system.

IMPORTANT RULES:
- Base every claim strictly on the numbers provided. Do not infer traits not supported by the data.
- Gender: describe as "balanced" if 40-60%, "more female/male" if 60-70%, "predominantly female/male" only if >70%.
- Comparisons: use the "vs population avg" deltas to say whether this cluster is above or below average on each metric.
- Translate vitals into plain risk language (e.g. systolic BP >=140 = hypertensive range, glucose >=126 mg/dL = diabetic range, BMI >=30 = obese).
- Let the dominant careplan category guide the clinical framing (Cardiac, Respiratory, Metabolic, Maternal, Musculoskeletal, Psychiatric, Other, none).
- If a value is "N/A" or 0 with no clinical meaning, do not mention that metric.
- Do NOT use em dashes (-) anywhere in your response. Use commas or plain sentence structure instead.

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


def _na(value):
    return value if value is not None else "N/A"


class ClusterService:
    def __init__(self, repo: ClusterRepository):
        self.repo = repo

    def get_all_clusters(self):
        return self.repo.get_all_clusters()

    def get_cluster_statistics(self):
        return self.repo.get_cluster_statistics()

    def get_numerical_features_statistics(self):
        return self.repo.get_numerical_features_statistics()

    def get_categorical_features_statistics(self):
        return self.repo.get_categorical_features_statistics()

    def get_cluster_detail(self, cluster_id: int):
        return self.repo.get_cluster_detail(cluster_id)

    def get_ai_analysis(self, cluster_id: int) -> AiAnalysisResponse:
        # Fast path: no lock, return cached analysis if already computed.
        cached = self.repo.get_cluster_ai_analysis(cluster_id)
        if cached is not None:
            return cached

        # Slow path: acquire row lock and recheck. Concurrent requests for the
        # same cluster block here, so only one LLM call happens.
        locked = self.repo.lock_cluster_ai_analysis(cluster_id)
        if locked is not None:
            return locked

        ctx = self.repo.get_ai_context(cluster_id)
        prompt = self._build_prompt(ctx)

        raw = ask_ai(prompt)
        analysis = parse_ai_json(raw)

        self.repo.save_cluster_ai_analysis(cluster_id, analysis)
        return AiAnalysisResponse(**analysis)

    @staticmethod
    def _build_prompt(ctx: dict) -> str:
        meta = ctx["meta"]
        cluster = ctx["cluster"]
        size = ctx["size"]
        vitals = ctx["vitals"]
        utilization = ctx["utilization"]
        prevalence = ctx["prevalence"]
        dominants = ctx["dominants"]
        gender = ctx["gender"]
        smoking = ctx["smoking"]
        pop = ctx["population"]
        metrics = meta["metrics"]
        is_outlier = cluster["cluster_id"] == -1

        return PROMPT_AI_ANALYSIS.format(
            n_patients=meta["n_patients"],
            n_clusters=meta["n_clusters"],
            silhouette=round(metrics.get("silhouette", 0), 3),
            davies_bouldin=round(metrics.get("davies_bouldin", 0), 3),
            pop_avg_age=_na(pop.get("pop_avg_age")),
            pop_avg_bmi=_na(pop.get("pop_avg_bmi")),
            pop_avg_systolic_bp=_na(pop.get("pop_avg_systolic_bp")),
            pop_avg_glucose=_na(pop.get("pop_avg_glucose")),
            pop_avg_qaly=_na(pop.get("pop_avg_qaly")),
            pop_avg_daly=_na(pop.get("pop_avg_daly")),
            pop_avg_meds=_na(pop.get("pop_avg_meds")),
            pop_avg_procedures=_na(pop.get("pop_avg_procedures")),
            pop_avg_conditions=_na(pop.get("pop_avg_conditions")),
            pop_avg_days_since=_na(pop.get("pop_avg_days_since")),
            pop_diabetes_pct=_na(pop.get("pop_diabetes_pct")),
            pop_hypertension_pct=_na(pop.get("pop_hypertension_pct")),
            pop_heart_pct=_na(pop.get("pop_heart_pct")),
            pop_cancer_pct=_na(pop.get("pop_cancer_pct")),
            pop_polypharmacy_pct=_na(pop.get("pop_polypharmacy_pct")),
            title=cluster["title"],
            cluster_type="outlier group" if is_outlier else "regular cluster",
            count=size["count"],
            pct=size["percentage"],
            description=cluster["description"],
            avg_age=vitals["avg_age"],
            avg_bmi=vitals["avg_bmi"],
            avg_systolic_bp=vitals["avg_systolic_bp"],
            avg_glucose=vitals["avg_glucose"],
            avg_qaly=vitals["avg_qaly"],
            avg_daly=vitals["avg_daly"],
            avg_meds=utilization["avg_medications"],
            avg_procedures=utilization["avg_procedures"],
            avg_conditions=utilization["avg_active_conditions"],
            avg_days_since=utilization["avg_days_since_encounter"],
            female_pct=gender["F"],
            male_pct=gender["M"],
            diabetes_pct=prevalence["diabetes_pct"],
            hypertension_pct=prevalence["hypertension_pct"],
            heart_disease_pct=prevalence["heart_disease_pct"],
            cancer_pct=prevalence["cancer_pct"],
            polypharmacy_pct=prevalence["polypharmacy_pct"],
            current_smoker_pct=smoking["current"],
            former_smoker_pct=smoking["former"],
            never_smoker_pct=smoking["never"],
            dominant_encounter=dominants["dominant_encounter_class"],
            dominant_careplan=dominants["dominant_careplan"],
            dominant_marital=dominants["dominant_marital"],
        )
