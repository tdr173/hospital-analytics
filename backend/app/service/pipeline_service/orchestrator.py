import logging

from db.db_connector import engine, SessionLocal
from repository import PipelineRepository

logger = logging.getLogger(__name__)


def _stop_requested() -> bool:
    with SessionLocal() as db:
        return PipelineRepository(db).is_stop_requested()


def _mark_stopped() -> None:
    with SessionLocal() as db:
        PipelineRepository(db).mark_stopped()


def run_pipeline(triggered_by: str) -> None:
    """Sequential offline pipeline: ETL (only if patient table empty) ->
    clustering -> sequence mining (global, then per-cluster). Updates the
    pipeline_run singleton between stages so the frontend can poll progress.

    Safe to call from a background thread or the scheduler. Never raises: any
    failure is recorded on the state row.
    """
    # atomic guard: only one run at a time
    with SessionLocal() as db:
        if not PipelineRepository(db).try_mark_running(triggered_by):
            logger.info("Pipeline already running; ignoring %s trigger", triggered_by)
            return

    try:
        # --- Stage 1: ETL (first-run only) ---
        with SessionLocal() as db:
            patient_table_empty = PipelineRepository(db).is_patient_table_empty()
            PipelineRepository(db).set_stage("ETL", etl_skipped=not patient_table_empty)
        if patient_table_empty:
            logger.info("Pipeline: patient table empty, running ETL")
            from db.etl_script import run_etl
            run_etl(engine)
        else:
            logger.info("Pipeline: patient table populated, skipping ETL")

        if _stop_requested():
            logger.info("Pipeline (%s) stopped after ETL", triggered_by)
            _mark_stopped()
            return

        # --- Stage 2: Clustering ---
        with SessionLocal() as db:
            PipelineRepository(db).set_stage("CLUSTERING")
        from clustering_algorithms.k_prototypes.k_prototypes import run_clustering_stage
        run_clustering_stage(engine)

        if _stop_requested():
            logger.info("Pipeline (%s) stopped after clustering", triggered_by)
            _mark_stopped()
            return

        # --- Stage 3a: Sequence mining, global scope ---
        with SessionLocal() as db:
            PipelineRepository(db).set_stage("SEQUENCES_GLOBAL")
        from clustering_algorithms.prefix_span import prefix_span
        with SessionLocal() as db:
            prefix_span.run(engine, db, n_clusters=None)

        if _stop_requested():
            logger.info("Pipeline (%s) stopped after global sequence mining", triggered_by)
            _mark_stopped()
            return

        # --- Stage 3b: Sequence mining, per cluster (0..k-1 plus -1 outliers) ---
        with SessionLocal() as db:
            repo = PipelineRepository(db)
            repo.set_stage("SEQUENCES_CLUSTERS")
            n_clusters = repo.get_current_n_clusters()
        if n_clusters:
            labels = list(range(n_clusters)) + [-1]
            for label in labels:
                if _stop_requested():
                    logger.info("Pipeline (%s) stopped during per-cluster sequence mining", triggered_by)
                    _mark_stopped()
                    return
                with SessionLocal() as db:
                    prefix_span._run_single(engine, db, cluster_label=label)
        else:
            logger.warning("Pipeline: no cluster_meta found, skipping per-cluster sequence mining")

        with SessionLocal() as db:
            PipelineRepository(db).mark_success()
        logger.info("Pipeline (%s) completed successfully", triggered_by)

    except Exception as exc:
        logger.exception("Pipeline (%s) failed", triggered_by)
        try:
            with SessionLocal() as db:
                PipelineRepository(db).mark_failed(str(exc))
        except Exception:
            logger.exception("Pipeline: failed to record failure state")
