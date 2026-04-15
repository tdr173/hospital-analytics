from repository import SequenceRepository


class SequenceService:
    def __init__(self, repo: SequenceRepository):
        self.repo = repo

    def get_ai_analysis(self, pattern_id: int):
        return self.repo.get_sequence_ai_analysis(pattern_id)
