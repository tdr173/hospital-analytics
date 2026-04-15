from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import OrganizationResourcesResponse
from repository import OrganizationRepository
from service import OrganizationService
from .organization_router import organization_router


@organization_router.get("/resources", response_model=OrganizationResourcesResponse)
async def get_organizations_resources(db: Session = Depends(get_db)):
    return OrganizationService(OrganizationRepository(db)).get_organization_resources()
