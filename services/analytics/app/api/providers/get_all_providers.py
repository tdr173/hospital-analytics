from typing import Optional
from fastapi import Depends, Query
from sqlalchemy.orm import Session
import re

from db.db_connector import get_db
from domain import ProviderListResponse
from repository import ProviderRepository
from service import ProviderService
from .provider_router import provider_router


def _to_snake(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name).lower()


@provider_router.get("", response_model=ProviderListResponse)
async def get_providers(
    search: Optional[str] = None,
    gender: Optional[str] = None,
    speciality: Optional[str] = None,
    city: Optional[str] = None,
    page: int = 1,
    rows: int = 25,
    sort_by: str = Query("lastName", alias="sortBy"),
    sort_type: str = Query("asc", alias="sortType"),
    db: Session = Depends(get_db),
):
    return ProviderService(ProviderRepository(db)).get_providers(
        search=search,
        gender=gender,
        speciality=speciality,
        city=city,
        page=page,
        rows=rows,
        sort_by=_to_snake(sort_by),
        sort_type=sort_type,
    )
