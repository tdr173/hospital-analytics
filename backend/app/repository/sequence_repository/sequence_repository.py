from typing import Optional
from sqlalchemy import func, case, cast, Numeric, desc, asc, text
from sqlalchemy.orm import Session

from domain import (
    PrefixSpanPatternModel,
    PrefixSpanPatientPatternModel,
    ClusterPatientModel,
    SequenceListItem,
    SequenceContinuationItem,
    SequenceListResponse,
    SequenceResourcesResponse,
    SequenceSortOption,
)
from repository._helpers import clamp_page_size


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


class SequenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_resources(self) -> SequenceResourcesResponse:
        row = self.db.query(
            func.min(PrefixSpanPatternModel.length).label("min_len"),
            func.max(PrefixSpanPatternModel.length).label("max_len"),
        ).filter(PrefixSpanPatternModel.cluster_label == None).first()
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
        cluster_labels: Optional[list[int]] = None,
    ) -> SequenceListResponse:
        q = self.db.query(PrefixSpanPatternModel).filter(
            PrefixSpanPatternModel.length >= min_length,
        )

        if cluster_labels is not None:
            q = q.filter(PrefixSpanPatternModel.cluster_label.in_(cluster_labels))
        else:
            q = q.filter(PrefixSpanPatternModel.cluster_label == None)

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

    def get_patient_continuations(
        self,
        patient_id: str,
        min_matched: int = 2,
    ) -> list[SequenceContinuationItem]:
        _BLACKLIST = frozenset({
            "assessment of health and social care needs",
            "medication review due",
            "medication reconciliation",
        })
        _MAX_EVENTS = 25

        rows = self.db.execute(text("""
            SELECT start_date AS event_date, 'C:' || TRIM(description) AS item, 0 AS pref_rank
            FROM condition
            WHERE patient_id = :pid AND description IS NOT NULL AND start_date IS NOT NULL
            UNION ALL
            SELECT start_date, 'M:' || TRIM(description), 1
            FROM medication
            WHERE patient_id = :pid AND description IS NOT NULL AND start_date IS NOT NULL
            UNION ALL
            SELECT start_date, 'P:' || TRIM(description), 2
            FROM "procedure"
            WHERE patient_id = :pid AND description IS NOT NULL AND start_date IS NOT NULL
            UNION ALL
            SELECT start_date, 'CP:' || TRIM(description), 3
            FROM careplan
            WHERE patient_id = :pid AND description IS NOT NULL AND start_date IS NOT NULL
            ORDER BY event_date, pref_rank, item
        """), {"pid": patient_id}).fetchall()

        events = [r.item for r in rows if not any(bl in r.item.lower() for bl in _BLACKLIST)]

        deduped: list[str] = []
        for e in events:
            if not deduped or deduped[-1] != e:
                deduped.append(e)

        patient_events = deduped[-_MAX_EVENTS:]
        if len(patient_events) < min_matched:
            return []

        completed_ids = {
            row[0]
            for row in self.db.query(PrefixSpanPatientPatternModel.pattern_id)
            .filter(PrefixSpanPatientPatternModel.patient_id == patient_id)
            .all()
        }

        all_patterns = self.db.query(PrefixSpanPatternModel).all()

        results: list[SequenceContinuationItem] = []
        for pattern in all_patterns:
            if pattern.id in completed_ids:
                continue
            steps = pattern.pattern_str.split(" -> ")
            if len(steps) <= min_matched:
                continue
            max_k = min(len(steps) - 1, len(patient_events))
            for k in range(max_k, min_matched - 1, -1):
                if patient_events[-k:] == steps[:k]:
                    results.append(SequenceContinuationItem(
                        id=pattern.id,
                        rank=pattern.rank,
                        pattern_str=pattern.pattern_str,
                        length=pattern.length,
                        support_count=pattern.support_count,
                        support_pct=pattern.support_pct,
                        has_ai_analysis=pattern.ai_analysis is not None,
                        matched_steps=k,
                        matched_pattern_str=" -> ".join(steps[:k]),
                    ))
                    break

        results.sort(key=lambda x: (-x.matched_steps, -x.support_count))
        return results

    def save_pattern_ai_analysis(self, pattern_id: int, analysis: dict) -> None:
        self.db.query(PrefixSpanPatternModel).filter(
            PrefixSpanPatternModel.id == pattern_id
        ).update({"ai_analysis": analysis}, synchronize_session="fetch")
        self.db.commit()

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
