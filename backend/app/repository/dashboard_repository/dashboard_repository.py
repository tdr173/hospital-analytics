from sqlalchemy.orm import Session
from sqlalchemy import func, case, text, Date, cast, and_

from domain import (
    PatientModel, ProviderModel, OrganizationModel, EncounterModel,
    ConditionModel, ClusterModel, ClusterPatientModel,
    KpiCards, EncounterClassItem, GenderDistributionItem, AgeGroupItem,
    DailyEncounterItem, RecentEncounterItem, DashboardResponse,
    TopConditionItem, ClusterDistributionItem,
)
from repository._helpers import patient_name_col, provider_name_col
from repository.statistics_repository._common import compute_min_date

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

    def get_dashboard(
        self, range_str: str = "month", provider_id: str | None = None
    ) -> DashboardResponse:
        # Range-based cutoffs (None == "all time", no filter)
        encounter_cutoff = compute_min_date(self.db, EncounterModel.start_date, range_str)
        condition_cutoff = compute_min_date(self.db, ConditionModel.start_date, range_str)

        # Every count/aggregate is scoped to the selected period (and provider, if
        # doctor). The filters are spliced into the SQL only when they apply rather
        # than using `:param IS NULL OR col = :param` guards: those guards stop
        # Postgres from using the start_date / provider_id indexes and from turning
        # `encounter_id IN (...)` into a hash semi-join, which forced sequential
        # scans over encounter/condition/procedure and made this query take ~10s+.
        kpi_params: dict = {}
        if encounter_cutoff is not None:
            kpi_params["enc_cutoff"] = encounter_cutoff
        if provider_id is not None:
            kpi_params["pid"] = provider_id

        # WHERE for subqueries directly over `encounter e`.
        def enc_where() -> str:
            parts = []
            if encounter_cutoff is not None:
                parts.append("e.start_date >= :enc_cutoff")
            if provider_id is not None:
                parts.append("e.provider_id = :pid")
            return ("WHERE " + " AND ".join(parts)) if parts else ""

        # WHERE for child tables (condition/careplan/procedure), scoped to the
        # doctor via their encounter_id and to the period via their own start_date.
        def child_where(alias: str, extra: list[str] | None = None) -> str:
            parts = list(extra or [])
            if encounter_cutoff is not None:
                parts.append(f"{alias}.start_date >= :enc_cutoff")
            if provider_id is not None:
                parts.append(
                    f"{alias}.encounter_id IN "
                    "(SELECT encounter_id FROM encounter WHERE provider_id = :pid)"
                )
            return ("WHERE " + " AND ".join(parts)) if parts else ""

        if encounter_cutoff is None:
            total_patients_sql = "SELECT count(*) FROM patient"
            active_patients_sql = "SELECT count(*) FROM patient WHERE deathdate IS NULL"
            total_providers_sql = "SELECT count(*) FROM provider"
            total_orgs_sql = "SELECT count(*) FROM organization"
            avg_age_sql = "SELECT ROUND(AVG(age)::numeric, 1) FROM patient"
        else:
            total_patients_sql = f"SELECT count(DISTINCT e.patient_id) FROM encounter e {enc_where()}"
            ap_parts = ["p.deathdate IS NULL", "e.start_date >= :enc_cutoff"]
            if provider_id is not None:
                ap_parts.append("e.provider_id = :pid")
            active_patients_sql = (
                "SELECT count(DISTINCT e.patient_id) FROM encounter e "
                "JOIN patient p ON p.patient_id = e.patient_id WHERE "
                + " AND ".join(ap_parts)
            )
            total_providers_sql = f"SELECT count(DISTINCT e.provider_id) FROM encounter e {enc_where()}"
            total_orgs_sql = f"SELECT count(DISTINCT e.organization_id) FROM encounter e {enc_where()}"
            avg_age_sql = (
                "SELECT ROUND(AVG(p.age)::numeric, 1) FROM patient p WHERE p.patient_id IN "
                f"(SELECT DISTINCT e.patient_id FROM encounter e {enc_where()})"
            )

        kpi_sql = f"""
            SELECT
                ({total_patients_sql})                                  AS total_patients,
                ({active_patients_sql})                                 AS active_patients,
                ({total_providers_sql})                                 AS total_providers,
                ({total_orgs_sql})                                      AS total_organizations,
                (SELECT count(*) FROM encounter e {enc_where()})        AS total_encounters,
                (SELECT count(*) FROM condition c {child_where('c')})   AS total_conditions,
                (SELECT count(*) FROM careplan cp {child_where('cp')})  AS total_careplans,
                (SELECT count(*) FROM procedure pr {child_where('pr')}) AS total_procedures,
                (SELECT count(*) FROM careplan cp
                 {child_where('cp', ['(cp.end_date IS NULL OR cp.end_date > CURRENT_DATE)'])}) AS active_careplans,
                ({avg_age_sql})                                         AS avg_patient_age
        """
        kpi_row = self.db.execute(text(kpi_sql), kpi_params).first()

        # Provider's encounter ids (used to scope conditions to the doctor)
        provider_enc_ids = None
        if provider_id:
            provider_enc_ids = (
                self.db.query(EncounterModel.encounter_id)
                .filter(EncounterModel.provider_id == provider_id)
                .subquery()
            )

        # New patients in the selected period (first ever seen within the window)
        np_params = {"cutoff": encounter_cutoff}
        provider_clause = ""
        if provider_id:
            provider_clause = "WHERE provider_id = :pid"
            np_params["pid"] = provider_id
        new_patients_in_period = self.db.execute(text(f"""
            SELECT COUNT(*) FROM (
                SELECT patient_id, MIN(start_date) AS first_seen
                FROM encounter
                {provider_clause}
                GROUP BY patient_id
            ) t
            WHERE (:cutoff IS NULL OR first_seen >= :cutoff)
        """), np_params).scalar() or 0

        total_encounters = kpi_row.total_encounters or 0
        total_patients = kpi_row.total_patients or 0
        avg_encounters_per_patient = (
            round(total_encounters / total_patients, 2) if total_patients else 0.0
        )

        kpis = KpiCards(
            total_patients=total_patients,
            active_patients=kpi_row.active_patients or 0,
            total_providers=kpi_row.total_providers or 0,
            total_organizations=kpi_row.total_organizations or 0,
            total_encounters=total_encounters,
            total_conditions=kpi_row.total_conditions or 0,
            total_careplans=kpi_row.total_careplans or 0,
            total_procedures=kpi_row.total_procedures or 0,
            avg_encounters_per_patient=avg_encounters_per_patient,
            active_careplans=kpi_row.active_careplans or 0,
            new_patients_in_period=new_patients_in_period,
            avg_patient_age=float(kpi_row.avg_patient_age or 0),
        )

        # Patients active in the period (used to scope demographics & clusters)
        active_patient_subq = None
        if encounter_cutoff is not None:
            apq = self.db.query(EncounterModel.patient_id).filter(
                EncounterModel.start_date >= encounter_cutoff
            )
            if provider_id:
                apq = apq.filter(EncounterModel.provider_id == provider_id)
            active_patient_subq = apq.distinct().subquery()

        class_query = self.db.query(
            EncounterModel.encounter_class,
            func.count(EncounterModel.encounter_id).label("count"),
        )
        if encounter_cutoff is not None:
            class_query = class_query.filter(EncounterModel.start_date >= encounter_cutoff)
        if provider_id:
            class_query = class_query.filter(EncounterModel.provider_id == provider_id)
        encounter_rows = (
            class_query
            .group_by(EncounterModel.encounter_class)
            .order_by(func.count(EncounterModel.encounter_id).desc())
            .all()
        )
        encounter_by_class = [
            EncounterClassItem(encounter_class=r.encounter_class, count=r.count)
            for r in encounter_rows
        ]

        cond_query = self.db.query(
            ConditionModel.description,
            func.count(ConditionModel.id).label("count"),
        )
        if condition_cutoff is not None:
            cond_query = cond_query.filter(ConditionModel.start_date >= condition_cutoff)
        if provider_enc_ids is not None:
            cond_query = cond_query.filter(
                ConditionModel.encounter_id.in_(self.db.query(provider_enc_ids.c.encounter_id))
            )
        condition_rows = (
            cond_query
            .group_by(ConditionModel.description)
            .order_by(func.count(ConditionModel.id).desc())
            .limit(10)
            .all()
        )
        top_conditions = [
            TopConditionItem(description=r.description, count=r.count)
            for r in condition_rows
        ]

        cluster_join = ClusterPatientModel.cluster_label == ClusterModel.cluster_label
        if active_patient_subq is not None:
            cluster_join = and_(
                cluster_join,
                ClusterPatientModel.patient_id.in_(
                    self.db.query(active_patient_subq.c.patient_id)
                ),
            )
        cluster_rows = (
            self.db.query(
                ClusterModel.title,
                ClusterModel.color,
                func.count(ClusterPatientModel.id).label("count"),
            )
            .outerjoin(ClusterPatientModel, cluster_join)
            .group_by(ClusterModel.id, ClusterModel.title, ClusterModel.color)
            .order_by(func.count(ClusterPatientModel.id).desc())
            .all()
        )
        cluster_distribution = [
            ClusterDistributionItem(title=r.title, count=r.count or 0, color=r.color)
            for r in cluster_rows
        ]

        gender_query = self.db.query(
            PatientModel.gender,
            func.count(PatientModel.patient_id).label("count"),
        ).filter(PatientModel.gender.isnot(None))
        if active_patient_subq is not None:
            gender_query = gender_query.filter(
                PatientModel.patient_id.in_(self.db.query(active_patient_subq.c.patient_id))
            )
        gender_rows = gender_query.group_by(PatientModel.gender).all()
        gender_distribution = [
            GenderDistributionItem(gender=r.gender, count=r.count)
            for r in gender_rows
        ]

        age_query = self.db.query(
            AGE_GROUP_CASE.label("age_group"),
            func.count(PatientModel.patient_id).label("count"),
        )
        if active_patient_subq is not None:
            age_query = age_query.filter(
                PatientModel.patient_id.in_(self.db.query(active_patient_subq.c.patient_id))
            )
        age_group_rows = age_query.group_by(AGE_GROUP_CASE).all()
        age_group_map = {r.age_group: r.count for r in age_group_rows}
        age_groups = [
            AgeGroupItem(age_group=g, count=age_group_map.get(g, 0))
            for g in AGE_GROUP_ORDER
        ]

        # Visit volume: managers always see the full year (monthly); doctors follow the range.
        timeline_range = "year" if provider_id is None else range_str
        timeline_cutoff = compute_min_date(self.db, EncounterModel.start_date, timeline_range)
        encounters_timeline: list[DailyEncounterItem] = []
        if timeline_cutoff is not None:
            if timeline_range == "year":
                period_expr = func.date_trunc("month", cast(EncounterModel.start_date, Date))
            else:
                period_expr = cast(EncounterModel.start_date, Date)
            timeline_query = (
                self.db.query(
                    func.to_char(period_expr, "YYYY-MM-DD").label("day"),
                    func.count(EncounterModel.encounter_id).label("count"),
                )
                .filter(EncounterModel.start_date >= timeline_cutoff)
            )
            if provider_id:
                timeline_query = timeline_query.filter(EncounterModel.provider_id == provider_id)
            daily_rows = (
                timeline_query
                .group_by(period_expr)
                .order_by(period_expr.asc())
                .all()
            )
            encounters_timeline = [
                DailyEncounterItem(day=r.day, count=r.count)
                for r in daily_rows
            ]

        recent_query = (
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
        )
        if provider_id:
            recent_query = recent_query.filter(EncounterModel.provider_id == provider_id)
        recent_rows = (
            recent_query
            .order_by(EncounterModel.start_date.desc())
            .limit(10)
            .all()
        )
        recent_encounters = [RecentEncounterItem(**r._asdict()) for r in recent_rows]

        return DashboardResponse(
            kpis=kpis,
            encounter_by_class=encounter_by_class,
            top_conditions=top_conditions,
            cluster_distribution=cluster_distribution,
            gender_distribution=gender_distribution,
            age_groups=age_groups,
            encounters_timeline=encounters_timeline,
            recent_encounters=recent_encounters,
        )
