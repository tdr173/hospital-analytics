from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import OrganizationDetailResponse
from repository import OrganizationRepository
from service import OrganizationService
from .organization_router import organization_router


@organization_router.get("/{organization_id}", response_model=OrganizationDetailResponse)
async def get_organization(organization_id: str, db: Session = Depends(get_db)):
    try:
        return OrganizationService(OrganizationRepository(db)).get_organization(organization_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
