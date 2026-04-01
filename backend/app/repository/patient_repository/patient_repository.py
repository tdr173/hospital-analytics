from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from domain import (
    PatientListItem, PatientListResponse, PatientDetailResponse,
    PatientSummaryResponse, ConditionItem, MedicationItem,
    ProcedureItem, ImmunizationItem, AllergyItem, EncounterItem,
    FilterOption, PatientResourcesResponse,
)

SORT_COL_MAP = {
    "last_name": "p.last_name",
    "first_name": "p.first_name",
    "age": "p.age",
    "city": "p.city",
    "gender": "p.gender",
    "race": "p.race",
    "marital": "p.marital",
}

AGE_GROUP_RANGES = {
    "child":        (0,  17),
    "young_adult":  (18, 34),
    "middle_aged":  (35, 54),
    "senior":       (55, 69),
    "elderly":      (70, 999),
}


class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def _latest_run_id(self) -> Optional[int]:
        return self.db.execute(text("SELECT MAX(id) FROM cluster_run")).scalar()

    # ------------------------------------------------------------------
    # GET /patients
    # ------------------------------------------------------------------
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
        sort_col = SORT_COL_MAP.get(sort_by, "p.last_name")
        sort_dir = "ASC" if sort_type.lower() == "asc" else "DESC"

        conditions: list[str] = []
        params: dict = {}

        if search:
            conditions.append(
                "(p.first_name ILIKE :search OR p.last_name ILIKE :search OR p.city ILIKE :search)"
            )
            params["search"] = f"%{search}%"

        if gender:
            genders = [g.strip() for g in gender.split(",") if g.strip()]
            if genders:
                placeholders = ", ".join(f":gender_{i}" for i in range(len(genders)))
                conditions.append(f"p.gender IN ({placeholders})")
                for i, g in enumerate(genders):
                    params[f"gender_{i}"] = g

        if age_group:
            groups = [g.strip() for g in age_group.split(",") if g.strip() and g.strip() in AGE_GROUP_RANGES]
            if groups:
                age_parts = []
                for i, g in enumerate(groups):
                    lo, hi = AGE_GROUP_RANGES[g]
                    age_parts.append(f"(p.age BETWEEN :age_lo_{i} AND :age_hi_{i})")
                    params[f"age_lo_{i}"] = lo
                    params[f"age_hi_{i}"] = hi
                conditions.append(f"({' OR '.join(age_parts)})")

        if status:
            statuses = {s.strip() for s in status.split(",") if s.strip()}
            has_alive = "alive" in statuses
            has_deceased = "deceased" in statuses
            if has_alive and not has_deceased:
                conditions.append("p.deathdate IS NULL")
            elif has_deceased and not has_alive:
                conditions.append("p.deathdate IS NOT NULL")

        if race:
            races = [r.strip() for r in race.split(",") if r.strip()]
            if races:
                placeholders = ", ".join(f":race_{i}" for i in range(len(races)))
                conditions.append(f"p.race IN ({placeholders})")
                for i, r in enumerate(races):
                    params[f"race_{i}"] = r

        if marital:
            maritals = [m.strip() for m in marital.split(",") if m.strip()]
            if maritals:
                placeholders = ", ".join(f":marital_{i}" for i in range(len(maritals)))
                conditions.append(f"p.marital IN ({placeholders})")
                for i, m in enumerate(maritals):
                    params[f"marital_{i}"] = m

        if city:
            conditions.append("p.city ILIKE :city")
            params["city"] = f"%{city}%"

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        # Cluster join (safe even when no run exists — LEFT JOIN returns NULLs)
        latest_run_id = self._latest_run_id()
        if latest_run_id:
            cluster_select = ", cp.cluster_label, c.title AS cluster_title, c.color AS cluster_color"
            cluster_join = (
                "LEFT JOIN cluster_patient cp ON cp.patient_id = p.patient_id AND cp.run_id = :run_id "
                "LEFT JOIN cluster c ON c.run_id = :run_id AND c.cluster_label = cp.cluster_label"
            )
            params["run_id"] = latest_run_id
        else:
            cluster_select = ", NULL::int AS cluster_label, NULL::varchar AS cluster_title, NULL::varchar AS cluster_color"
            cluster_join = ""

        # Total count
        total = self.db.execute(
            text(f"SELECT COUNT(*) FROM patient p {where}"), params
        ).scalar() or 0

        # Paginated data
        offset = (page - 1) * rows
        data_sql = f"""
            SELECT
                p.patient_id, p.first_name, p.last_name, p.age, p.gender,
                p.city, p.race, p.ethnicity, p.marital, p.birthdate, p.deathdate
                {cluster_select}
            FROM patient p
            {cluster_join}
            {where}
            ORDER BY {sort_col} {sort_dir} NULLS LAST
            LIMIT :limit OFFSET :offset
        """
        params["limit"] = rows
        params["offset"] = offset

        rows_data = self.db.execute(text(data_sql), params).mappings().all()
        items = [PatientListItem(**dict(row)) for row in rows_data]
        return PatientListResponse(items=items, total=total)

    # ------------------------------------------------------------------
    # GET /patients/{id}
    # ------------------------------------------------------------------
    def get_patient(self, patient_id: str) -> PatientDetailResponse:
        latest_run_id = self._latest_run_id()

        if latest_run_id:
            cluster_select = ", cp.cluster_label, c.title AS cluster_title, c.color AS cluster_color"
            cluster_join = (
                "LEFT JOIN cluster_patient cp ON cp.patient_id = p.patient_id AND cp.run_id = :run_id "
                "LEFT JOIN cluster c ON c.run_id = :run_id AND c.cluster_label = cp.cluster_label"
            )
            params = {"pid": patient_id, "run_id": latest_run_id}
        else:
            cluster_select = ", NULL::int AS cluster_label, NULL::varchar AS cluster_title, NULL::varchar AS cluster_color"
            cluster_join = ""
            params = {"pid": patient_id}

        row = self.db.execute(text(f"""
            SELECT
                p.patient_id, p.first_name, p.last_name, p.age, p.gender,
                p.city, p.race, p.ethnicity, p.marital, p.birthdate, p.deathdate,
                p.latitude, p.longitude
                {cluster_select}
            FROM patient p
            {cluster_join}
            WHERE p.patient_id = :pid
        """), params).mappings().first()

        if not row:
            raise ValueError(f"Patient {patient_id} not found")

        return PatientDetailResponse(**dict(row))

    # ------------------------------------------------------------------
    # GET /patients/{id}/summary
    # ------------------------------------------------------------------
    def get_patient_summary(self, patient_id: str) -> PatientSummaryResponse:
        latest_run_id = self._latest_run_id()

        # Try pre-computed features from clustering
        if latest_run_id:
            feat_row = self.db.execute(text("""
                SELECT features FROM cluster_patient
                WHERE patient_id = :pid AND run_id = :rid
            """), {"pid": patient_id, "rid": latest_run_id}).mappings().first()

            if feat_row and feat_row["features"]:
                f = feat_row["features"]
                return PatientSummaryResponse(
                    qaly=round(float(f["qaly"]), 2) if f.get("qaly") is not None else None,
                    avg_bmi=round(float(f["avg_bmi"]), 1) if f.get("avg_bmi") is not None else None,
                    active_conditions=int(f.get("active_conditions_count") or 0),
                    total_medications=int(f.get("total_medications") or 0),
                    total_procedures=int(f.get("total_procedures") or 0),
                    emergency_visits=int(f.get("emergency_count") or 0),
                    days_since_last_encounter=int(f.get("days_since_last_encounter") or 0),
                )

        # Fallback: compute directly from tables
        row = self.db.execute(text("""
            SELECT
                (SELECT value_numeric FROM observation
                 WHERE patient_id = :pid AND description = 'QALY'
                 ORDER BY date DESC LIMIT 1) AS qaly,

                (SELECT ROUND(AVG(value_numeric)::numeric, 1) FROM (
                    SELECT value_numeric FROM observation
                    WHERE patient_id = :pid AND description = 'Body Mass Index'
                      AND value_numeric IS NOT NULL
                    ORDER BY date DESC LIMIT 5
                ) bmi_sub) AS avg_bmi,

                (SELECT COUNT(*) FROM condition
                 WHERE patient_id = :pid AND end_date IS NULL) AS active_conditions,

                (SELECT COUNT(*) FROM medication
                 WHERE patient_id = :pid) AS total_medications,

                (SELECT COUNT(*) FROM "procedure"
                 WHERE patient_id = :pid) AS total_procedures,

                (SELECT COUNT(*) FROM encounter
                 WHERE patient_id = :pid AND encounter_class = 'emergency') AS emergency_visits,

                (SELECT EXTRACT(DAY FROM NOW() - MAX(start_date))::int FROM encounter
                 WHERE patient_id = :pid) AS days_since_last_encounter
        """), {"pid": patient_id}).mappings().first()

        return PatientSummaryResponse(
            qaly=round(float(row["qaly"]), 2) if row["qaly"] is not None else None,
            avg_bmi=round(float(row["avg_bmi"]), 1) if row["avg_bmi"] is not None else None,
            active_conditions=int(row["active_conditions"] or 0),
            total_medications=int(row["total_medications"] or 0),
            total_procedures=int(row["total_procedures"] or 0),
            emergency_visits=int(row["emergency_visits"] or 0),
            days_since_last_encounter=int(row["days_since_last_encounter"] or 0) if row["days_since_last_encounter"] is not None else None,
        )

    # ------------------------------------------------------------------
    # GET /patients/{id}/conditions
    # ------------------------------------------------------------------
    def get_patient_conditions(self, patient_id: str) -> list[ConditionItem]:
        rows = self.db.execute(text("""
            SELECT id, description, condition_code::varchar, start_date, end_date
            FROM condition
            WHERE patient_id = :pid
            ORDER BY start_date DESC
        """), {"pid": patient_id}).mappings().all()
        return [ConditionItem(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # GET /patients/{id}/medications
    # ------------------------------------------------------------------
    def get_patient_medications(self, patient_id: str) -> list[MedicationItem]:
        rows = self.db.execute(text("""
            SELECT id, description, medication_code::varchar, start_date, end_date,
                   duration_days, reason_description
            FROM medication
            WHERE patient_id = :pid
            ORDER BY start_date DESC
        """), {"pid": patient_id}).mappings().all()
        return [MedicationItem(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # GET /patients/{id}/procedures
    # ------------------------------------------------------------------
    def get_patient_procedures(self, patient_id: str) -> list[ProcedureItem]:
        rows = self.db.execute(text("""
            SELECT id, description, procedure_code::varchar, date, reason_description
            FROM "procedure"
            WHERE patient_id = :pid
            ORDER BY date DESC
        """), {"pid": patient_id}).mappings().all()
        return [ProcedureItem(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # GET /patients/{id}/immunizations
    # ------------------------------------------------------------------
    def get_patient_immunizations(self, patient_id: str) -> list[ImmunizationItem]:
        rows = self.db.execute(text("""
            SELECT id, description, immunization_code::varchar, date
            FROM immunization
            WHERE patient_id = :pid
            ORDER BY date DESC
        """), {"pid": patient_id}).mappings().all()
        return [ImmunizationItem(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # GET /patients/{id}/allergies
    # ------------------------------------------------------------------
    def get_patient_allergies(self, patient_id: str) -> list[AllergyItem]:
        rows = self.db.execute(text("""
            SELECT id, description, allergy_code::varchar, start_date, end_date
            FROM allergy
            WHERE patient_id = :pid
            ORDER BY start_date DESC
        """), {"pid": patient_id}).mappings().all()
        return [AllergyItem(**dict(r)) for r in rows]

    # ------------------------------------------------------------------
    # GET /patients/resources
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # GET /patients/{id}/encounters
    # ------------------------------------------------------------------
    def get_patient_encounters(self, patient_id: str) -> list[EncounterItem]:
        rows = self.db.execute(text("""
            SELECT
                e.encounter_id, e.start_date, e.end_date, e.duration,
                e.encounter_class, e.description, e.reason_description,
                pr.first_name || ' ' || pr.last_name AS provider_name,
                o.name AS organization_name
            FROM encounter e
            LEFT JOIN provider pr ON e.provider_id = pr.provider_id
            LEFT JOIN organization o ON e.organization_id = o.organization_id
            WHERE e.patient_id = :pid
            ORDER BY e.start_date DESC
        """), {"pid": patient_id}).mappings().all()
        return [EncounterItem(**dict(r)) for r in rows]
