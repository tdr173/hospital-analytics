from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from service import ClusterService
from domain import GetClusterStatistics
from repository import ClusterRepository
from .cluster_router import cluster_router


@cluster_router.get("/statistics", response_model=GetClusterStatistics)
def get_cluster_statistics(db: Session = Depends(get_db)):
    cluster_repo = ClusterRepository(db)
    cluster_service = ClusterService(cluster_repo)

    return cluster_service.get_cluster_statistics()
