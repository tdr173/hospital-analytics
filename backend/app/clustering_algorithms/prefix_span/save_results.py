from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def save_prefix_span_results(
    db: Session,
    patterns: list[dict],
    patient_memberships: dict[int, list[str]],
    cluster_label: Optional[int] = None,
) -> None:
    """Replace prefix_span_pattern + prefix_span_patient_pattern rows for the given scope.

    `cluster_label=None` targets the global mining run (rows where cluster_label IS NULL).
    An integer value targets only that cluster's rows, leaving all other scopes untouched.

    Wipes the scoped rows first (junction before parent to satisfy FK), then inserts fresh
    rows and maps (rank → inserted id) so the junction gets the correct pattern_id.
    `ai_analysis` is left NULL on write; it is filled lazily by the LLM endpoint.
    """
    # Delete junction rows for this scope first (FK child before parent).
    db.execute(text("""
        DELETE FROM prefix_span_patient_pattern pp
        USING prefix_span_pattern p
        WHERE pp.pattern_id = p.id
          AND (
            (:label IS NULL AND p.cluster_label IS NULL)
            OR (p.cluster_label = :label)
          )
    """), {"label": cluster_label})

    db.execute(text("""
        DELETE FROM prefix_span_pattern
        WHERE (
            (:label IS NULL AND cluster_label IS NULL)
            OR cluster_label = :label
        )
    """), {"label": cluster_label})

    rank_to_id: dict[int, int] = {}
    insert_pattern = text("""
        INSERT INTO prefix_span_pattern (rank, pattern_str, length, support_count, support_pct, cluster_label)
        VALUES (:rank, :pattern_str, :length, :support_count, :support_pct, :cluster_label)
        RETURNING id
    """)

    for p in patterns:
        row = {**p, "cluster_label": cluster_label}
        pattern_id = db.execute(insert_pattern, row).scalar_one()
        rank_to_id[p["rank"]] = pattern_id

    junction_rows: list[dict] = []
    for rank, patient_ids in patient_memberships.items():
        pattern_id = rank_to_id.get(rank)
        if pattern_id is None:
            continue
        for pid in patient_ids:
            junction_rows.append({"pattern_id": pattern_id, "patient_id": pid})

    if junction_rows:
        db.execute(
            text("""
                INSERT INTO prefix_span_patient_pattern (pattern_id, patient_id)
                VALUES (:pattern_id, :patient_id)
            """),
            junction_rows,
        )

    db.commit()
    scope_tag = "global" if cluster_label is None else f"cluster {cluster_label}"
    print(
        f"Saved ({scope_tag}): {len(patterns)} patterns + {len(junction_rows)} patient-pattern links"
    )
