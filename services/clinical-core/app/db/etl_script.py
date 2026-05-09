import re
import pandas as pd
from pathlib import Path

from db import engine as db_engine

dataset_path = Path(__file__).parent.parent.parent.parent.parent / "synthea" / "output" / "csv"
print(dataset_path)


def _strip_digits(s: str) -> str:
    if not isinstance(s, str):
        return s
    return re.sub(r"\d+", "", s).strip()


def load_patients(engine):
    df = pd.read_csv(dataset_path / "patients.csv")

    keep_cols = {
        "Id": "patient_id",
        "BIRTHDATE": "birthdate",
        "DEATHDATE": "deathdate",
        "FIRST": "first_name",
        "LAST": "last_name",
        "MARITAL": "marital",
        "GENDER": "gender",
        "RACE": "race",
        "ETHNICITY": "ethnicity",
        "CITY": "city",
    }

    patients_df = df[list(keep_cols.keys())].rename(columns=keep_cols)
    patients_df["first_name"] = patients_df["first_name"].apply(_strip_digits)
    patients_df["last_name"] = patients_df["last_name"].apply(_strip_digits)
    patients_df["marital"] = patients_df["marital"].fillna("S")

    ref_date = pd.Timestamp.now()
    patients_df["birthdate"] = pd.to_datetime(patients_df["birthdate"])
    patients_df["deathdate"] = pd.to_datetime(patients_df["deathdate"])
    patients_df["age"] = (patients_df["deathdate"].fillna(ref_date) - patients_df["birthdate"]).dt.days // 365

    categorical_cols = ["gender", "race", "ethnicity"]
    for col in categorical_cols:
        if patients_df[col].isnull().any():
            patients_df[col] = patients_df[col].fillna(patients_df[col].mode()[0])

    patients_df.to_sql(name="patient", con=engine, if_exists="append", index=False)
    print(f"Loaded {len(patients_df)} patients.")


def _pick_single_org() -> dict:
    df = pd.read_csv(dataset_path / "organizations.csv")
    row = df.loc[df["UTILIZATION"].idxmax()]
    return {
        "organization_id": row["Id"],
        "name": row["NAME"],
        "city": row["CITY"],
        "latitude": row["LAT"],
        "longitude": row["LON"],
        "phone": str(row["PHONE"]),
        "utilization": int(row["UTILIZATION"]),
    }


def _pick_top_provider_ids(max_providers: int = 300) -> list[str]:
    enc_df = pd.read_csv(dataset_path / "encounters.csv", usecols=["PROVIDER"])
    counts = enc_df["PROVIDER"].value_counts()
    return counts.head(max_providers).index.tolist()


def load_organizations(engine):
    org = _pick_single_org()
    orgs_df = pd.DataFrame([org])
    orgs_df = orgs_df.drop(columns=[c for c in ["latitude", "longitude"] if c in orgs_df.columns])
    orgs_df.to_sql(name="organization", con=engine, if_exists="append", index=False)
    print(f"Loaded 1 organization: {org['name']} (utilization={org['utilization']}).")


def load_providers(engine):
    df = pd.read_csv(dataset_path / "providers.csv")

    # Synthea older exports have ENCOUNTERS/PROCEDURES; newer exports have UTILIZATION only
    if "ENCOUNTERS" in df.columns:
        activity_cols = {"ENCOUNTERS": "encounters", "PROCEDURES": "procedures"}
    else:
        activity_cols = {"UTILIZATION": "encounters"}

    keep_cols = {
        "Id": "provider_id",
        "ORGANIZATION": "organization_id",
        "NAME": "name",
        "GENDER": "gender",
        "SPECIALITY": "speciality",
        "CITY": "city",
        **activity_cols,
    }

    providers_df = df[list(keep_cols.keys())].rename(columns=keep_cols)
    if "procedures" not in providers_df.columns:
        providers_df["procedures"] = 0

    kept_ids = set(_pick_top_provider_ids())
    providers_df = providers_df[providers_df["provider_id"].isin(kept_ids)].copy()
    providers_df["organization_id"] = _pick_single_org()["organization_id"]

    name_parts = providers_df["name"].str.rsplit(" ", n=1)
    providers_df["first_name"] = name_parts.str[0].apply(_strip_digits)
    providers_df["last_name"] = name_parts.str[1].apply(_strip_digits)
    providers_df = providers_df.drop(columns=["name"])

    for col in ["gender", "speciality"]:
        if providers_df[col].isnull().any():
            providers_df[col] = providers_df[col].fillna(providers_df[col].mode()[0])

    for col in ["encounters", "procedures"]:
        if providers_df[col].isnull().any():
            providers_df[col] = providers_df[col].fillna(providers_df[col].median())

    providers_df.to_sql(name="provider", con=engine, if_exists="append", index=False)
    print(f"Loaded {len(providers_df)} providers.")


