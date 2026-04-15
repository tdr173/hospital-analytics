from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import OrganizationEncounterResponse
from repository import OrganizationRepository
from service import OrganizationService
from .organization_router import organization_router


@organization_router.get("/{organization_id}/encounters", response_model=OrganizationEncounterResponse)
async def get_organization_encounters(
    organization_id: str,
    page: int = 1,
    rows: int = 25,
    db: Session = Depends(get_db),
):
    return OrganizationService(OrganizationRepository(db)).get_organization_encounters(
        organization_id, page, rows
    )
