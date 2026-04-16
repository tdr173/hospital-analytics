from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from domain import (
    OrganizationModel, ProviderModel, EncounterModel, PatientModel,
    OrganizationListItem, OrganizationListResponse,
    OrganizationDetailResponse, OrganizationProviderItem,
    OrganizationEncounterItem,
    OrganizationResourcesResponse, FilterOption,
)
from repository._helpers import patient_name_col, provider_name_col, clamp_page_size

SORT_COL_MAP = {
    "name": OrganizationModel.name,
    "city": OrganizationModel.city,
    "utilization": OrganizationModel.utilization,
}


class OrganizationRepository:
    def __init__(self, db: Session):
        self.db = db

    def _provider_count_subq(self):
        return (
            self.db.query(
                ProviderModel.organization_id,
                func.count(ProviderModel.provider_id).label("provider_count"),
            )
            .group_by(ProviderModel.organization_id)
            .subquery()
        )

    def get_organizations(
        self,
        search: Optional[str],
        city: Optional[str],
        page: int,
        rows: int,
        sort_by: str,
        sort_type: str,
    ) -> OrganizationListResponse:
        filters = []

        if search:
            filters.append(or_(
                OrganizationModel.name.ilike(f"%{search}%"),
                OrganizationModel.city.ilike(f"%{search}%"),
            ))

        if city:
            filters.append(OrganizationModel.city == city)

        total = (
            self.db.query(func.count(OrganizationModel.organization_id))
            .filter(*filters)
            .scalar() or 0
        )

        pc_subq = self._provider_count_subq()
        provider_count_col = func.coalesce(pc_subq.c.provider_count, 0)

        if sort_by == "provider_count":
            sort_expr = (
                provider_count_col.asc()
                if sort_type.lower() == "asc"
                else provider_count_col.desc()
            )
        else:
            sort_col = SORT_COL_MAP.get(sort_by, OrganizationModel.name)
            sort_expr = (
                sort_col.asc().nulls_last()
                if sort_type.lower() == "asc"
                else sort_col.desc().nulls_last()
            )

        rows = clamp_page_size(rows)
        offset = (page - 1) * rows
        rows_data = (
            self.db.query(
                OrganizationModel.organization_id,
                OrganizationModel.name,
                OrganizationModel.city,
                OrganizationModel.phone,
                OrganizationModel.utilization,
                provider_count_col.label("provider_count"),
            )
            .outerjoin(pc_subq, OrganizationModel.organization_id == pc_subq.c.organization_id)
            .filter(*filters)
            .order_by(sort_expr)
            .limit(rows)
            .offset(offset)
            .all()
        )

        items = [OrganizationListItem(**row._asdict()) for row in rows_data]
        return OrganizationListResponse(items=items, total=total)

    def get_organization(self, organization_id: str) -> OrganizationDetailResponse:
        row = (
            self.db.query(OrganizationModel)
            .filter(OrganizationModel.organization_id == organization_id)
            .first()
        )
        if not row:
            raise ValueError(f"Organization {organization_id} not found")
        return OrganizationDetailResponse(
            organization_id=row.organization_id,
            name=row.name,
            city=row.city,
            latitude=row.latitude,
            longitude=row.longitude,
        )

    def get_organization_providers(self, organization_id: str) -> list[OrganizationProviderItem]:
        rows = (
            self.db.query(ProviderModel)
            .filter(ProviderModel.organization_id == organization_id)
            .order_by(ProviderModel.last_name.asc())
            .all()
        )
        return [
            OrganizationProviderItem(
                provider_id=r.provider_id,
                first_name=r.first_name,
                last_name=r.last_name,
                gender=r.gender,
                speciality=r.speciality,
                utilization=r.utilization,
            )
            for r in rows
        ]

    def get_organization_encounters(self, organization_id: str) -> list[OrganizationEncounterItem]:
        rows_data = (
            self.db.query(
                EncounterModel.encounter_id,
                EncounterModel.patient_id,
                patient_name_col(),
                EncounterModel.provider_id,
                provider_name_col(),
                EncounterModel.start_date,
                EncounterModel.end_date,
                EncounterModel.duration,
                EncounterModel.encounter_class,
                EncounterModel.description,
                EncounterModel.reason_description,
            )
            .outerjoin(PatientModel, EncounterModel.patient_id == PatientModel.patient_id)
            .outerjoin(ProviderModel, EncounterModel.provider_id == ProviderModel.provider_id)
            .filter(EncounterModel.organization_id == organization_id)
            .order_by(EncounterModel.start_date.desc())
            .all()
        )

        return [OrganizationEncounterItem(**row._asdict()) for row in rows_data]

    def get_organization_resources(self) -> OrganizationResourcesResponse:
        city_rows = (
            self.db.query(OrganizationModel.city)
            .filter(OrganizationModel.city.isnot(None))
            .distinct()
            .order_by(OrganizationModel.city)
            .all()
        )
        cities = [FilterOption(value=r.city, label=r.city) for r in city_rows]
        return OrganizationResourcesResponse(cities=cities)