def load_encounters(engine):
    df = pd.read_csv(dataset_path / "encounters.csv")

    kept_ids = set(_pick_top_provider_ids())
    single_org_id = _pick_single_org()["organization_id"]

    enc_year = pd.to_datetime(df["START"], utc=True).dt.year
    kept_mask = df["PROVIDER"].isin(kept_ids)
    year_provider_counts = (
        df[kept_mask]
        .assign(year=enc_year[kept_mask])
        .groupby(["year", "PROVIDER"])
        .size()
        .reset_index(name="cnt")
        .sort_values(["year", "cnt"], ascending=[True, False])
    )
    year_to_providers: dict[int, list[str]] = {
        yr: grp["PROVIDER"].tolist()
        for yr, grp in year_provider_counts.groupby("year")
    }
    global_fallback = year_provider_counts.groupby("PROVIDER")["cnt"].sum().idxmax()

    keep_cols = {
        "Id": "encounter_id",
        "PATIENT": "patient_id",
        "ORGANIZATION": "organization_id",
        "PROVIDER": "provider_id",
        "START": "start_date",
        "STOP": "end_date",
        "ENCOUNTERCLASS": "encounter_class",
        "DESCRIPTION": "description",
        "REASONDESCRIPTION": "reason_description",
    }

    encounters_df = df[list(keep_cols.keys())].rename(columns=keep_cols)
    encounters_df["organization_id"] = single_org_id

    dropped_mask = ~encounters_df["provider_id"].isin(kept_ids)
    if dropped_mask.any():
        years = pd.to_datetime(encounters_df.loc[dropped_mask, "start_date"], utc=True).dt.year
        year_counters: dict[int, int] = {}
        new_providers = []
        for y in years:
            providers = year_to_providers.get(y, [global_fallback])
            idx = year_counters.get(y, 0)
            year_counters[y] = idx + 1
            new_providers.append(providers[idx % len(providers)])
        encounters_df.loc[dropped_mask, "provider_id"] = new_providers
        print(f"Redistributed {dropped_mask.sum():,} encounters from dropped providers.")

    today = pd.Timestamp.now(tz="UTC").normalize()
    encounters_df["start_date"] = pd.to_datetime(encounters_df["start_date"]).clip(upper=today)
    encounters_df["end_date"] = pd.to_datetime(encounters_df["end_date"]).clip(upper=today)
    encounters_df["duration"] = (encounters_df["end_date"] - encounters_df["start_date"]).dt.total_seconds() / 60

    duration_caps = {
        "wellness": 120, "ambulatory": 480, "outpatient": 1440,
        "urgentcare": 1440, "emergency": 4320, "inpatient": 43200,
    }
    for enc_class, max_minutes in duration_caps.items():
        mask = (encounters_df["encounter_class"] == enc_class) & (encounters_df["duration"] > max_minutes)
        encounters_df.loc[mask, "duration"] = max_minutes

    for col in ["encounter_class", "description", "reason_description"]:
        encounters_df[col] = encounters_df[col].fillna("no_reason_specified")
    if encounters_df["duration"].isnull().any():
        encounters_df["duration"] = encounters_df["duration"].fillna(encounters_df["duration"].median())

    encounters_df.to_sql(name="encounter", con=engine, if_exists="append", index=False)
    print(f"Loaded {len(encounters_df)} encounters.")


