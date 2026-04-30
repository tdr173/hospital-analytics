from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case, text, Date, cast, Numeric

from domain import (
    PatientModel, ProviderModel, OrganizationModel, EncounterModel,
    ConditionModel, ClusterModel, ClusterPatientModel,
    KpiCards, EncounterClassItem, GenderDistributionItem, AgeGroupItem,
    DailyEncounterItem, RecentEncounterItem, DashboardResponse,
    TopConditionItem, ClusterDistributionItem,
)
from domain.models.careplan_model import CarePlanModel
from domain.models.procedure_model import ProcedureModel
from repository._helpers import patient_name_col, provider_name_col

AGE_GROUP_CASE = case(
    (PatientModel.age <= 17, "Child"),
    (PatientModel.age <= 34, "Young Adult"),
    (PatientModel.age <= 54, "Middle Aged"),
    (PatientModel.age <= 69, "Senior"),
    else_="Elderly",
)

AGE_GROUP_ORDER = ["Child", "Young Adult", "Middle Aged", "Senior", "Elderly"]


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self, scope=None) -> DashboardResponse:
        provider_id: Optional[str] = None
        if scope is not None and scope.is_doctor:
            provider_id = scope.provider_id

        if provider_id:
            return self._get_dashboard_scoped(provider_id)
        return self._get_dashboard_all()

    # ----------------------------------------------------------------- scoped

    def _get_dashboard_scoped(self, provider_id: str) -> DashboardResponse:
        provider_patients_subq = (
            self.db.query(EncounterModel.patient_id)
            .filter(EncounterModel.provider_id == provider_id)
            .distinct()
            .subquery()
        )
        pat_filter = PatientModel.patient_id.in_(provider_patients_subq)
        enc_filter = EncounterModel.provider_id == provider_id

        total_patients = (
            self.db.query(func.count(PatientModel.patient_id))
            .filter(pat_filter)
            .scalar() or 0
        )
        active_patients = (
            self.db.query(func.count(PatientModel.patient_id))
            .filter(pat_filter, PatientModel.deathdate.is_(None))
            .scalar() or 0
        )
        total_encounters = (
            self.db.query(func.count(EncounterModel.encounter_id))
            .filter(enc_filter)
            .scalar() or 0
        )
        total_conditions = (
            self.db.query(func.count(ConditionModel.id))
            .filter(ConditionModel.patient_id.in_(provider_patients_subq))
            .scalar() or 0
        )
        total_careplans = (
            self.db.query(func.count(CarePlanModel.careplan_code))
            .filter(CarePlanModel.patient_id.in_(provider_patients_subq))
            .scalar() or 0
        )
        total_procedures = (
            self.db.query(func.count(ProcedureModel.procedure_code))
            .filter(ProcedureModel.patient_id.in_(provider_patients_subq))
            .scalar() or 0
        )
        active_careplans = (
            self.db.query(func.count(CarePlanModel.careplan_code))
            .filter(
                CarePlanModel.patient_id.in_(provider_patients_subq),
                (CarePlanModel.end_date.is_(None)),
            )
            .scalar() or 0
        )
        avg_enc = round(total_encounters / total_patients, 2) if total_patients else 0.0
        avg_age_row = (
            self.db.query(func.round(cast(func.avg(PatientModel.age), Numeric), 1))
            .filter(pat_filter)
            .scalar()
        )

        new_patients_last_30_days = 0
        max_encounter_date = (
            self.db.query(func.max(EncounterModel.start_date))
            .filter(enc_filter)
            .scalar()
        )
        if max_encounter_date is not None:
            cutoff = max_encounter_date - timedelta(days=30)
            new_patients_last_30_days = (
                self.db.query(func.count(func.distinct(EncounterModel.patient_id)))
                .filter(
                    enc_filter,
                    EncounterModel.start_date >= cutoff,
                )
                .scalar() or 0
            )

        kpis = KpiCards(
            total_patients=total_patients,
            active_patients=active_patients,
            total_providers=1,
            total_organizations=0,
            total_encounters=total_encounters,
            total_conditions=total_conditions,
            total_careplans=total_careplans,
            total_procedures=total_procedures,
            avg_encounters_per_patient=avg_enc,
            active_careplans=active_careplans,
            new_patients_last_30_days=new_patients_last_30_days,
            avg_patient_age=float(avg_age_row or 0),
        )

        last_week_encounter_by_class: list[EncounterClassItem] = []
        if max_encounter_date is not None:
            week_cutoff = max_encounter_date - timedelta(days=7)
            encounter_rows = (
                self.db.query(
                    EncounterModel.encounter_class,
                    func.count(EncounterModel.encounter_id).label("count"),
                )
                .filter(enc_filter, EncounterModel.start_date >= week_cutoff)
                .group_by(EncounterModel.encounter_class)
                .order_by(func.count(EncounterModel.encounter_id).desc())
                .all()
            )
            last_week_encounter_by_class = [
                EncounterClassItem(encounter_class=r.encounter_class, count=r.count)
                for r in encounter_rows
            ]

        gender_rows = (
            self.db.query(
                PatientModel.gender,
                func.count(PatientModel.patient_id).label("count"),
            )
            .filter(pat_filter, PatientModel.gender.isnot(None))
            .group_by(PatientModel.gender)
            .all()
        )
        gender_distribution = [
            GenderDistributionItem(gender=r.gender, count=r.count)
            for r in gender_rows
        ]

        age_group_rows = (
            self.db.query(
                AGE_GROUP_CASE.label("age_group"),
                func.count(PatientModel.patient_id).label("count"),
            )
            .filter(pat_filter)
            .group_by(AGE_GROUP_CASE)
            .all()
        )
        age_group_map = {r.age_group: r.count for r in age_group_rows}
        age_groups = [
            AgeGroupItem(age_group=g, count=age_group_map.get(g, 0))
            for g in AGE_GROUP_ORDER
        ]

        last_month_encounters: list[DailyEncounterItem] = []
        if max_encounter_date is not None:
            month_cutoff = max_encounter_date - timedelta(days=30)
            daily_rows = (
                self.db.query(
                    func.to_char(cast(EncounterModel.start_date, Date), "YYYY-MM-DD").label("day"),
                    func.count(EncounterModel.encounter_id).label("count"),
                )
                .filter(enc_filter, EncounterModel.start_date >= month_cutoff)
                .group_by(cast(EncounterModel.start_date, Date))
                .order_by(cast(EncounterModel.start_date, Date).asc())
                .all()
            )
            last_month_encounters = [
                DailyEncounterItem(day=r.day, count=r.count)
                for r in daily_rows
            ]

        recent_rows = (
            self.db.query(
                EncounterModel.encounter_id,
                EncounterModel.patient_id,
                patient_name_col(),
                provider_name_col(),
                OrganizationModel.name.label("organization_name"),
                EncounterModel.start_date,
                EncounterModel.encounter_class,
                EncounterModel.description,
            )
            .outerjoin(PatientModel, EncounterModel.patient_id == PatientModel.patient_id)
            .outerjoin(ProviderModel, EncounterModel.provider_id == ProviderModel.provider_id)
            .outerjoin(OrganizationModel, EncounterModel.organization_id == OrganizationModel.organization_id)
            .filter(enc_filter)
            .order_by(EncounterModel.start_date.desc())
            .limit(10)
            .all()
        )
        recent_encounters = [RecentEncounterItem(**r._asdict()) for r in recent_rows]

        return DashboardResponse(
            kpis=kpis,
            last_week_encounter_by_class=last_week_encounter_by_class,
            top_conditions_last_week=[],
            cluster_distribution=[],
            gender_distribution=gender_distribution,
            age_groups=age_groups,
            last_month_encounters=last_month_encounters,
            recent_encounters=recent_encounters,
        )

    # -------------------------------------------------------------------- all

    def _get_dashboard_all(self) -> DashboardResponse:
        kpi_row = self.db.execute(text("""
            SELECT
                (SELECT count(*) FROM patient)                                                 AS total_patients,
                (SELECT count(*) FROM patient WHERE deathdate IS NULL)                         AS active_patients,
                (SELECT count(*) FROM provider)                                                AS total_providers,
                (SELECT count(*) FROM organization)                                            AS total_organizations,
                (SELECT count(*) FROM encounter)                                               AS total_encounters,
                (SELECT count(*) FROM condition)                                               AS total_conditions,
                (SELECT count(*) FROM careplan)                                                AS total_careplans,
                (SELECT count(*) FROM procedure)                                               AS total_procedures,
                (SELECT ROUND(CAST(COUNT(*) AS NUMERIC)
                              / NULLIF((SELECT COUNT(*) FROM patient), 0), 2)
                 FROM encounter)                                                               AS avg_encounters_per_patient,
                (SELECT ROUND(AVG(age)::numeric, 1) FROM patient)                              AS avg_patient_age,
                (SELECT COUNT(*) FROM careplan
                 WHERE end_date IS NULL OR end_date > CURRENT_DATE)                            AS active_careplans
        """)).first()

        max_encounter_date = self.db.query(func.max(EncounterModel.start_date)).scalar()
        max_condition_date = self.db.query(func.max(ConditionModel.start_date)).scalar()

        new_patients_last_30_days = 0
        if max_encounter_date is not None:
            cutoff = max_encounter_date - timedelta(days=30)
            new_patients_last_30_days = self.db.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT patient_id, MIN(start_date) AS first_seen
                    FROM encounter
                    GROUP BY patient_id
                ) t
                WHERE first_seen >= :cutoff
            """), {"cutoff": cutoff}).scalar() or 0

        kpis = KpiCards(
            total_patients=kpi_row.total_patients or 0,
            active_patients=kpi_row.active_patients or 0,
            total_providers=kpi_row.total_providers or 0,
            total_organizations=kpi_row.total_organizations or 0,
            total_encounters=kpi_row.total_encounters or 0,
            total_conditions=kpi_row.total_conditions or 0,
            total_careplans=kpi_row.total_careplans or 0,
            total_procedures=kpi_row.total_procedures or 0,
            avg_encounters_per_patient=float(kpi_row.avg_encounters_per_patient or 0),
            active_careplans=kpi_row.active_careplans or 0,
            new_patients_last_30_days=new_patients_last_30_days,
            avg_patient_age=float(kpi_row.avg_patient_age or 0),
        )

        last_week_encounter_by_class: list[EncounterClassItem] = []
        if max_encounter_date is not None:
            week_cutoff = max_encounter_date - timedelta(days=7)
            encounter_rows = (
                self.db.query(
                    EncounterModel.encounter_class,
                    func.count(EncounterModel.encounter_id).label("count"),
                )
                .filter(EncounterModel.start_date >= week_cutoff)
                .group_by(EncounterModel.encounter_class)
                .order_by(func.count(EncounterModel.encounter_id).desc())
                .all()
            )
            last_week_encounter_by_class = [
                EncounterClassItem(encounter_class=r.encounter_class, count=r.count)
                for r in encounter_rows
            ]

        top_conditions_last_week: list[TopConditionItem] = []
        if max_condition_date is not None:
            cond_cutoff = max_condition_date - timedelta(days=7)
            condition_rows = (
                self.db.query(
                    ConditionModel.description,
                    func.count(ConditionModel.id).label("count"),
                )
                .filter(ConditionModel.start_date >= cond_cutoff)
                .group_by(ConditionModel.description)
                .order_by(func.count(ConditionModel.id).desc())
                .limit(5)
                .all()
            )
            top_conditions_last_week = [
                TopConditionItem(description=r.description, count=r.count)
                for r in condition_rows
            ]

        cluster_rows = (
            self.db.query(
                ClusterModel.title,
                ClusterModel.color,
                func.count(ClusterPatientModel.id).label("count"),
            )
            .outerjoin(
                ClusterPatientModel,
                ClusterPatientModel.cluster_label == ClusterModel.cluster_label,
            )
            .group_by(ClusterModel.id, ClusterModel.title, ClusterModel.color)
            .order_by(func.count(ClusterPatientModel.id).desc())
            .all()
        )
        cluster_distribution = [
            ClusterDistributionItem(title=r.title, count=r.count or 0, color=r.color)
            for r in cluster_rows
        ]

        gender_rows = (
            self.db.query(
                PatientModel.gender,
                func.count(PatientModel.patient_id).label("count"),
            )
            .filter(PatientModel.gender.isnot(None))
            .group_by(PatientModel.gender)
            .all()
        )
        gender_distribution = [
            GenderDistributionItem(gender=r.gender, count=r.count)
            for r in gender_rows
        ]

        age_group_rows = (
            self.db.query(
                AGE_GROUP_CASE.label("age_group"),
                func.count(PatientModel.patient_id).label("count"),
            )
            .group_by(AGE_GROUP_CASE)
            .all()
        )
        age_group_map = {r.age_group: r.count for r in age_group_rows}
        age_groups = [
            AgeGroupItem(age_group=g, count=age_group_map.get(g, 0))
            for g in AGE_GROUP_ORDER
        ]

        last_month_encounters: list[DailyEncounterItem] = []
        if max_encounter_date is not None:
            month_cutoff = max_encounter_date - timedelta(days=30)
            daily_rows = (
                self.db.query(
                    func.to_char(cast(EncounterModel.start_date, Date), "YYYY-MM-DD").label("day"),
                    func.count(EncounterModel.encounter_id).label("count"),
                )
                .filter(EncounterModel.start_date >= month_cutoff)
                .group_by(cast(EncounterModel.start_date, Date))
                .order_by(cast(EncounterModel.start_date, Date).asc())
                .all()
            )
            last_month_encounters = [
                DailyEncounterItem(day=r.day, count=r.count)
                for r in daily_rows
            ]

        recent_rows = (
            self.db.query(
                EncounterModel.encounter_id,
                EncounterModel.patient_id,
                patient_name_col(),
                provider_name_col(),
                OrganizationModel.name.label("organization_name"),
                EncounterModel.start_date,
                EncounterModel.encounter_class,
                EncounterModel.description,
            )
            .outerjoin(PatientModel, EncounterModel.patient_id == PatientModel.patient_id)
            .outerjoin(ProviderModel, EncounterModel.provider_id == ProviderModel.provider_id)
            .outerjoin(OrganizationModel, EncounterModel.organization_id == OrganizationModel.organization_id)
            .order_by(EncounterModel.start_date.desc())
            .limit(10)
            .all()
        )
        recent_encounters = [RecentEncounterItem(**r._asdict()) for r in recent_rows]

        return DashboardResponse(
            kpis=kpis,
            last_week_encounter_by_class=last_week_encounter_by_class,
            top_conditions_last_week=top_conditions_last_week,
            cluster_distribution=cluster_distribution,
            gender_distribution=gender_distribution,
            age_groups=age_groups,
            last_month_encounters=last_month_encounters,
            recent_encounters=recent_encounters,
        )
