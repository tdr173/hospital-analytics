from repository import ProviderRepository


class ProviderService:
    def __init__(self, repo: ProviderRepository):
        self.repo = repo

    def get_providers(self, search, gender, speciality, city, page, rows, sort_by, sort_type):
        return self.repo.get_providers(search, gender, speciality, city, page, rows, sort_by, sort_type)

    def get_provider(self, provider_id: str):
        return self.repo.get_provider(provider_id)

    def get_provider_encounters(self, provider_id: str, page: int = 1, page_size: int = 20):
        return self.repo.get_provider_encounters(provider_id, page, page_size)

    def get_provider_resources(self):
        return self.repo.get_provider_resources()

    def create_provider(self, payload):
        return self.repo.create_provider(payload)

    def update_provider(self, provider_id: str, payload):
        return self.repo.update_provider(provider_id, payload)

    def delete_provider(self, provider_id: str):
        return self.repo.delete_provider(provider_id)
