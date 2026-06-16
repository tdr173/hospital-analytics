from domain import AiAnalysisResponse, ClusterDetailResponse
from prompts.clusters import PROMPT_AI_ANALYSIS
from repository import ClusterRepository
from service._helpers import parse_ai_json
from service.lllm_sql_agent_service.llm_models import ask_ai


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

    def get_cluster_detail(self, cluster_id: int) -> ClusterDetailResponse:
        cached = self.repo.get_cluster_detail_cache(cluster_id)
        if cached is not None:
            return cached
        result = self.repo.get_cluster_detail(cluster_id)
        self.repo.save_cluster_detail_cache(cluster_id, result)
        return result

    def warm_detail_cache(self) -> list[int]:
        """Precompute and persist detail_cache for every cluster that lacks it.

        The per-cluster computation scans millions of observation rows, so this
        is meant to run in the background (e.g. at startup) to keep the first
        page load fast. Returns the labels that were warmed.
        """
        labels = self.repo.get_cluster_labels_missing_detail_cache()
        warmed = []
        for label in labels:
            result = self.repo.get_cluster_detail(label)
            self.repo.save_cluster_detail_cache(label, result)
            warmed.append(label)
        return warmed

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
