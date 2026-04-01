from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from .statistics_router import statistics_router
from service.statistics_service.organization_service import OrganizationService
from domain.schemas.statistics_schemas.organization_schema import OrganizationStatisticsResponse


@statistics_router.get("/organizations", response_model=OrganizationStatisticsResponse)
async def get_organization_statistics(db: Session = Depends(get_db)):
    service = OrganizationService(db)
    return service.get_organization_summary()
