from repository import OrganizationRepository


class OrganizationService:
    def __init__(self, repo: OrganizationRepository):
        self.repo = repo

    def get_organizations(self, search, city, page, rows, sort_by, sort_type):
        return self.repo.get_organizations(search, city, page, rows, sort_by, sort_type)

    def get_organization(self, organization_id: str):
        return self.repo.get_organization(organization_id)

    def get_organization_providers(self, organization_id: str):
        return self.repo.get_organization_providers(organization_id)

    def get_organization_encounters(self, organization_id: str):
        return self.repo.get_organization_encounters(organization_id)

    def get_organization_resources(self):
        return self.repo.get_organization_resources()
