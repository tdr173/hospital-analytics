import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from domain import (
    ProviderModel, OrganizationModel, EncounterModel, PatientModel,
    ProviderListItem, ProviderListResponse, ProviderDetailResponse,
    ProviderEncounterItem, ProviderResourcesResponse, FilterOption,
)
from domain.schemas.provider_schemas.provider_schema import (
    ProviderCreateRequest, ProviderUpdateRequest,
)
from repository._helpers import patient_name_col, clamp_page_size

SORT_COL_MAP = {
    "last_name": ProviderModel.last_name,
    "first_name": ProviderModel.first_name,
    "speciality": ProviderModel.speciality,
    "city": ProviderModel.city,
    "encounters": func.count(EncounterModel.encounter_id),
}


class ProviderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_providers(
        self,
        search: Optional[str],
        gender: Optional[str],
        speciality: Optional[str],
        city: Optional[str],
        page: int,
        rows: int,
        sort_by: str,
        sort_type: str,
    ) -> ProviderListResponse:
        sort_col = SORT_COL_MAP.get(sort_by, ProviderModel.last_name)
        sort_expr = sort_col.asc().nulls_last() if sort_type.lower() == "asc" else sort_col.desc().nulls_last()

        filters = []

        if search:
            filters.append(or_(
                ProviderModel.first_name.ilike(f"%{search}%"),
                ProviderModel.last_name.ilike(f"%{search}%"),
                ProviderModel.city.ilike(f"%{search}%"),
            ))

        if gender:
            genders = [g.strip() for g in gender.split(",") if g.strip()]
            if genders:
                filters.append(ProviderModel.gender.in_(genders))

        if speciality:
            specialities = [s.strip() for s in speciality.split(",") if s.strip()]
            if specialities:
                filters.append(ProviderModel.speciality.in_(specialities))

        if city:
            filters.append(ProviderModel.city.ilike(f"%{city}%"))

        total = (
            self.db.query(func.count(ProviderModel.provider_id))
            .filter(*filters)
            .scalar() or 0
        )

        rows = clamp_page_size(rows)
        offset = (page - 1) * rows
        rows_data = (
            self.db.query(
                ProviderModel.provider_id,
                ProviderModel.first_name,
                ProviderModel.last_name,
                ProviderModel.gender,
                ProviderModel.speciality,
                ProviderModel.city,
                func.count(EncounterModel.encounter_id).label("encounters"),
                OrganizationModel.name.label("organization_name"),
            )
            .outerjoin(OrganizationModel, ProviderModel.organization_id == OrganizationModel.organization_id)
            .outerjoin(EncounterModel, EncounterModel.provider_id == ProviderModel.provider_id)
            .filter(*filters)
            .group_by(
                ProviderModel.provider_id,
                ProviderModel.first_name,
                ProviderModel.last_name,
                ProviderModel.gender,
                ProviderModel.speciality,
                ProviderModel.city,
                ProviderModel.organization_id,
                OrganizationModel.name,
            )
            .order_by(sort_expr)
            .limit(rows)
            .offset(offset)
            .all()
        )

        items = [ProviderListItem(**row._asdict()) for row in rows_data]
        return ProviderListResponse(items=items, total=total)

    def get_provider(self, provider_id: str) -> ProviderDetailResponse:
        row = (
            self.db.query(
                ProviderModel.provider_id,
                ProviderModel.first_name,
                ProviderModel.last_name,
                ProviderModel.gender,
                ProviderModel.speciality,
                ProviderModel.city,
                func.count(EncounterModel.encounter_id).label("encounters"),
                ProviderModel.organization_id,
                OrganizationModel.name.label("organization_name"),
            )
            .outerjoin(OrganizationModel, ProviderModel.organization_id == OrganizationModel.organization_id)
            .outerjoin(EncounterModel, EncounterModel.provider_id == ProviderModel.provider_id)
            .filter(ProviderModel.provider_id == provider_id)
            .group_by(
                ProviderModel.provider_id,
                ProviderModel.first_name,
                ProviderModel.last_name,
                ProviderModel.gender,
                ProviderModel.speciality,
                ProviderModel.city,
                ProviderModel.organization_id,
                OrganizationModel.name,
            )
            .first()
        )

        if not row:
            raise ValueError(f"Provider {provider_id} not found")

        return ProviderDetailResponse(**row._asdict())

    def get_provider_encounters(self, provider_id: str, page: int = 1, page_size: int = 20):
        offset = (page - 1) * page_size
        rows = (
            self.db.query(
                EncounterModel.encounter_id,
                EncounterModel.patient_id,
                patient_name_col(),
                EncounterModel.start_date,
                EncounterModel.end_date,
                EncounterModel.duration,
                EncounterModel.encounter_class,
                EncounterModel.description,
                EncounterModel.reason_description,
            )
            .outerjoin(PatientModel, EncounterModel.patient_id == PatientModel.patient_id)
            .filter(EncounterModel.provider_id == provider_id)
            .order_by(EncounterModel.start_date.desc())
            .offset(offset)
            .limit(page_size + 1)
            .all()
        )
        has_more = len(rows) > page_size
        items = [ProviderEncounterItem(**row._asdict()) for row in rows[:page_size]]
        return items, has_more

    def _resolve_default_org(self) -> OrganizationModel:
        org = self.db.query(OrganizationModel).first()
        if not org:
            raise ValueError("No organization configured")
        return org

    def create_provider(self, payload: ProviderCreateRequest) -> ProviderDetailResponse:
        org = self._resolve_default_org()
        provider = ProviderModel(
            provider_id=uuid.uuid4().hex,
            organization_id=org.organization_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            gender=payload.gender,
            speciality=payload.speciality,
            city=payload.city or org.city,
        )
        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)
        return self.get_provider(provider.provider_id)

    def update_provider(self, provider_id: str, payload: ProviderUpdateRequest) -> ProviderDetailResponse:
        provider = self.db.get(ProviderModel, provider_id)
        if not provider:
            raise ValueError(f"Provider {provider_id} not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(provider, field, value)
        self.db.add(provider)
        self.db.commit()
        return self.get_provider(provider_id)

    def delete_provider(self, provider_id: str) -> None:
        provider = self.db.get(ProviderModel, provider_id)
        if not provider:
            raise ValueError(f"Provider {provider_id} not found")
        encounter_count = (
            self.db.query(func.count(EncounterModel.encounter_id))
            .filter(EncounterModel.provider_id == provider_id)
            .scalar() or 0
        )
        if encounter_count > 0:
            raise ValueError(f"Provider has {encounter_count} encounters; cannot delete")
        self.db.delete(provider)
        self.db.commit()

    def get_provider_resources(self) -> ProviderResourcesResponse:
        speciality_rows = (
            self.db.query(ProviderModel.speciality)
            .filter(ProviderModel.speciality.isnot(None))
            .distinct()
            .order_by(ProviderModel.speciality)
            .all()
        )
        specialities = [FilterOption(value=r.speciality, label=r.speciality) for r in speciality_rows]

        return ProviderResourcesResponse(
            genders=[
                FilterOption(value="M", label="Male"),
                FilterOption(value="F", label="Female"),
            ],
            specialities=specialities,
        )
