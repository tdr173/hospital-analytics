from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from domain import (
    PipelineRunModel,
    PatientModel,
    MedicationModel,
    ProcedureModel,
    CarePlanModel,
    ConditionModel,
    ClusterModel,
    ClusterMetaModel,
    PrefixSpanPatternModel,
    DataCounts,
)


class PipelineRepository:
    def __init__(self, db: Session):
        self.db = db

    def ensure_singleton(self) -> PipelineRunModel:
        state = self.db.get(PipelineRunModel, 1)
        if state is None:
            state = PipelineRunModel(id=1, status="IDLE")
            self.db.add(state)
            self.db.commit()
            self.db.refresh(state)
        return state

    def get_state(self) -> PipelineRunModel:
        return self.ensure_singleton()

    def try_mark_running(self, triggered_by: str) -> bool:
        """Atomically flip the singleton to RUNNING only if it isn't already.
        Returns False if a run is already in progress (guards double-click /
        scheduler overlap)."""
        self.ensure_singleton()
        updated = (
            self.db.query(PipelineRunModel)
            .filter(PipelineRunModel.id == 1, PipelineRunModel.status != "RUNNING")
            .update(
                {
                    "status": "RUNNING",
                    "current_stage": None,
                    "etl_skipped": False,
                    "triggered_by": triggered_by,
                    "started_at": datetime.now(),
                    "finished_at": None,
                    "error": None,
                    "stop_requested": False,
                },
                synchronize_session=False,
            )
        )
        self.db.commit()
        return updated > 0

    def fail_stale_running(self, error: str) -> bool:
        """Called once at process startup: a RUNNING row left over from a
        previous process means that process died (crash/restart) taking its
        background thread with it, so nothing will ever mark it done. Fail it
        so the UI doesn't show a run that can never finish or be stopped."""
        updated = (
            self.db.query(PipelineRunModel)
            .filter(PipelineRunModel.id == 1, PipelineRunModel.status == "RUNNING")
            .update(
                {
                    "status": "FAILED",
                    "finished_at": datetime.now(),
                    "error": error,
                    "stop_requested": False,
                },
                synchronize_session=False,
            )
        )
        self.db.commit()
        return updated > 0

    def request_stop(self) -> bool:
        """Ask a RUNNING pipeline to stop at its next checkpoint. Returns False
        if no run is in progress."""
        updated = (
            self.db.query(PipelineRunModel)
            .filter(PipelineRunModel.id == 1, PipelineRunModel.status == "RUNNING")
            .update({"stop_requested": True}, synchronize_session=False)
        )
        self.db.commit()
        return updated > 0

    def is_stop_requested(self) -> bool:
        return bool(self.ensure_singleton().stop_requested)

    def set_stage(self, stage: str, etl_skipped: Optional[bool] = None) -> None:
        values = {"current_stage": stage}
        if etl_skipped is not None:
            values["etl_skipped"] = etl_skipped
        self.db.query(PipelineRunModel).filter(PipelineRunModel.id == 1).update(
            values, synchronize_session=False
        )
        self.db.commit()

    def mark_success(self) -> None:
        now = datetime.now()
        self.db.query(PipelineRunModel).filter(PipelineRunModel.id == 1).update(
            {
                "status": "SUCCESS",
                "current_stage": "DONE",
                "finished_at": now,
                "last_run_at": now,
                "error": None,
                "stop_requested": False,
            },
            synchronize_session=False,
        )
        self.db.commit()

    def mark_failed(self, error: str) -> None:
        now = datetime.now()
        self.db.query(PipelineRunModel).filter(PipelineRunModel.id == 1).update(
            {
                "status": "FAILED",
                "finished_at": now,
                "last_run_at": now,
                "error": error[:2000],
                "stop_requested": False,
            },
            synchronize_session=False,
        )
        self.db.commit()

    def mark_stopped(self) -> None:
        now = datetime.now()
        self.db.query(PipelineRunModel).filter(PipelineRunModel.id == 1).update(
            {
                "status": "STOPPED",
                "finished_at": now,
                "last_run_at": now,
                "error": None,
                "stop_requested": False,
            },
            synchronize_session=False,
        )
        self.db.commit()

    def is_patient_table_empty(self) -> bool:
        count = self.db.query(func.count()).select_from(PatientModel).scalar()
        return (count or 0) == 0

    def get_current_n_clusters(self) -> Optional[int]:
        meta = self.db.query(ClusterMetaModel).first()
        return meta.n_clusters if meta is not None else None

    def get_data_counts(self) -> DataCounts:
        return DataCounts(
            patients=self.db.query(func.count()).select_from(PatientModel).scalar() or 0,
            medications=self.db.query(func.count()).select_from(MedicationModel).scalar() or 0,
            procedures=self.db.query(func.count()).select_from(ProcedureModel).scalar() or 0,
            careplans=self.db.query(func.count()).select_from(CarePlanModel).scalar() or 0,
            conditions=self.db.query(func.count()).select_from(ConditionModel).scalar() or 0,
        )

    def get_cluster_interpretation_counts(self) -> tuple[int, int]:
        total = self.db.query(func.count()).select_from(ClusterModel).scalar() or 0
        interpreted = (
            self.db.query(func.count())
            .select_from(ClusterModel)
            .filter(ClusterModel.ai_analysis.isnot(None))
            .scalar()
            or 0
        )
        return interpreted, total

    def get_sequence_interpretation_counts(self) -> tuple[int, int]:
        total = self.db.query(func.count()).select_from(PrefixSpanPatternModel).scalar() or 0
        interpreted = (
            self.db.query(func.count())
            .select_from(PrefixSpanPatternModel)
            .filter(PrefixSpanPatternModel.ai_analysis.isnot(None))
            .scalar()
            or 0
        )
        return interpreted, total
