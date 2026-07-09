import threading
from typing import Optional

from repository import PipelineRepository
from domain import PipelineStatus, PipelineOverview
from service.pipeline_service.orchestrator import run_pipeline

PIPELINE_JOB_ID = "monthly_pipeline"


class PipelineService:
    def __init__(self, repo: PipelineRepository, scheduler=None):
        self.repo = repo
        self.scheduler = scheduler

    def _status_from_state(self, state) -> dict:
        return {
            "status": state.status,
            "current_stage": state.current_stage,
            "etl_skipped": state.etl_skipped,
            "triggered_by": state.triggered_by,
            "error": state.error,
            "started_at": state.started_at,
            "finished_at": state.finished_at,
            "stop_requested": state.stop_requested,
        }

    def _next_run(self) -> Optional[object]:
        if self.scheduler is None:
            return None
        job = self.scheduler.get_job(PIPELINE_JOB_ID)
        return job.next_run_time if job is not None else None

    def get_status(self) -> PipelineStatus:
        state = self.repo.get_state()
        return PipelineStatus(**self._status_from_state(state))

    def get_overview(self) -> PipelineOverview:
        state = self.repo.get_state()
        interpreted_clusters, total_clusters = self.repo.get_cluster_interpretation_counts()
        interpreted_sequences, total_sequences = self.repo.get_sequence_interpretation_counts()
        return PipelineOverview(
            **self._status_from_state(state),
            last_run=state.last_run_at,
            next_run=self._next_run(),
            interpreted_clusters=interpreted_clusters,
            total_clusters=total_clusters,
            interpreted_sequences=interpreted_sequences,
            total_sequences=total_sequences,
            counts=self.repo.get_data_counts(),
        )

    def start_manual(self) -> tuple[bool, PipelineStatus]:
        """Spawn the pipeline in a background daemon thread. Returns
        (started, status). started is False if a run is already in progress."""
        state = self.repo.get_state()
        if state.status == "RUNNING":
            return False, PipelineStatus(**self._status_from_state(state))

        thread = threading.Thread(
            target=run_pipeline,
            args=("manual",),
            name="pipeline-run",
            daemon=True,
        )
        thread.start()
        return True, PipelineStatus(**self._status_from_state(state))

    def stop_manual(self) -> tuple[bool, PipelineStatus]:
        """Request the running pipeline to stop at its next checkpoint.
        Returns (accepted, status). accepted is False if nothing is running."""
        accepted = self.repo.request_stop()
        state = self.repo.get_state()
        return accepted, PipelineStatus(**self._status_from_state(state))
