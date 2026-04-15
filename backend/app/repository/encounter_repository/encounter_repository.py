from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, case

from domain import (
    PatientModel, ProviderModel, OrganizationModel, EncounterModel,
    ObservationModel, ConditionModel, MedicationModel,
    ProcedureModel, ImmunizationModel, AllergyModel, CarePlanModel,
    EncounterListItem, EncounterListResponse, EncounterDetailResponse,
    EncounterObservationItem, EncounterConditionItem, EncounterMedicationItem,
    EncounterProcedureItem, EncounterImmunizationItem, EncounterAllergyItem,
    EncounterCarePlanItem,
    EncounterResourcesResponse, FilterOption,
)

SORT_COL_MAP = {
    "start_date": EncounterModel.start_date,
    "duration": EncounterModel.duration,
    "encounter_class": EncounterModel.encounter_class,
}

_patient_name_col = case(
    (PatientModel.first_name == PatientModel.last_name,
     func.regexp_replace(PatientModel.first_name, '[0-9]', '', 'g')),
    else_=(
        func.regexp_replace(PatientModel.first_name, '[0-9]', '', 'g')
        + ' '
        + func.regexp_replace(PatientModel.last_name, '[0-9]', '', 'g')
    )
).label("patient_name")

_provider_name_col = case(
    (ProviderModel.first_name == ProviderModel.last_name,
     func.regexp_replace(ProviderModel.first_name, '[0-9]', '', 'g')),
    else_=(
        func.regexp_replace(ProviderModel.first_name, '[0-9]', '', 'g')
        + ' '
        + func.regexp_replace(ProviderModel.last_name, '[0-9]', '', 'g')
    )
).label("provider_name")


class EncounterRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_encounters(
        self,
        search: Optional[str],
        encounter_class: Optional[str],
        date_from: Optional[str],
        date_to: Optional[str],
        page: int,
        rows: int,
        sort_by: str,
        sort_type: str,
    ) -> EncounterListResponse:
        sort_col = SORT_COL_MAP.get(sort_by, EncounterModel.start_date)
        sort_expr = (
            sort_col.asc().nulls_last()
            if sort_type.lower() == "asc"
            else sort_col.desc().nulls_last()
        )

        enc_filters = []
        patient_filters = []

        if search:
            patient_filters.append(or_(
                PatientModel.first_name.ilike(f"%{search}%"),
                PatientModel.last_name.ilike(f"%{search}%"),
            ))

        if encounter_class:
            classes = [c.strip() for c in encounter_class.split(",") if c.strip()]
            if classes:
                enc_filters.append(EncounterModel.encounter_class.in_(classes))

        if date_from:
            enc_filters.append(EncounterModel.start_date >= date_from)

        if date_to:
            enc_filters.append(EncounterModel.start_date <= date_to)

        # Count — join patient only when searching by name
        count_q = self.db.query(func.count(EncounterModel.encounter_id)).filter(*enc_filters)
        if patient_filters:
            count_q = (
                count_q
                .join(PatientModel, EncounterModel.patient_id == PatientModel.patient_id)
                .filter(*patient_filters)
            )
        total = count_q.scalar() or 0

        # Data query — always join all three for display
        offset = (page - 1) * rows
        q = (
            self.db.query(
                EncounterModel.encounter_id,
                EncounterModel.patient_id,
                _patient_name_col,
                _provider_name_col,
                OrganizationModel.name.label("organization_name"),
                EncounterModel.start_date,
                EncounterModel.duration,
                EncounterModel.encounter_class,
                EncounterModel.description,
                EncounterModel.reason_description,
            )
            .join(PatientModel, EncounterModel.patient_id == PatientModel.patient_id)
            .outerjoin(ProviderModel, EncounterModel.provider_id == ProviderModel.provider_id)
            .outerjoin(OrganizationModel, EncounterModel.organization_id == OrganizationModel.organization_id)
            .filter(*enc_filters)
        )
        if patient_filters:
            q = q.filter(*patient_filters)

        rows_data = q.order_by(sort_expr).limit(rows).offset(offset).all()
        items = [EncounterListItem(**r._asdict()) for r in rows_data]
        return EncounterListResponse(items=items, total=total)

    def get_encounter(self, encounter_id: str) -> EncounterDetailResponse:
        row = (
            self.db.query(
                EncounterModel.encounter_id,
                EncounterModel.patient_id,
                _patient_name_col,
                EncounterModel.provider_id,
                _provider_name_col,
                EncounterModel.organization_id,
                OrganizationModel.name.label("organization_name"),
                EncounterModel.start_date,
                EncounterModel.end_date,
                EncounterModel.duration,
                EncounterModel.encounter_class,
                EncounterModel.description,
                EncounterModel.reason_description,
            )
            .join(PatientModel, EncounterModel.patient_id == PatientModel.patient_id)
            .outerjoin(ProviderModel, EncounterModel.provider_id == ProviderModel.provider_id)
            .outerjoin(OrganizationModel, EncounterModel.organization_id == OrganizationModel.organization_id)
            .filter(EncounterModel.encounter_id == encounter_id)
            .first()
        )
        if not row:
            raise ValueError(f"Encounter {encounter_id} not found")
        return EncounterDetailResponse(**row._asdict())

    def get_encounter_observations(self, encounter_id: str) -> list[EncounterObservationItem]:
        rows = (
            self.db.query(ObservationModel)
            .filter(ObservationModel.encounter_id == encounter_id)
            .order_by(ObservationModel.date.asc())
            .all()
        )
        return [
            EncounterObservationItem(
                id=r.id,
                date=r.date,
                observation_code=str(r.observation_code),
                description=r.description,
                value=r.value,
                value_numeric=r.value_numeric,
                units=r.units,
            )
            for r in rows
        ]

    def get_encounter_conditions(self, encounter_id: str) -> list[EncounterConditionItem]:
        rows = (
            self.db.query(ConditionModel)
            .filter(ConditionModel.encounter_id == encounter_id)
            .order_by(ConditionModel.start_date.asc())
            .all()
        )
        return [
            EncounterConditionItem(
                id=r.id,
                condition_code=str(r.condition_code),
                description=r.description,
                start_date=r.start_date,
                end_date=r.end_date,
            )
            for r in rows
        ]

    def get_encounter_medications(self, encounter_id: str) -> list[EncounterMedicationItem]:
        rows = (
            self.db.query(MedicationModel)
            .filter(MedicationModel.encounter_id == encounter_id)
            .order_by(MedicationModel.start_date.asc())
            .all()
        )
        return [
            EncounterMedicationItem(
                id=r.id,
                medication_code=str(r.medication_code),
                description=r.description,
                start_date=r.start_date,
                end_date=r.end_date,
                duration_days=r.duration_days if r.duration_days else None,
                reason_description=r.reason_description,
            )
            for r in rows
        ]

    def get_encounter_procedures(self, encounter_id: str) -> list[EncounterProcedureItem]:
        rows = (
            self.db.query(ProcedureModel)
            .filter(ProcedureModel.encounter_id == encounter_id)
            .order_by(ProcedureModel.start_date.asc())
            .all()
        )
        return [
            EncounterProcedureItem(
                id=r.id,
                procedure_code=str(r.procedure_code),
                description=r.description,
                start_date=r.start_date,
                end_date=r.end_date,
                reason_description=r.reason_description,
            )
            for r in rows
        ]

    def get_encounter_immunizations(self, encounter_id: str) -> list[EncounterImmunizationItem]:
        rows = (
            self.db.query(ImmunizationModel)
            .filter(ImmunizationModel.encounter_id == encounter_id)
            .order_by(ImmunizationModel.date.asc())
            .all()
        )
        return [
            EncounterImmunizationItem(
                id=r.id,
                immunization_code=str(r.immunization_code),
                description=r.description,
                date=r.date,
            )
            for r in rows
        ]

    def get_encounter_careplans(self, encounter_id: str) -> list[EncounterCarePlanItem]:
        rows = (
            self.db.query(CarePlanModel)
            .filter(CarePlanModel.encounter_id == encounter_id)
            .order_by(CarePlanModel.start_date.asc())
            .all()
        )
        return [
            EncounterCarePlanItem(
                id=r.id,
                careplan_code=str(r.careplan_code),
                description=r.description,
                start_date=r.start_date,
                end_date=r.end_date,
                reason_description=r.reason_description,
            )
            for r in rows
        ]

    def get_encounter_allergies(self, encounter_id: str) -> list[EncounterAllergyItem]:
        rows = (
            self.db.query(AllergyModel)
            .filter(AllergyModel.encounter_id == encounter_id)
            .order_by(AllergyModel.start_date.asc())
            .all()
        )
        return [
            EncounterAllergyItem(
                id=r.id,
                allergy_code=str(r.allergy_code),
                description=r.description,
                start_date=r.start_date,
                end_date=r.end_date,
            )
            for r in rows
        ]

    def get_encounter_resources(self) -> EncounterResourcesResponse:
        rows = (
            self.db.query(EncounterModel.encounter_class)
            .distinct()
            .order_by(EncounterModel.encounter_class)
            .all()
        )
        encounter_classes = [FilterOption(value=r.encounter_class, label=r.encounter_class) for r in rows]
        return EncounterResourcesResponse(encounter_classes=encounter_classes)
