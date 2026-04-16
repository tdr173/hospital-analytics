from typing import Callable, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, cast, Numeric, literal

from domain import (
    PatientModel, ClusterPatientModel, ClusterModel,
    EncounterModel, ProviderModel, OrganizationModel,
    ConditionModel, MedicationModel, ProcedureModel, ImmunizationModel, AllergyModel,
    ObservationModel, CarePlanModel,
    PrefixSpanPatternModel, PrefixSpanPatientPatternModel,
    PatientListItem, PatientListResponse, PatientDetailResponse,
    PatientSummaryResponse, ConditionItem, MedicationItem,
    ProcedureItem, ImmunizationItem, AllergyItem, CarePlanItem, EncounterItem,
    FilterOption, PatientResourcesResponse, SequenceListItem,
)
from repository._helpers import provider_name_col, clamp_page_size

SORT_COL_MAP = {
    "last_name": PatientModel.last_name,
    "first_name": PatientModel.first_name,
    "age": PatientModel.age,
    "city": PatientModel.city,
    "gender": PatientModel.gender,
    "race": PatientModel.race,
    "marital": PatientModel.marital,
}

AGE_GROUP_RANGES = {
    "child":        (0,  17),
    "young_adult":  (18, 34),
    "middle_aged":  (35, 54),
    "senior":       (55, 69),
    "elderly":      (70, 999),
}

_LIST_COLS = [
    PatientModel.patient_id,
    PatientModel.first_name,
    PatientModel.last_name,
    PatientModel.age,
    PatientModel.gender,
    PatientModel.city,
    PatientModel.race,
    PatientModel.ethnicity,
    PatientModel.marital,
    PatientModel.birthdate,
    PatientModel.deathdate,
]

_DETAIL_COLS = _LIST_COLS + [
    PatientModel.latitude,
    PatientModel.longitude,
]