def load_patient_providers(engine):
    print("Loading patient-provider relationships...")
    enc = pd.read_csv(dataset_path / "encounters.csv", usecols=["PATIENT", "PROVIDER"])
    enc = enc.rename(columns={"PATIENT": "patient_id", "PROVIDER": "provider_id"})
    kept_ids = set(_pick_top_provider_ids())
    pp = enc[enc["provider_id"].isin(kept_ids)].drop_duplicates().dropna()
    pp.to_sql("patient_provider", con=engine, if_exists="append", index=False)
    print(f"  {len(pp)} patient-provider pairs loaded.")


def load_allergies(engine):
    df = pd.read_csv(dataset_path / "allergies.csv")

    keep_cols = {
        "START": "start_date",
        "STOP": "end_date",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "allergy_code",
        "DESCRIPTION": "description",
    }

    allergies_df = df[list(keep_cols.keys())].rename(columns=keep_cols)
    allergies_df["start_date"] = pd.to_datetime(allergies_df["start_date"])
    allergies_df["end_date"] = pd.to_datetime(allergies_df["end_date"])
    if allergies_df["description"].isnull().any():
        allergies_df["description"] = allergies_df["description"].fillna("unknown_allergy")

    allergies_df.to_sql(name="allergy", con=engine, if_exists="append", index=True, index_label="id")
    print(f"Loaded {len(allergies_df)} allergy records.")


def load_procedures(engine):
    df = pd.read_csv(dataset_path / "procedures.csv")

    # Synthea older exports have START/STOP; newer exports have only DATE
    if "START" in df.columns:
        date_cols = {"START": "start_date", "STOP": "end_date"}
    else:
        date_cols = {"DATE": "start_date"}

    keep_cols = {
        **date_cols,
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "procedure_code",
        "DESCRIPTION": "description",
        "REASONDESCRIPTION": "reason_description",
    }

    procedures_df = df[list(keep_cols.keys())].rename(columns=keep_cols)
    procedures_df["start_date"] = pd.to_datetime(procedures_df["start_date"])
    if "end_date" not in procedures_df.columns:
        procedures_df["end_date"] = pd.NaT
    else:
        procedures_df["end_date"] = pd.to_datetime(procedures_df["end_date"])

    for col in ["description", "reason_description"]:
        procedures_df[col] = procedures_df[col].fillna("routine_procedure")

    procedures_df.to_sql(name="procedure", con=engine, if_exists="append", index=True, index_label="id")
    print(f"Loaded {len(procedures_df)} procedures.")


def load_medications(engine):
    df = pd.read_csv(dataset_path / "medications.csv")

    keep_cols = {
        "START": "start_date",
        "STOP": "end_date",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "medication_code",
        "DESCRIPTION": "description",
        "REASONDESCRIPTION": "reason_description",
    }

    medications_df = df[list(keep_cols.keys())].rename(columns=keep_cols)
    medications_df["start_date"] = pd.to_datetime(medications_df["start_date"])
    medications_df["end_date"] = pd.to_datetime(medications_df["end_date"])
    medications_df["duration_days"] = (medications_df["end_date"] - medications_df["start_date"]).dt.days.fillna(0).astype(int)

    for col in ["description", "reason_description"]:
        medications_df[col] = medications_df[col].fillna("no_reason_specified")

    medications_df.to_sql(name="medication", con=engine, if_exists="append", index=True, index_label="id")
    print(f"Loaded {len(medications_df)} medications.")


def load_immunizations(engine):
    df = pd.read_csv(dataset_path / "immunizations.csv")

    keep_cols = {
        "DATE": "date",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "immunization_code",
        "DESCRIPTION": "description",
    }

    immunizations_df = df[list(keep_cols.keys())].rename(columns=keep_cols)
    immunizations_df["date"] = pd.to_datetime(immunizations_df["date"])
    if immunizations_df["description"].isnull().any():
        immunizations_df["description"] = immunizations_df["description"].fillna("unknown_vaccine")

    immunizations_df.to_sql(name="immunization", con=engine, if_exists="append", index=True, index_label="id")
    print(f"Loaded {len(immunizations_df)} immunizations.")


