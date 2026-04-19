from typing import Optional
from fastapi import Depends, Query
from sqlalchemy.orm import Session
import re

from db.db_connector import get_db
from domain import OrganizationListResponse
from repository import OrganizationRepository
from service import OrganizationService
from .organization_router import organization_router


def _to_snake(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name).lower()


@organization_router.get("", response_model=OrganizationListResponse)
async def get_organizations(
    search: Optional[str] = None,
    city: Optional[str] = None,  # comma-separated list
    page: int = 1,
    rows: int = 25,
    sort_by: str = Query("name", alias="sortBy"),
    sort_type: str = Query("asc", alias="sortType"),
    db: Session = Depends(get_db),
):
    cities = [c.strip() for c in city.split(",")] if city else None
    return OrganizationService(OrganizationRepository(db)).get_organizations(
        search=search,
        city=cities,
        page=page,
        rows=rows,
        sort_by=_to_snake(sort_by),
        sort_type=sort_type,
    )
