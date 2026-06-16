from repository import DashboardRepository


class DashboardService:
    def __init__(self, repo: DashboardRepository):
        self.repo = repo

    def get_dashboard(self, range_str: str = "month", provider_id: str | None = None):
        return self.repo.get_dashboard(range_str=range_str, provider_id=provider_id)
