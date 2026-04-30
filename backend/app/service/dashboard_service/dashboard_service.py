from repository import DashboardRepository


class DashboardService:
    def __init__(self, repo: DashboardRepository):
        self.repo = repo

    def get_dashboard(self, scope=None):
        return self.repo.get_dashboard(scope)
