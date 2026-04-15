from sqlalchemy.orm import Session
from sqlalchemy import func, case, text

from domain import (
    PatientModel, ProviderModel, OrganizationModel, EncounterModel,
    KpiCards, EncounterClassItem, GenderDistributionItem, AgeGroupItem,
    MonthlyEncounterItem, RecentEncounterItem, DashboardResponse,
)

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

    def get_dashboard(self) -> DashboardResponse:
        # KPIs — single round-trip with correlated subqueries
        kpi_row = self.db.execute(text("""
            SELECT
                (SELECT count(*) FROM patient)                            AS total_patients,
                (SELECT count(*) FROM patient WHERE deathdate IS NULL)    AS active_patients,
                (SELECT count(*) FROM provider)                           AS total_providers,
                (SELECT count(*) FROM organization)                       AS total_organizations,
                (SELECT count(*) FROM encounter)                          AS total_encounters
        """)).first()

        kpis = KpiCards(
            total_patients=kpi_row.total_patients or 0,
            active_patients=kpi_row.active_patients or 0,
            total_providers=kpi_row.total_providers or 0,
            total_organizations=kpi_row.total_organizations or 0,
            total_encounters=kpi_row.total_encounters or 0,
        )

        # Encounter by class
        enc_class_rows = (
            self.db.query(
                EncounterModel.encounter_class,
                func.count(EncounterModel.encounter_id).label("count"),
            )
            .group_by(EncounterModel.encounter_class)
            .order_by(func.count(EncounterModel.encounter_id).desc())
            .all()
        )
        encounter_by_class = [
            EncounterClassItem(encounter_class=r.encounter_class, count=r.count)
            for r in enc_class_rows
        ]

        # Gender distribution
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

        # Age groups
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

        # Monthly encounters (last 12 months)
        monthly_rows = (
            self.db.query(
                func.to_char(
                    func.date_trunc("month", EncounterModel.start_date), "YYYY-MM"
                ).label("month"),
                func.count(EncounterModel.encounter_id).label("count"),
            )
            .filter(
                EncounterModel.start_date >= func.date_trunc(
                    "month", func.now() - text("interval '11 months'")
                )
            )
            .group_by(
                func.date_trunc("month", EncounterModel.start_date)
            )
            .order_by(
                func.date_trunc("month", EncounterModel.start_date).asc()
            )
            .all()
        )
        monthly_encounters = [
            MonthlyEncounterItem(month=r.month, count=r.count)
            for r in monthly_rows
        ]

        # Recent encounters (last 10)
        patient_name_col = case(
            (PatientModel.first_name == PatientModel.last_name,
             func.regexp_replace(PatientModel.first_name, '[0-9]', '', 'g')),
            else_=(
                func.regexp_replace(PatientModel.first_name, '[0-9]', '', 'g')
                + ' '
                + func.regexp_replace(PatientModel.last_name, '[0-9]', '', 'g')
            )
        ).label("patient_name")

        provider_name_col = case(
            (ProviderModel.first_name == ProviderModel.last_name,
             func.regexp_replace(ProviderModel.first_name, '[0-9]', '', 'g')),
            else_=(
                func.regexp_replace(ProviderModel.first_name, '[0-9]', '', 'g')
                + ' '
                + func.regexp_replace(ProviderModel.last_name, '[0-9]', '', 'g')
            )
        ).label("provider_name")

        recent_rows = (
            self.db.query(
                EncounterModel.encounter_id,
                EncounterModel.patient_id,
                patient_name_col,
                provider_name_col,
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
            encounter_by_class=encounter_by_class,
            gender_distribution=gender_distribution,
            age_groups=age_groups,
            monthly_encounters=monthly_encounters,
            recent_encounters=recent_encounters,
        )
