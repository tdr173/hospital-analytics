from typing import Optional

from prompts.sequences import PROMPT_SEQUENCE_ANALYSIS
from repository import SequenceRepository
from service._helpers import parse_ai_json
from service.lllm_sql_agent_service.llm_models import ask_ai


class SequenceService:
    def __init__(self, repo: SequenceRepository):
        self.repo = repo

    def get_resources(self):
        return self.repo.get_resources()

    def get_sequences(
        self,
        search: Optional[str] = None,
        min_length: int = 1,
        sort_by: str = "support",
        sort_type: str = "desc",
        page: int = 1,
        rows: int = 8,
        cluster_labels: Optional[list[int]] = None,
    ):
        return self.repo.get_sequences(
            search=search,
            min_length=min_length,
            sort_by=sort_by,
            sort_type=sort_type,
            page=page,
            rows=rows,
            cluster_labels=cluster_labels,
        )

    def get_ai_analysis(self, pattern_id: int) -> dict:
        cached = self.repo.get_pattern_ai_analysis(pattern_id)
        if cached:
            return cached

        # Row-lock the pattern to serialize concurrent requests for the same id.
        locked = self.repo.lock_pattern_ai_analysis(pattern_id)
        if locked:
            return locked

        ctx = self.repo.get_pattern_ai_context(pattern_id)
        prompt = PROMPT_SEQUENCE_ANALYSIS.format(
            **ctx["pattern"],
            **ctx["patient_stats"],
        )

        analysis = parse_ai_json(ask_ai(prompt))
        self.repo.save_pattern_ai_analysis(pattern_id, analysis)
        return analysis
