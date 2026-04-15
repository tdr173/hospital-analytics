from repository import EncounterRepository


class EncounterService:
    def __init__(self, repo: EncounterRepository):
        self.repo = repo

    def get_encounters(self, search, encounter_class, date_from, date_to, page, rows, sort_by, sort_type):
        return self.repo.get_encounters(search, encounter_class, date_from, date_to, page, rows, sort_by, sort_type)

    def get_encounter(self, encounter_id: str):
        return self.repo.get_encounter(encounter_id)

    def get_encounter_observations(self, encounter_id: str):
        return self.repo.get_encounter_observations(encounter_id)

    def get_encounter_conditions(self, encounter_id: str):
        return self.repo.get_encounter_conditions(encounter_id)

    def get_encounter_medications(self, encounter_id: str):
        return self.repo.get_encounter_medications(encounter_id)

    def get_encounter_procedures(self, encounter_id: str):
        return self.repo.get_encounter_procedures(encounter_id)

    def get_encounter_immunizations(self, encounter_id: str):
        return self.repo.get_encounter_immunizations(encounter_id)

    def get_encounter_careplans(self, encounter_id: str):
        return self.repo.get_encounter_careplans(encounter_id)

    def get_encounter_allergies(self, encounter_id: str):
        return self.repo.get_encounter_allergies(encounter_id)

    def get_encounter_resources(self):
        return self.repo.get_encounter_resources()
