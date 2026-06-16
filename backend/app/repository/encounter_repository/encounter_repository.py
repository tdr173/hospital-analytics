import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

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
from domain.schemas.encounter_schemas.encounter_schema import (
    EncounterCreateRequest, EncounterUpdateRequest,
    ObservationCreateRequest, ObservationUpdateRequest,
    ConditionCreateRequest, ConditionUpdateRequest,
    MedicationCreateRequest, MedicationUpdateRequest,
    ProcedureCreateRequest, ProcedureUpdateRequest,
    ImmunizationCreateRequest, ImmunizationUpdateRequest,
    CarePlanCreateRequest, CarePlanUpdateRequest,
    AllergyCreateRequest, AllergyUpdateRequest,
)
from repository._helpers import patient_name_col, provider_name_col, clamp_page_size, link_patient_provider


SUBRECORD_MODELS = {
    "observation": ObservationModel,
    "condition": ConditionModel,
    "medication": MedicationModel,
    "procedure": ProcedureModel,
    "immunization": ImmunizationModel,
    "careplan": CarePlanModel,
    "allergy": AllergyModel,
}

SORT_COL_MAP = {
    "start_date": EncounterModel.start_date,
    "duration": EncounterModel.duration,
    "encounter_class": EncounterModel.encounter_class,
}


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
        role: Optional[str] = None,
        patient_id_scope: Optional[str] = None,
        provider_id_scope: Optional[str] = None,
    ) -> EncounterListResponse:
        sort_col = SORT_COL_MAP.get(sort_by, EncounterModel.start_date)
        sort_expr = (
            sort_col.asc().nulls_last()
            if sort_type.lower() == "asc"
            else sort_col.desc().nulls_last()
        )

        enc_filters = []
        patient_filters = []

        role_u = (role or "MANAGER").upper()
        if role_u == "PATIENT" and patient_id_scope:
            enc_filters.append(EncounterModel.patient_id == patient_id_scope)
        elif role_u == "DOCTOR" and provider_id_scope:
            enc_filters.append(EncounterModel.provider_id == provider_id_scope)

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

        count_q = self.db.query(func.count(EncounterModel.encounter_id)).filter(*enc_filters)
        if patient_filters:
            count_q = (
                count_q
                .join(PatientModel, EncounterModel.patient_id == PatientModel.patient_id)
                .filter(*patient_filters)
            )
        total = count_q.scalar() or 0

        rows = clamp_page_size(rows)
        offset = (page - 1) * rows
        q = (
            self.db.query(
                EncounterModel.encounter_id,
                EncounterModel.patient_id,
                patient_name_col(),
                provider_name_col(),
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
                patient_name_col(),
                EncounterModel.provider_id,
                provider_name_col(),
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

    def _paginate(self, query, page: int, page_size: int):
        rows = query.offset((page - 1) * page_size).limit(page_size + 1).all()
        has_more = len(rows) > page_size
        return rows[:page_size], has_more

    def get_encounter_observations(self, encounter_id: str, page: int = 1, page_size: int = 20):
        q = (
            self.db.query(ObservationModel)
            .filter(ObservationModel.encounter_id == encounter_id)
            .order_by(ObservationModel.date.asc())
        )
        rows, has_more = self._paginate(q, page, page_size)
        items = [
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
        return items, has_more

    def get_encounter_conditions(self, encounter_id: str, page: int = 1, page_size: int = 20):
        q = (
            self.db.query(ConditionModel)
            .filter(ConditionModel.encounter_id == encounter_id)
            .order_by(ConditionModel.start_date.asc())
        )
        rows, has_more = self._paginate(q, page, page_size)
        items = [
            EncounterConditionItem(
                id=r.id,
                condition_code=str(r.condition_code),
                description=r.description,
                start_date=r.start_date,
                end_date=r.end_date,
            )
            for r in rows
        ]
        return items, has_more

    def get_encounter_medications(self, encounter_id: str, page: int = 1, page_size: int = 20):
        q = (
            self.db.query(MedicationModel)
            .filter(MedicationModel.encounter_id == encounter_id)
            .order_by(MedicationModel.start_date.asc())
        )
        rows, has_more = self._paginate(q, page, page_size)
        items = [
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
        return items, has_more

    def get_encounter_procedures(self, encounter_id: str, page: int = 1, page_size: int = 20):
        q = (
            self.db.query(ProcedureModel)
            .filter(ProcedureModel.encounter_id == encounter_id)
            .order_by(ProcedureModel.start_date.asc())
        )
        rows, has_more = self._paginate(q, page, page_size)
        items = [
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
        return items, has_more

    def get_encounter_immunizations(self, encounter_id: str, page: int = 1, page_size: int = 20):
        q = (
            self.db.query(ImmunizationModel)
            .filter(ImmunizationModel.encounter_id == encounter_id)
            .order_by(ImmunizationModel.date.asc())
        )
        rows, has_more = self._paginate(q, page, page_size)
        items = [
            EncounterImmunizationItem(
                id=r.id,
                immunization_code=str(r.immunization_code),
                description=r.description,
                date=r.date,
            )
            for r in rows
        ]
        return items, has_more

    def get_encounter_careplans(self, encounter_id: str, page: int = 1, page_size: int = 20):
        q = (
            self.db.query(CarePlanModel)
            .filter(CarePlanModel.encounter_id == encounter_id)
            .order_by(CarePlanModel.start_date.asc())
        )
        rows, has_more = self._paginate(q, page, page_size)
        items = [
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
        return items, has_more

    def get_encounter_allergies(self, encounter_id: str, page: int = 1, page_size: int = 20):
        q = (
            self.db.query(AllergyModel)
            .filter(AllergyModel.encounter_id == encounter_id)
            .order_by(AllergyModel.start_date.asc())
        )
        rows, has_more = self._paginate(q, page, page_size)
        items = [
            EncounterAllergyItem(
                id=r.id,
                allergy_code=str(r.allergy_code),
                description=r.description,
                start_date=r.start_date,
                end_date=r.end_date,
            )
            for r in rows
        ]
        return items, has_more

    def _resolve_default_org_id(self) -> str:
        org = self.db.query(OrganizationModel).first()
        if not org:
            raise ValueError("No organization configured")
        return org.organization_id

    def _ensure_encounter(self, encounter_id: str, provider_id_scope: Optional[str]) -> EncounterModel:
        enc = self.db.get(EncounterModel, encounter_id)
        if not enc:
            raise ValueError(f"Encounter {encounter_id} not found")
        if provider_id_scope and enc.provider_id != provider_id_scope:
            raise PermissionError("Encounter does not belong to this provider")
        return enc

    def create_encounter(self, payload: EncounterCreateRequest, provider_id_scope: Optional[str]) -> EncounterDetailResponse:
        if not self.db.get(PatientModel, payload.patient_id):
            raise ValueError(f"Patient {payload.patient_id} not found")
        provider_id = provider_id_scope or payload.provider_id
        if not provider_id:
            raise ValueError("providerId required when role is not DOCTOR")
        if not self.db.get(ProviderModel, provider_id):
            raise ValueError(f"Provider {provider_id} not found")
        org_id = self._resolve_default_org_id()
        duration = max((payload.end_date - payload.start_date).total_seconds() / 60.0, 0.0)
        enc = EncounterModel(
            encounter_id=uuid.uuid4().hex,
            patient_id=payload.patient_id,
            provider_id=provider_id,
            organization_id=org_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            duration=duration,
            encounter_class=payload.encounter_class,
            description=payload.description,
            reason_description=payload.reason_description,
        )
        self.db.add(enc)
        self.db.commit()
        # keep the junction table in sync: the encounter's provider should see
        # this patient in their panel even if they never shared a visit before
        link_patient_provider(self.db, enc.patient_id, enc.provider_id)
        return self.get_encounter(enc.encounter_id)

    def update_encounter(self, encounter_id: str, payload: EncounterUpdateRequest, provider_id_scope: Optional[str]) -> EncounterDetailResponse:
        enc = self._ensure_encounter(encounter_id, provider_id_scope)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(enc, field, value)
        if payload.start_date is not None or payload.end_date is not None:
            enc.duration = max((enc.end_date - enc.start_date).total_seconds() / 60.0, 0.0)
        self.db.add(enc)
        self.db.commit()
        # if the provider was reassigned, make sure the new provider gets the
        # patient in their panel (idempotent if unchanged)
        link_patient_provider(self.db, enc.patient_id, enc.provider_id)
        return self.get_encounter(encounter_id)

    def delete_encounter(self, encounter_id: str, provider_id_scope: Optional[str]) -> None:
        enc = self._ensure_encounter(encounter_id, provider_id_scope)
        for model in SUBRECORD_MODELS.values():
            self.db.query(model).filter(model.encounter_id == encounter_id).delete(synchronize_session=False)
        self.db.delete(enc)
        self.db.commit()

    def create_subrecord(self, kind: str, encounter_id: str, payload, provider_id_scope: Optional[str]):
        enc = self._ensure_encounter(encounter_id, provider_id_scope)
        model = SUBRECORD_MODELS[kind]
        data = payload.model_dump(exclude_unset=False)
        instance = model(
            patient_id=enc.patient_id,
            encounter_id=encounter_id,
            **data,
        )
        if kind == "medication" and payload.start_date and payload.end_date:
            instance.duration_days = max((payload.end_date - payload.start_date).total_seconds() / 86400.0, 0.0)
        if kind == "careplan" and payload.start_date and payload.end_date:
            instance.duration_days = max((payload.end_date - payload.start_date).total_seconds() / 86400.0, 0.0)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update_subrecord(self, kind: str, encounter_id: str, record_id: int, payload, provider_id_scope: Optional[str]):
        self._ensure_encounter(encounter_id, provider_id_scope)
        model = SUBRECORD_MODELS[kind]
        instance = self.db.get(model, record_id)
        if not instance or instance.encounter_id != encounter_id:
            raise ValueError(f"{kind} {record_id} not found in encounter {encounter_id}")
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(instance, field, value)
        if kind in ("medication", "careplan") and instance.start_date and instance.end_date:
            instance.duration_days = max((instance.end_date - instance.start_date).total_seconds() / 86400.0, 0.0)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete_subrecord(self, kind: str, encounter_id: str, record_id: int, provider_id_scope: Optional[str]) -> None:
        self._ensure_encounter(encounter_id, provider_id_scope)
        model = SUBRECORD_MODELS[kind]
        instance = self.db.get(model, record_id)
        if not instance or instance.encounter_id != encounter_id:
            raise ValueError(f"{kind} {record_id} not found in encounter {encounter_id}")
        self.db.delete(instance)
        self.db.commit()

    def get_encounter_resources(self) -> EncounterResourcesResponse:
        rows = (
            self.db.query(EncounterModel.encounter_class)
            .distinct()
            .order_by(EncounterModel.encounter_class)
            .all()
        )
        encounter_classes = [FilterOption(value=r.encounter_class, label=r.encounter_class) for r in rows]
        return EncounterResourcesResponse(encounter_classes=encounter_classes)
