from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_connector import get_db
from service import ClusterService
from domain import ClusterDetailResponse
from repository import ClusterRepository
from .cluster_router import cluster_router


@cluster_router.get("/detail/{cluster_id}", response_model=ClusterDetailResponse)
def get_cluster_detail(cluster_id: int, db: Session = Depends(get_db)):
    cluster_repo = ClusterRepository(db)
    cluster_service = ClusterService(cluster_repo)

    try:
        return cluster_service.get_cluster_detail(cluster_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
