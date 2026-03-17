from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.api.statistics.statistics_router import statistics_router
from app.service.statistics_service.organization_service import OrganizationService
from app.domain.schemas.statistics_schema.organization_schema import OrganizationStatisticsResponse


@statistics_router.get("/organizations", response_model=OrganizationStatisticsResponse)
async def get_organization_statistics(db: Session = Depends(get_db)):
    service = OrganizationService(db)
    return service.get_organization_summary()
