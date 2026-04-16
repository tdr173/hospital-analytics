"""
Persist PrefixSpan results to the database.

Tables (defined as ORM models in domain/models/):
  prefix_span_pattern          — one row per mined pattern
  prefix_span_patient_pattern  — junction: patient ↔ pattern

Access patterns after saving:
  Patient → sequences  : SELECT * FROM prefix_span_patient_pattern WHERE patient_id = '...'
  Sequence → patients  : SELECT * FROM prefix_span_patient_pattern WHERE pattern_id = <id>
  Cluster → sequences  : JOIN prefix_span_patient_pattern pp
                             ON pp.patient_id = cluster_patient.patient_id
                         WHERE cluster_patient.cluster_label = <N>

Overwrite vs Append:
  overwrite=True  → DELETE both tables, then insert fresh results.
  overwrite=False → INSERT without deleting; useful for combining results
                    from multiple runs / different configurations.
"""

from sqlalchemy import text


def save_sequence_results(
    engine,
    patterns: list,            # list of (support_count, pattern, seq_ids)
    patient_ids: list[str],    # patient_ids[seq_id] → patient UUID
    id_to_item: list[str],     # id_to_item[item_id] → item string
    format_pattern,            # callable(pattern, id_to_item) → str
    overwrite: bool = True,
) -> None:
    n_sequences = len(patient_ids)
    total_junction_rows = 0

    # engine.begin() opens a transaction and commits on successful exit,
    # rolls back on any exception. All deletes and inserts run atomically:
    # a failure mid-save leaves the tables exactly as they were before.
    with engine.begin() as conn:
        if overwrite:
            # junction must be cleared first — it references prefix_span_pattern(id).
            conn.execute(text("DELETE FROM prefix_span_patient_pattern"))
            conn.execute(text("DELETE FROM prefix_span_pattern"))

        for rank, (sup, pat, seq_ids) in enumerate(patterns, start=1):
            pattern_str = format_pattern(pat, id_to_item)
            length = sum(len(iset) for iset in pat)
            support_pct = round(100.0 * sup / n_sequences, 2) if n_sequences else 0.0

            result = conn.execute(
                text("""
                    INSERT INTO prefix_span_pattern
                        (rank, pattern_str, length, support_count, support_pct)
                    VALUES
                        (:rank, :pattern_str, :length, :support_count, :support_pct)
                    RETURNING id
                """),
                {
                    "rank": rank,
                    "pattern_str": pattern_str,
                    "length": length,
                    "support_count": sup,
                    "support_pct": support_pct,
                },
            )
            pattern_id = result.fetchone()[0]

            # Deduplicate seq_ids defensively so the junction never ends up
            # with duplicate (pattern_id, patient_id) pairs when the same
            # patient is mapped to multiple internal sequence ids (shouldn't
            # happen in normal runs, but is cheap insurance).
            unique_seq_ids = set(seq_ids)
            junction_rows = [
                {"pattern_id": pattern_id, "patient_id": patient_ids[sid]}
                for sid in unique_seq_ids
                if patient_ids[sid] is not None
            ]
            if junction_rows:
                conn.execute(
                    text("""
                        INSERT INTO prefix_span_patient_pattern (pattern_id, patient_id)
                        VALUES (:pattern_id, :patient_id)
                        ON CONFLICT DO NOTHING
                    """),
                    junction_rows,
                )
                total_junction_rows += len(junction_rows)

    print(
        f"saved {len(patterns)} patterns and {total_junction_rows} junction rows "
        f"(overwrite={overwrite})"
    )
