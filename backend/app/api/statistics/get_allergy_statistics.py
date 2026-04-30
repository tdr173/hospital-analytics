from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from api._scope import Scope, scope_dep
from .statistics_router import statistics_router
from service.statistics_service.allergy_service import AllergyService
from domain.schemas.statistics_schemas.allergy_schema import AllergyStatisticsResponse


@statistics_router.get("/allergies", response_model=AllergyStatisticsResponse)
async def get_allergy_statistics(
    range: str = Query("all", pattern="^(all|week|month)$"),
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    provider_id = scope.provider_id if scope.is_doctor else None
    service = AllergyService(db, range, provider_id)
    return service.get_allergy_summary()
