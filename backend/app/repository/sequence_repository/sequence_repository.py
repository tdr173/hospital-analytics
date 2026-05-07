from typing import Optional
from sqlalchemy import func, case, cast, Numeric, desc, asc, text
from sqlalchemy.orm import Session

from domain import (
    PrefixSpanPatternModel,
    PrefixSpanPatientPatternModel,
    ClusterPatientModel,
    SequenceListItem,
    SequenceListResponse,
    SequenceResourcesResponse,
    SequenceSortOption,
    PatientContinuationItem,
)
from repository._helpers import clamp_page_size


# Mirrors prefix_span.py miner constants so continuation results match what the
# miner saw when patterns were created.
_MINER_BLACKLIST_SUBSTRINGS = (
    "assessment of health and social care needs",
    "medication review due",
    "medication reconciliation",
)
_MINER_MAX_EVENTS_PER_PATIENT = 25
_MINER_PREFIX_ORDER = {"C": 0, "M": 1, "P": 2, "CP": 3}


SEQUENCE_PREFIX_COLORS = {
    "C": "#2563EB",   # Condition - blue
    "M": "#16A34A",   # Medication - green
    "P": "#EA580C",   # Procedure - orange
    "CP": "#7C3AED",  # CarePlan - purple
}

SEQUENCE_SORT_OPTIONS = [
    {"value": "support", "label": "Highest Support"},
    {"value": "length", "label": "Sequence Length"},
]


def _parse_pattern_steps(pattern_str: str) -> list[list[str]]:
    """Split `pattern_str` into ordered steps. A step is a list of tokens
    (strings of form "PREFIX:Value"). Same-day groups appear as
    `(C:X, M:Y)` and become a list of multiple tokens.

    Mirrors the FE parser frontend/app/(main)/sequences/utils/parsePattern.ts:8-19.
    """
    steps_raw = [s.strip() for s in pattern_str.split("->") if s.strip()]
    out: list[list[str]] = []
    for step in steps_raw:
        inner = step
        if inner.startswith("(") and inner.endswith(")"):
            inner = inner[1:-1]
        tokens = [t.strip() for t in inner.split(",") if t.strip()]
        if tokens:
            out.append(tokens)
    return out


def _format_step(tokens: list[str]) -> str:
    if len(tokens) == 1:
        return tokens[0]
    return "(" + ", ".join(tokens) + ")"


def _walk_prefix(events: list[str], steps: list[list[str]]) -> tuple[int, int]:
    """Greedy left-to-right walk: try to consume pattern steps in order.

    A step matches if every token in the step appears in the patient's
    remaining events; for single-token steps, "appears" means "shows up
    once at or after the cursor". For same-day group steps (multiple tokens),
    all tokens must appear at or after the cursor (not necessarily in order
    relative to each other), which mirrors how the FE renders these as a
    single grouped chip.

    Returns (prefix_length, last_consumed_event_idx). If prefix_length == 0,
    last_consumed_event_idx is -1.
    """
    cursor = 0
    last_idx = -1
    matched = 0
    for step in steps:
        consumed_idx = _try_consume_step(events, cursor, step)
        if consumed_idx == -1:
            break
        matched += 1
        last_idx = consumed_idx
        cursor = consumed_idx + 1
    return matched, last_idx


def _try_consume_step(events: list[str], start: int, step_tokens: list[str]) -> int:
    """Try to consume `step_tokens` from `events[start:]`. Returns the index
    of the LAST event used to satisfy this step, or -1 if no match.

    Single token: scan forward for the first matching event, return its index.
    Multiple tokens (same-day group): every token must occur at or after
      `start`; we accept the maximum index over the matched tokens, so the
      cursor advances past all of them.
    """
    if len(step_tokens) == 1:
        tok = step_tokens[0]
        for i in range(start, len(events)):
            if events[i] == tok:
                return i
        return -1

    indices: list[int] = []
    for tok in step_tokens:
        idx = -1
        for i in range(start, len(events)):
            if events[i] == tok:
                idx = i
                break
        if idx == -1:
            return -1
        indices.append(idx)
    return max(indices)


class SequenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_resources(self) -> SequenceResourcesResponse:
        row = self.db.query(
            func.min(PrefixSpanPatternModel.length).label("min_len"),
            func.max(PrefixSpanPatternModel.length).label("max_len"),
        ).first()
        min_len = int(row.min_len) if row and row.min_len is not None else 1
        max_len = int(row.max_len) if row and row.max_len is not None else 1
        return SequenceResourcesResponse(
            min_length=min_len,
            max_length=max_len,
            colors=SEQUENCE_PREFIX_COLORS,
            sort_options=[SequenceSortOption(**o) for o in SEQUENCE_SORT_OPTIONS],
        )

    def get_sequences(
        self,
        search: Optional[str] = None,
        min_length: int = 1,
        sort_by: str = "support",
        sort_type: str = "desc",
        page: int = 1,
        rows: int = 8,
    ) -> SequenceListResponse:
        q = self.db.query(PrefixSpanPatternModel).filter(
            PrefixSpanPatternModel.length >= min_length,
        )
        if search:
            q = q.filter(PrefixSpanPatternModel.pattern_str.ilike(f"%{search}%"))

        total = q.count()

        sort_col = (
            PrefixSpanPatternModel.length
            if sort_by == "length"
            else PrefixSpanPatternModel.support_count
        )
        order = desc if sort_type == "desc" else asc
        q = q.order_by(order(sort_col), PrefixSpanPatternModel.rank.asc())

        page = max(1, page)
        rows = clamp_page_size(rows)
        patterns = q.offset((page - 1) * rows).limit(rows).all()

        items = [
            SequenceListItem(
                id=p.id,
                rank=p.rank,
                pattern_str=p.pattern_str,
                length=p.length,
                support_count=p.support_count,
                support_pct=p.support_pct,
                has_ai_analysis=p.ai_analysis is not None,
            )
            for p in patterns
        ]
        return SequenceListResponse(total=total, items=items)

    def get_pattern(self, pattern_id: int) -> PrefixSpanPatternModel:
        pattern = self.db.query(PrefixSpanPatternModel).filter(
            PrefixSpanPatternModel.id == pattern_id
        ).first()
        if not pattern:
            raise ValueError(f"Pattern {pattern_id} not found")
        return pattern

    def get_pattern_ai_analysis(self, pattern_id: int) -> Optional[dict]:
        pattern = self.get_pattern(pattern_id)
        return pattern.ai_analysis

    def lock_pattern_ai_analysis(self, pattern_id: int) -> Optional[dict]:
        """Row-lock the pattern and return cached analysis if present.

        Caller must commit/rollback to release the lock - save_pattern_ai_analysis commits.
        """
        pattern = self.db.query(PrefixSpanPatternModel).filter(
            PrefixSpanPatternModel.id == pattern_id
        ).with_for_update().first()
        if not pattern:
            raise ValueError(f"Pattern {pattern_id} not found")
        return pattern.ai_analysis

    def save_pattern_ai_analysis(self, pattern_id: int, analysis: dict) -> None:
        self.db.query(PrefixSpanPatternModel).filter(
            PrefixSpanPatternModel.id == pattern_id
        ).update({"ai_analysis": analysis}, synchronize_session="fetch")
        self.db.commit()

    def _fetch_patient_event_tokens_ordered(self, patient_id: str) -> list[str]:
        """Build the patient's chronological list of `PREFIX:Description` tokens
        using the same encoding the prefix_span miner applies.

        The miner (clustering_algorithms/prefix_span/prefix_span.py:110-186):
          - UNION ALL over condition / medication / procedure / careplan
          - Orders by start_date ASC, then a fixed prefix rank (C, M, P, CP), then item
          - Drops items containing miner blacklist substrings
          - Collapses adjacent identical items
          - Caps at MAX_EVENTS_PER_PATIENT (25) most-recent events
        """
        sql = text("""
            SELECT event_date, item FROM (
                SELECT start_date AS event_date,
                       'C:'  || TRIM(description) AS item
                FROM condition
                WHERE patient_id = :pid AND description IS NOT NULL AND start_date IS NOT NULL
                UNION ALL
                SELECT start_date, 'M:'  || TRIM(description)
                FROM medication
                WHERE patient_id = :pid AND description IS NOT NULL AND start_date IS NOT NULL
                UNION ALL
                SELECT start_date, 'P:'  || TRIM(description)
                FROM "procedure"
                WHERE patient_id = :pid AND description IS NOT NULL AND start_date IS NOT NULL
                UNION ALL
                SELECT start_date, 'CP:' || TRIM(description)
                FROM careplan
                WHERE patient_id = :pid AND description IS NOT NULL AND start_date IS NOT NULL
            ) e
            ORDER BY event_date ASC, item ASC
        """)
        rows = self.db.execute(sql, {"pid": patient_id}).all()
        if not rows:
            return []

        # Re-sort using the miner's prefix-rank tiebreaker (C, M, P, CP) within
        # the same date — SQL's lexicographic ORDER BY on item already gives a
        # stable ordering, but to match the miner exactly we group by date and
        # apply the prefix_order, then item lexicographic.
        from collections import defaultdict
        by_date: dict = defaultdict(list)
        for r in rows:
            by_date[r.event_date].append(r.item)

        ordered: list[str] = []
        for d in sorted(by_date.keys()):
            items = by_date[d]
            items.sort(key=lambda it: (
                _MINER_PREFIX_ORDER.get(it.split(":", 1)[0], 99),
                it,
            ))
            ordered.extend(items)

        # Drop blacklisted items (Synthea protocol noise the miner strips).
        ordered = [
            it for it in ordered
            if not any(sub in it.lower() for sub in _MINER_BLACKLIST_SUBSTRINGS)
        ]

        # Collapse runs of identical adjacent items.
        deduped: list[str] = []
        for it in ordered:
            if not deduped or deduped[-1] != it:
                deduped.append(it)

        # Cap at the most recent N events.
        return deduped[-_MINER_MAX_EVENTS_PER_PATIENT:]

    def get_patient_continuations(
        self,
        patient_id: str,
        last_n: int = 3,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PatientContinuationItem], bool]:
        """Find patterns where the patient's recent events form a leading prefix.

        For each pattern: walk the patient's event list left-to-right, attempt
        to consume pattern steps in order. Accept the pattern iff
          1 <= prefix_length < pattern.length (continuation exists), AND
          the last consumed event index is within the trailing `last_n` window
          (keeps suggestions "fresh").

        Sorted: prefix_length DESC, support_count DESC, rank ASC.
        """
        events = self._fetch_patient_event_tokens_ordered(patient_id)
        if not events:
            return [], False

        last_window_start = max(0, len(events) - max(1, last_n))
        # All patterns of length >= 2 (need at least 1 prefix + 1 continuation).
        patterns = (
            self.db.query(PrefixSpanPatternModel)
            .filter(PrefixSpanPatternModel.length >= 2)
            .all()
        )

        matches: list[tuple[PrefixSpanPatternModel, int, int]] = []
        for p in patterns:
            steps = _parse_pattern_steps(p.pattern_str)
            if len(steps) < 2:
                continue

            prefix_length, last_idx = _walk_prefix(events, steps)
            if prefix_length == 0 or prefix_length >= len(steps):
                continue
            if last_idx < last_window_start:
                continue

            matches.append((p, prefix_length, last_idx))

        matches.sort(
            key=lambda m: (-m[1], -m[0].support_count, m[0].rank)
        )

        page_size = clamp_page_size(page_size)
        start = (max(1, page) - 1) * page_size
        window = matches[start:start + page_size + 1]
        has_more = len(window) > page_size
        window = window[:page_size]

        items: list[PatientContinuationItem] = []
        for p, prefix_length, _last_idx in window:
            steps = _parse_pattern_steps(p.pattern_str)
            matched_prefix_str = " -> ".join(_format_step(s) for s in steps[:prefix_length])
            items.append(PatientContinuationItem(
                pattern_id=p.id,
                rank=p.rank,
                pattern_str=p.pattern_str,
                length=p.length,
                support_count=p.support_count,
                support_pct=p.support_pct,
                has_ai_analysis=p.ai_analysis is not None,
                prefix_length=prefix_length,
                continuation_length=p.length - prefix_length,
                matched_prefix_str=matched_prefix_str,
            ))

        return items, has_more

    def get_pattern_ai_context(self, pattern_id: int) -> dict:
        pattern = self.get_pattern(pattern_id)

        def avg_feat(feature, decimals=1):
            return func.round(
                func.avg(cast(ClusterPatientModel.features[feature].astext, Numeric)),
                decimals,
            )

        def flag_pct(feature, value):
            return func.round(
                100.0 * func.sum(case(
                    (ClusterPatientModel.features[feature].astext == value, 1),
                    else_=0,
                )) / func.nullif(func.count(), 0),
                1,
            )

        stats = (
            self.db.query(
                func.count().label("patient_count"),
                avg_feat("age").label("avg_age"),
                avg_feat("avg_bmi", 1).label("avg_bmi"),
                avg_feat("total_medications").label("avg_meds"),
                avg_feat("active_conditions_count").label("avg_conditions"),
                flag_pct("gender", "F").label("female_pct"),
                flag_pct("gender", "M").label("male_pct"),
                flag_pct("has_diabetes", "Yes").label("diabetes_pct"),
                flag_pct("has_hypertension", "Yes").label("hypertension_pct"),
                flag_pct("has_heart_disease", "Yes").label("heart_disease_pct"),
                flag_pct("has_cancer", "Yes").label("cancer_pct"),
                flag_pct("is_polypharmacy", "Yes").label("polypharmacy_pct"),
                func.mode().within_group(
                    ClusterPatientModel.features["dominant_careplan"].astext
                ).label("dominant_careplan"),
            )
            .select_from(ClusterPatientModel)
            .join(
                PrefixSpanPatientPatternModel,
                PrefixSpanPatientPatternModel.patient_id == ClusterPatientModel.patient_id,
            )
            .filter(
                PrefixSpanPatientPatternModel.pattern_id == pattern_id,
                ClusterPatientModel.is_outlier == False,
            )
            .first()
        )

        raw = stats._asdict() if stats else {}
        fields = [
            "avg_age", "avg_bmi", "avg_meds", "avg_conditions",
            "female_pct", "male_pct", "diabetes_pct", "hypertension_pct",
            "heart_disease_pct", "cancer_pct", "polypharmacy_pct",
            "dominant_careplan",
        ]
        patient_stats = {k: (raw.get(k) if raw.get(k) is not None else "N/A") for k in fields}

        return {
            "pattern": {
                "pattern_str": pattern.pattern_str,
                "support_count": pattern.support_count,
                "support_pct": pattern.support_pct,
                "length": pattern.length,
            },
            "patient_stats": patient_stats,
        }
