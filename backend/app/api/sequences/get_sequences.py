from typing import Optional
from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from service import SequenceService
from domain import SequenceListResponse
from repository import SequenceRepository
from .sequence_router import sequence_router


@sequence_router.get("", response_model=SequenceListResponse)
async def get_sequences(
    search: Optional[str] = None,
    min_length: int = Query(default=1, ge=1, alias="minLength"),
    sort_by: str = Query(default="support", alias="sortBy"),
    sort_type: str = Query(default="desc", alias="sortType"),
    page: int = Query(default=1, ge=1),
    rows: int = Query(default=8, ge=1, le=100),
    cluster_labels: Optional[str] = Query(default=None, alias="clusterLabels"),
    db: Session = Depends(get_db),
):
    labels: Optional[list[int]] = None
    if cluster_labels:
        labels = [int(x) for x in cluster_labels.split(",") if x.strip()]

    repo = SequenceRepository(db)
    service = SequenceService(repo)
    return service.get_sequences(
        search=search,
        min_length=min_length,
        sort_by=sort_by,
        sort_type=sort_type,
        page=page,
        rows=rows,
        cluster_labels=labels,
    )
