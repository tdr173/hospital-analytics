import json
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import text


def save_sequence_results(db: Session, result: dict) -> int:
    """
    Saves a PrefixSpan sequence mining run to the database.

    Tables used:
        sequence_run       — one row per execution (metadata + params)
        frequent_sequence  — one row per discovered frequent pattern

    Returns the run_id.
    """

    # 1. ensure tables exist
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS sequence_run (
            id              SERIAL PRIMARY KEY,
            created_at      TIMESTAMP NOT NULL,
            sequence_type   VARCHAR NOT NULL,
            n_patients      INTEGER NOT NULL,
            min_support     FLOAT NOT NULL,
            max_length      INTEGER NOT NULL,
            closed_only     BOOLEAN NOT NULL DEFAULT TRUE,
            n_patterns      INTEGER NOT NULL,
            length_stats    JSONB
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS frequent_sequence (
            id               SERIAL PRIMARY KEY,
            run_id           INTEGER NOT NULL REFERENCES sequence_run(id),
            pattern          JSONB NOT NULL,
            pattern_length   INTEGER NOT NULL,
            support_count    INTEGER NOT NULL,
            support_fraction FLOAT NOT NULL
        )
    """))
    db.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_frequent_sequence_run_id ON frequent_sequence(run_id)"
    ))

    # 2. insert run
    row = db.execute(
        text("""
            INSERT INTO sequence_run
                (created_at, sequence_type, n_patients, min_support, max_length,
                 closed_only, n_patterns, length_stats)
            VALUES
                (:created_at, :sequence_type, :n_patients, :min_support, :max_length,
                 :closed_only, :n_patterns, :length_stats)
            RETURNING id
        """),
        {
            "created_at": datetime.utcnow(),
            "sequence_type": result["sequence_type"],
            "n_patients": result["n_patients"],
            "min_support": result["min_support"],
            "max_length": result["max_length"],
            "closed_only": result.get("closed_only", True),
            "n_patterns": result["n_patterns"],
            "length_stats": json.dumps(result["sequence_length_stats"]),
        },
    )
    run_id = row.fetchone()[0]

    # 3. insert frequent patterns
    if result["patterns"]:
        db.execute(
            text("""
                INSERT INTO frequent_sequence
                    (run_id, pattern, pattern_length, support_count, support_fraction)
                VALUES
                    (:run_id, :pattern, :pattern_length, :support_count, :support_fraction)
            """),
            [
                {
                    "run_id": run_id,
                    "pattern": json.dumps(p["pattern"]),
                    "pattern_length": p["length"],
                    "support_count": p["support_count"],
                    "support_fraction": p["support_fraction"],
                }
                for p in result["patterns"]
            ],
        )

    db.commit()
    print(
        f"Saved sequence run_id={run_id}: {result['n_patterns']} patterns "
        f"({result['sequence_type']}, {result['n_patients']} patients)"
    )
    return run_id
