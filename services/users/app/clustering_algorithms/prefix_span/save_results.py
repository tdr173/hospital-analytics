from sqlalchemy import text
from sqlalchemy.orm import Session


def save_prefix_span_results(
    db: Session,
    patterns: list[dict],
    patient_memberships: dict[int, list[str]],
) -> None:
    """Replace prefix_span_pattern + prefix_span_patient_pattern with fresh mined data.

    `patterns` — each dict: {rank, pattern_str, length, support_count, support_pct}.
    `patient_memberships` — {rank -> [patient_id, ...]} listing which patients contain each pattern.

    Wipes both tables first (junction before parent to satisfy FK), then inserts fresh rows
    and maps each (rank -> inserted id) so we can populate the junction with the correct
    pattern_id. `ai_analysis` is left NULL on write; it is filled lazily by the LLM endpoint.
    """
    db.execute(text("DELETE FROM prefix_span_patient_pattern"))
    db.execute(text("DELETE FROM prefix_span_pattern"))

    rank_to_id: dict[int, int] = {}
    insert_pattern = text("""
        INSERT INTO prefix_span_pattern (rank, pattern_str, length, support_count, support_pct)
        VALUES (:rank, :pattern_str, :length, :support_count, :support_pct)
        RETURNING id
    """)

    for p in patterns:
        pattern_id = db.execute(insert_pattern, p).scalar_one()
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
    print(
        f"Saved: {len(patterns)} patterns + {len(junction_rows)} patient-pattern links"
    )