class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def _has_cluster_data(self) -> bool:
        return self.db.query(ClusterPatientModel).count() > 0

    def _patient_query_with_cluster(self, base_cols: list):
        if self._has_cluster_data():
            return (
                self.db.query(
                    *base_cols,
                    ClusterPatientModel.cluster_label,
                    ClusterModel.title.label("cluster_title"),
                    ClusterModel.color.label("cluster_color"),
                )
                .outerjoin(
                    ClusterPatientModel,
                    ClusterPatientModel.patient_id == PatientModel.patient_id,
                )
                .outerjoin(
                    ClusterModel,
                    ClusterModel.cluster_label == ClusterPatientModel.cluster_label,
                )
            )
        return self.db.query(
            *base_cols,
            literal(None).label("cluster_label"),
            literal(None).label("cluster_title"),
            literal(None).label("cluster_color"),
        )

    @staticmethod
    def _cached_or_scalar(features: dict, key: str, query_fn: Callable):
        cached = features.get(key)
        if cached is not None:
            return cached
        return query_fn()

    def get_patients(
        self,
        search: Optional[str],
        gender: Optional[str],
        age_group: Optional[str],
        status: Optional[str],
        race: Optional[str],
        marital: Optional[str],
        city: Optional[str],
        page: int,
        rows: int,
        sort_by: str,
        sort_type: str,
    ) -> PatientListResponse:
        sort_col = SORT_COL_MAP.get(sort_by, PatientModel.last_name)
        sort_expr = (
            sort_col.asc().nulls_last()
            if sort_type.lower() == "asc"
            else sort_col.desc().nulls_last()
        )

        filters = []

        if search:
            filters.append(or_(
                PatientModel.first_name.ilike(f"%{search}%"),
                PatientModel.last_name.ilike(f"%{search}%"),
                PatientModel.city.ilike(f"%{search}%"),
            ))

        if gender:
            genders = [g.strip() for g in gender.split(",") if g.strip()]
            if genders:
                filters.append(PatientModel.gender.in_(genders))

        if age_group:
            groups = [g.strip() for g in age_group.split(",") if g.strip() and g.strip() in AGE_GROUP_RANGES]
            if groups:
                age_parts = []
                for g in groups:
                    lo, hi = AGE_GROUP_RANGES[g]
                    age_parts.append(and_(PatientModel.age >= lo, PatientModel.age <= hi))
                filters.append(or_(*age_parts))

        if status:
            statuses = {s.strip() for s in status.split(",") if s.strip()}
            has_alive = "alive" in statuses
            has_deceased = "deceased" in statuses
            if has_alive and not has_deceased:
                filters.append(PatientModel.deathdate.is_(None))
            elif has_deceased and not has_alive:
                filters.append(PatientModel.deathdate.isnot(None))

        if race:
            races = [r.strip() for r in race.split(",") if r.strip()]
            if races:
                filters.append(PatientModel.race.in_(races))

        if marital:
            maritals = [m.strip() for m in marital.split(",") if m.strip()]
            if maritals:
                filters.append(PatientModel.marital.in_(maritals))

        if city:
            filters.append(PatientModel.city.ilike(f"%{city}%"))

        total = self.db.query(func.count(PatientModel.patient_id)).filter(*filters).scalar() or 0

        rows = clamp_page_size(rows)
        offset = (page - 1) * rows
        rows_data = (
            self._patient_query_with_cluster(_LIST_COLS)
            .filter(*filters)
            .order_by(sort_expr)
            .limit(rows)
            .offset(offset)
            .all()
        )

        items = [PatientListItem(**row._asdict()) for row in rows_data]
        return PatientListResponse(items=items, total=total)

    def get_patient(self, patient_id: str) -> PatientDetailResponse:
        row = (
            self._patient_query_with_cluster(_DETAIL_COLS)
            .filter(PatientModel.patient_id == patient_id)
            .first()
        )
        if not row:
            raise ValueError(f"Patient {patient_id} not found")
        return PatientDetailResponse(**row._asdict())

    def get_patient_summary(self, patient_id: str) -> PatientSummaryResponse:
        cp = (
            self.db.query(ClusterPatientModel)
            .filter(ClusterPatientModel.patient_id == patient_id)
            .first()
        )
        f = cp.features if cp and cp.features else {}

        qaly = self._cached_or_scalar(f, "qaly", lambda: (
            self.db.query(ObservationModel.value_numeric)
            .filter(
                ObservationModel.patient_id == patient_id,
                ObservationModel.description == 'QALY',
            )
            .order_by(ObservationModel.date.desc())
            .limit(1)
            .scalar()
        ))

        def _avg_bmi():
            bmi_subq = (
                self.db.query(ObservationModel.value_numeric)
                .filter(
                    ObservationModel.patient_id == patient_id,
                    ObservationModel.description == 'Body Mass Index',
                    ObservationModel.value_numeric.isnot(None),
                )
                .order_by(ObservationModel.date.desc())
                .limit(5)
                .subquery()
            )
            return self.db.query(
                func.round(cast(func.avg(bmi_subq.c.value_numeric), Numeric), 1)
            ).scalar()

        avg_bmi = self._cached_or_scalar(f, "avg_bmi", _avg_bmi)

        active_conditions = self._cached_or_scalar(f, "active_conditions_count", lambda: (
            self.db.query(func.count(ConditionModel.id))
            .filter(
                ConditionModel.patient_id == patient_id,
                ConditionModel.end_date.is_(None),
            )
            .scalar()
        ))

        total_medications = self._cached_or_scalar(f, "total_medications", lambda: (
            self.db.query(func.count(MedicationModel.id))
            .filter(MedicationModel.patient_id == patient_id)
            .scalar()
        ))

        total_procedures = self._cached_or_scalar(f, "total_procedures", lambda: (
            self.db.query(func.count(ProcedureModel.id))
            .filter(ProcedureModel.patient_id == patient_id)
            .scalar()
        ))

        emergency_visits = self._cached_or_scalar(f, "emergency_count", lambda: (
            self.db.query(func.count(EncounterModel.encounter_id))
            .filter(
                EncounterModel.patient_id == patient_id,
                EncounterModel.encounter_class == 'emergency',
            )
            .scalar()
        ))

        days_since_last_encounter = self._cached_or_scalar(f, "days_since_last_encounter", lambda: (
            self.db.query(
                func.extract('day', func.now() - func.max(EncounterModel.start_date))
            )
            .filter(EncounterModel.patient_id == patient_id)
            .scalar()
        ))

        return PatientSummaryResponse(
            qaly=round(float(qaly), 2) if qaly is not None else None,
            avg_bmi=round(float(avg_bmi), 1) if avg_bmi is not None else None,
            active_conditions=int(active_conditions or 0),
            total_medications=int(total_medications or 0),
            total_procedures=int(total_procedures or 0),
            emergency_visits=int(emergency_visits or 0),
            days_since_last_encounter=int(days_since_last_encounter or 0) if days_since_last_encounter is not None else None,
        )

    def get_patient_conditions(self, patient_id: str) -> list[ConditionItem]:
        rows = (
            self.db.query(ConditionModel)
            .filter(ConditionModel.patient_id == patient_id)
            .order_by(ConditionModel.start_date.desc())
            .all()
        )
        return [
            ConditionItem(
                id=r.id,
                description=r.description,
                condition_code=str(r.condition_code),
                start_date=r.start_date,
                end_date=r.end_date,
            )
            for r in rows
        ]

    def get_patient_medications(self, patient_id: str) -> list[MedicationItem]:
        rows = (
            self.db.query(MedicationModel)
            .filter(MedicationModel.patient_id == patient_id)
            .order_by(MedicationModel.start_date.desc())
            .all()
        )
        return [
            MedicationItem(
                id=r.id,
                description=r.description,
                medication_code=str(r.medication_code),
                start_date=r.start_date,
                end_date=r.end_date,
                duration_days=r.duration_days,
                reason_description=r.reason_description,
            )
            for r in rows
        ]

    def get_patient_procedures(self, patient_id: str) -> list[ProcedureItem]:
        rows = (
            self.db.query(ProcedureModel)
            .filter(ProcedureModel.patient_id == patient_id)
            .order_by(ProcedureModel.start_date.desc())
            .all()
        )
        return [
            ProcedureItem(
                id=r.id,
                description=r.description,
                procedure_code=str(r.procedure_code),
                start_date=r.start_date,
                end_date=r.end_date,
                reason_description=r.reason_description,
            )
            for r in rows
        ]

    def get_patient_immunizations(self, patient_id: str) -> list[ImmunizationItem]:
        rows = (
            self.db.query(ImmunizationModel)
            .filter(ImmunizationModel.patient_id == patient_id)
            .order_by(ImmunizationModel.date.desc())
            .all()
        )
        return [
            ImmunizationItem(
                id=r.id,
                description=r.description,
                immunization_code=str(r.immunization_code),
                date=r.date,
            )
            for r in rows
        ]

    def get_patient_careplans(self, patient_id: str) -> list[CarePlanItem]:
        rows = (
            self.db.query(CarePlanModel)
            .filter(CarePlanModel.patient_id == patient_id)
            .order_by(CarePlanModel.start_date.desc())
            .all()
        )
        return [
            CarePlanItem(
                id=r.id,
                description=r.description,
                careplan_code=str(r.careplan_code),
                start_date=r.start_date,
                end_date=r.end_date,
                duration_days=r.duration_days,
                reason_description=r.reason_description,
            )
            for r in rows
        ]

    def get_patient_allergies(self, patient_id: str) -> list[AllergyItem]:
        rows = (
            self.db.query(AllergyModel)
            .filter(AllergyModel.patient_id == patient_id)
            .order_by(AllergyModel.start_date.desc())
            .all()
        )
        return [
            AllergyItem(
                id=r.id,
                description=r.description,
                allergy_code=str(r.allergy_code),
                start_date=r.start_date,
                end_date=r.end_date,
            )
            for r in rows
        ]

    def get_patient_resources(self) -> PatientResourcesResponse:
        return PatientResourcesResponse(
            genders=[
                FilterOption(value="M", label="Male"),
                FilterOption(value="F", label="Female"),
            ],
            age_groups=[
                FilterOption(value="child", label="Child"),
                FilterOption(value="young_adult", label="Young Adult"),
                FilterOption(value="middle_aged", label="Middle Aged"),
                FilterOption(value="senior", label="Senior"),
                FilterOption(value="elderly", label="Elderly"),
            ],
            statuses=[
                FilterOption(value="alive", label="Alive"),
                FilterOption(value="deceased", label="Deceased"),
            ],
            races=[
                FilterOption(value="White", label="White"),
                FilterOption(value="Black", label="Black"),
                FilterOption(value="Asian", label="Asian"),
                FilterOption(value="Native", label="Native"),
                FilterOption(value="Hispanic", label="Hispanic"),
                FilterOption(value="Other", label="Other"),
            ],
            marital_statuses=[
                FilterOption(value="M", label="Married"),
                FilterOption(value="S", label="Single"),
                FilterOption(value="D", label="Divorced"),
                FilterOption(value="W", label="Widowed"),
            ],
        )

    def get_patient_encounters(self, patient_id: str) -> list[EncounterItem]:
        rows = (
            self.db.query(
                EncounterModel.encounter_id,
                EncounterModel.start_date,
                EncounterModel.end_date,
                EncounterModel.duration,
                EncounterModel.encounter_class,
                EncounterModel.description,
                EncounterModel.reason_description,
                provider_name_col(),
                OrganizationModel.name.label("organization_name"),
            )
            .outerjoin(ProviderModel, EncounterModel.provider_id == ProviderModel.provider_id)
            .outerjoin(OrganizationModel, EncounterModel.organization_id == OrganizationModel.organization_id)
            .filter(EncounterModel.patient_id == patient_id)
            .order_by(EncounterModel.start_date.desc())
            .all()
        )
        return [EncounterItem(**row._asdict()) for row in rows]

    def get_patient_sequences(self, patient_id: str) -> list[SequenceListItem]:
        rows = (
            self.db.query(PrefixSpanPatternModel)
            .join(
                PrefixSpanPatientPatternModel,
                PrefixSpanPatientPatternModel.pattern_id == PrefixSpanPatternModel.id,
            )
            .filter(PrefixSpanPatientPatternModel.patient_id == patient_id)
            .order_by(
                PrefixSpanPatternModel.support_count.desc(),
                PrefixSpanPatternModel.rank.asc(),
            )
            .all()
        )
        return [
            SequenceListItem(
                id=r.id,
                rank=r.rank,
                pattern_str=r.pattern_str,
                length=r.length,
                support_count=r.support_count,
                support_pct=r.support_pct,
                has_ai_analysis=r.ai_analysis is not None,
            )
            for r in rows
        ]