def load_careplans(engine):
    df = pd.read_csv(dataset_path / "careplans.csv")

    keep_cols = {
        "START": "start_date",
        "STOP": "end_date",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "careplan_code",
        "DESCRIPTION": "description",
        "REASONCODE": "reason_code",
        "REASONDESCRIPTION": "reason_description",
    }

    careplans_df = df[list(keep_cols.keys())].rename(columns=keep_cols)
    careplans_df["start_date"] = pd.to_datetime(careplans_df["start_date"])
    careplans_df["end_date"] = pd.to_datetime(careplans_df["end_date"], errors="coerce")
    careplans_df["duration_days"] = (careplans_df["end_date"] - careplans_df["start_date"]).dt.days.fillna(0).astype(int)
    careplans_df["reason_description"] = careplans_df["reason_description"].fillna("no_reason_specified")
    careplans_df["description"] = careplans_df["description"].fillna("unknown_careplan")

    careplans_df.to_sql(name="careplan", con=engine, if_exists="append", index=True, index_label="id")
    print(f"Loaded {len(careplans_df)} careplans.")


def load_conditions(engine):
    df = pd.read_csv(dataset_path / "conditions.csv")

    keep_cols = {
        "START": "start_date",
        "STOP": "end_date",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "condition_code",
        "DESCRIPTION": "description",
    }

    conditions_df = df[list(keep_cols.keys())].rename(columns=keep_cols)
    conditions_df["start_date"] = pd.to_datetime(conditions_df["start_date"])
    conditions_df["end_date"] = pd.to_datetime(conditions_df["end_date"], errors="coerce")
    conditions_df["description"] = conditions_df["description"].fillna("unknown_condition")

    conditions_df.to_sql(name="condition", con=engine, if_exists="append", index=True, index_label="id")
    print(f"Loaded {len(conditions_df)} conditions.")


def load_observations(engine):
    df = pd.read_csv(dataset_path / "observations.csv")

    keep_cols = {
        "DATE": "date",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "observation_code",
        "DESCRIPTION": "description",
        "VALUE": "value",
        "UNITS": "units",
    }

    obs_df = df[list(keep_cols.keys())].rename(columns=keep_cols)
    obs_df["value_numeric"] = pd.to_numeric(obs_df["value"], errors="coerce")

    total = len(obs_df)
    chunk_size = 10_000
    print(f"Observations ETL started: {total:,} rows, chunk size {chunk_size:,}.")
    for i in range(0, total, chunk_size):
        obs_df.iloc[i: i + chunk_size].to_sql(
            name="observation", con=engine, if_exists="append", index=True, index_label="id"
        )
        print(f"  Inserted rows {i:,} – {min(i + chunk_size, total):,} / {total:,}")
    print(f"Loaded {total:,} observations.")


def _refresh_observation_views(engine):
    views = [
        "mv_obs_totals", "mv_obs_per_patient", "mv_obs_top_types",
        "mv_obs_numeric_stats", "mv_obs_categorical_stats",
    ]
    try:
        with engine.connect() as conn:
            for v in views:
                conn.execute(__import__("sqlalchemy").text(f"REFRESH MATERIALIZED VIEW {v}"))
            conn.commit()
        print("Observation materialized views refreshed.")
    except Exception as e:
        print(f"Could not refresh observation views (run app first to create them): {e}")


def _truncate_all_tables(engine):
    tables = [
        "observation", "condition", "careplan", "immunization",
        "medication", "procedure", "allergy", "encounter",
        "patient_provider",
        "patient", "provider", "organization",
    ]
    from sqlalchemy import text
    with engine.connect() as conn:
        existing = {
            row[0] for row in conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            ))
        }
        for table in tables:
            if table in existing:
                conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
        conn.commit()
    print("All tables truncated.")


def run_etl(engine):
    _truncate_all_tables(engine)
    load_patients(engine)
    load_organizations(engine)
    load_providers(engine)
    load_encounters(engine)
    load_patient_providers(engine)
    load_allergies(engine)
    load_procedures(engine)
    load_medications(engine)
    load_immunizations(engine)
    load_careplans(engine)
    load_conditions(engine)
    load_observations(engine)
    _refresh_observation_views(engine)


run_etl(db_engine)
