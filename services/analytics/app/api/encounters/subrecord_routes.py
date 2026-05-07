"""POST/PATCH/DELETE for all encounter sub-records.

One file holds all 7 kinds (observation, condition, medication, procedure,
immunization, careplan, allergy) because the per-kind handlers are nearly
identical and only differ in the request schema and response item shape.
"""
from typing import Optional, Type
from fastapi import Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.db_connector import get_clinical_db as get_db
from domain import (
    EncounterObservationItem, EncounterConditionItem, EncounterMedicationItem,
    EncounterProcedureItem, EncounterImmunizationItem, EncounterAllergyItem,
    EncounterCarePlanItem,
)
from domain.schemas.encounter_schemas.encounter_schema import (
    ObservationCreateRequest, ObservationUpdateRequest,
    ConditionCreateRequest, ConditionUpdateRequest,
    MedicationCreateRequest, MedicationUpdateRequest,
    ProcedureCreateRequest, ProcedureUpdateRequest,
    ImmunizationCreateRequest, ImmunizationUpdateRequest,
    CarePlanCreateRequest, CarePlanUpdateRequest,
    AllergyCreateRequest, AllergyUpdateRequest,
)
from repository import EncounterRepository
from service import EncounterService
from api._scope import Scope, scope_dep
from messaging import publish_event_nowait, EventAction
from .encounter_router import encounter_router


def _to_item(kind: str, instance):
    common = dict(id=instance.id, description=instance.description)
    if kind == "observation":
        return EncounterObservationItem(
            **common,
            date=instance.date,
            observation_code=str(instance.observation_code),
            value=instance.value,
            value_numeric=instance.value_numeric,
            units=instance.units,
        )
    if kind == "condition":
        return EncounterConditionItem(
            **common,
            condition_code=str(instance.condition_code),
            start_date=instance.start_date,
            end_date=instance.end_date,
        )
    if kind == "medication":
        return EncounterMedicationItem(
            **common,
            medication_code=str(instance.medication_code),
            start_date=instance.start_date,
            end_date=instance.end_date,
            duration_days=instance.duration_days or None,
            reason_description=instance.reason_description,
        )
    if kind == "procedure":
        return EncounterProcedureItem(
            **common,
            procedure_code=str(instance.procedure_code),
            start_date=instance.start_date,
            end_date=instance.end_date,
            reason_description=instance.reason_description,
        )
    if kind == "immunization":
        return EncounterImmunizationItem(
            **common,
            immunization_code=str(instance.immunization_code),
            date=instance.date,
        )
    if kind == "careplan":
        return EncounterCarePlanItem(
            **common,
            careplan_code=str(instance.careplan_code),
            start_date=instance.start_date,
            end_date=instance.end_date,
            reason_description=instance.reason_description,
        )
    if kind == "allergy":
        return EncounterAllergyItem(
            **common,
            allergy_code=str(instance.allergy_code),
            start_date=instance.start_date,
            end_date=instance.end_date,
        )
    raise ValueError(f"Unknown subrecord kind {kind}")


def _provider_scope(scope: Scope) -> Optional[str]:
    if scope.is_patient:
        raise HTTPException(status_code=403, detail="Patients cannot modify clinical records")
    return scope.provider_id if scope.is_doctor else None


_PATH_SEG = {
    "observation": "observations",
    "condition": "conditions",
    "medication": "medications",
    "procedure": "procedures",
    "immunization": "immunizations",
    "careplan": "careplans",
    "allergy": "allergies",
}


def _make_create(kind: str, request_model: Type[BaseModel], response_model):
    seg = _PATH_SEG[kind]

    @encounter_router.post(f"/{{encounter_id}}/{seg}", response_model=response_model, status_code=201)
    async def _create(
        encounter_id: str,
        payload: request_model,
        db: Session = Depends(get_db),
        scope: Scope = Depends(scope_dep),
    ):
        provider_scope = _provider_scope(scope)
        try:
            instance = EncounterService(EncounterRepository(db)).create_subrecord(kind, encounter_id, payload, provider_scope)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        publish_event_nowait(
            kind, EventAction.CREATED,
            patient_id=getattr(instance, "patient_id", None),
            encounter_id=encounter_id,
            record_id=getattr(instance, "id", None),
        )
        return _to_item(kind, instance)
    _create.__name__ = f"create_{kind}"
    return _create


def _make_update(kind: str, request_model: Type[BaseModel], response_model):
    seg = _PATH_SEG[kind]

    @encounter_router.patch(f"/{{encounter_id}}/{seg}/{{record_id}}", response_model=response_model)
    async def _update(
        encounter_id: str,
        record_id: int,
        payload: request_model,
        db: Session = Depends(get_db),
        scope: Scope = Depends(scope_dep),
    ):
        provider_scope = _provider_scope(scope)
        try:
            instance = EncounterService(EncounterRepository(db)).update_subrecord(kind, encounter_id, record_id, payload, provider_scope)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        publish_event_nowait(
            kind, EventAction.UPDATED,
            patient_id=getattr(instance, "patient_id", None),
            encounter_id=encounter_id,
            record_id=record_id,
        )
        return _to_item(kind, instance)
    _update.__name__ = f"update_{kind}"
    return _update


def _make_delete(kind: str):
    seg = _PATH_SEG[kind]

    @encounter_router.delete(f"/{{encounter_id}}/{seg}/{{record_id}}", status_code=204)
    async def _delete(
        encounter_id: str,
        record_id: int,
        db: Session = Depends(get_db),
        scope: Scope = Depends(scope_dep),
    ):
        provider_scope = _provider_scope(scope)
        try:
            EncounterService(EncounterRepository(db)).delete_subrecord(kind, encounter_id, record_id, provider_scope)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        publish_event_nowait(
            kind, EventAction.DELETED,
            encounter_id=encounter_id,
            record_id=record_id,
        )
        return Response(status_code=204)
    _delete.__name__ = f"delete_{kind}"
    return _delete


_REGISTRY = [
    ("observation", ObservationCreateRequest, ObservationUpdateRequest, EncounterObservationItem),
    ("condition", ConditionCreateRequest, ConditionUpdateRequest, EncounterConditionItem),
    ("medication", MedicationCreateRequest, MedicationUpdateRequest, EncounterMedicationItem),
    ("procedure", ProcedureCreateRequest, ProcedureUpdateRequest, EncounterProcedureItem),
    ("immunization", ImmunizationCreateRequest, ImmunizationUpdateRequest, EncounterImmunizationItem),
    ("careplan", CarePlanCreateRequest, CarePlanUpdateRequest, EncounterCarePlanItem),
    ("allergy", AllergyCreateRequest, AllergyUpdateRequest, EncounterAllergyItem),
]

for _kind, _create_req, _update_req, _resp in _REGISTRY:
    _make_create(_kind, _create_req, _resp)
    _make_update(_kind, _update_req, _resp)
    _make_delete(_kind)
