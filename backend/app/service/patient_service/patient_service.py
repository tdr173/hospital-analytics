from typing import Optional
from repository import PatientRepository


class PatientService:
    def __init__(self, repo: PatientRepository):
        self.repo = repo

    def get_patients(self, search, gender, age_group, status, race, marital, city, page, rows, sort_by, sort_type):
        return self.repo.get_patients(search, gender, age_group, status, race, marital, city, page, rows, sort_by, sort_type)

    def get_patient(self, patient_id: str):
        return self.repo.get_patient(patient_id)

    def get_patient_summary(self, patient_id: str):
        return self.repo.get_patient_summary(patient_id)

    def get_patient_conditions(self, patient_id: str):
        return self.repo.get_patient_conditions(patient_id)

    def get_patient_medications(self, patient_id: str):
        return self.repo.get_patient_medications(patient_id)

    def get_patient_procedures(self, patient_id: str):
        return self.repo.get_patient_procedures(patient_id)

    def get_patient_immunizations(self, patient_id: str):
        return self.repo.get_patient_immunizations(patient_id)

    def get_patient_careplans(self, patient_id: str):
        return self.repo.get_patient_careplans(patient_id)

    def get_patient_allergies(self, patient_id: str):
        return self.repo.get_patient_allergies(patient_id)

    def get_patient_encounters(self, patient_id: str):
        return self.repo.get_patient_encounters(patient_id)

    def get_patient_resources(self):
        return self.repo.get_patient_resources()
