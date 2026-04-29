from repository import EncounterRepository


class EncounterService:
    def __init__(self, repo: EncounterRepository):
        self.repo = repo

    def get_encounters(self, search, encounter_class, date_from, date_to, page, rows, sort_by, sort_type,
                       role=None, patient_id_scope=None, provider_id_scope=None):
        return self.repo.get_encounters(search, encounter_class, date_from, date_to, page, rows, sort_by, sort_type,
                                        role=role, patient_id_scope=patient_id_scope, provider_id_scope=provider_id_scope)

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

    def create_encounter(self, payload, provider_id_scope=None):
        return self.repo.create_encounter(payload, provider_id_scope)

    def update_encounter(self, encounter_id: str, payload, provider_id_scope=None):
        return self.repo.update_encounter(encounter_id, payload, provider_id_scope)

    def delete_encounter(self, encounter_id: str, provider_id_scope=None):
        return self.repo.delete_encounter(encounter_id, provider_id_scope)

    def create_subrecord(self, kind: str, encounter_id: str, payload, provider_id_scope=None):
        return self.repo.create_subrecord(kind, encounter_id, payload, provider_id_scope)

    def update_subrecord(self, kind: str, encounter_id: str, record_id: int, payload, provider_id_scope=None):
        return self.repo.update_subrecord(kind, encounter_id, record_id, payload, provider_id_scope)

    def delete_subrecord(self, kind: str, encounter_id: str, record_id: int, provider_id_scope=None):
        return self.repo.delete_subrecord(kind, encounter_id, record_id, provider_id_scope)
