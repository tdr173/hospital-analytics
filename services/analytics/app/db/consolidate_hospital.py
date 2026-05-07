"""
Consolidate a Synthea CSV dataset (many orgs, many providers, 100-year span)
into a single-hospital view with a realistic, generationally-rotating pool
of doctors.

Run standalone:
    python consolidate_hospital.py

Inputs  (read-only):  dataset/organizations.csv, providers.csv, encounters.csv
Outputs (overwrite):  dataset/hospital/organizations.csv
                      dataset/hospital/providers.csv
                      dataset/hospital/encounters.csv
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ACTIVE_DOCTORS_PER_YEAR = 50
CAREER_MIN_YEARS = 20
CAREER_MAX_YEARS = 30
RANDOM_SEED = 42

SOURCE_DIR = Path(__file__).resolve().parents[2] / "dataset"
OUTPUT_DIR = SOURCE_DIR / "hospital"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("consolidate_hospital")


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def pick_hospital(orgs: pd.DataFrame) -> pd.Series:
    """Return the single org row with the highest UTILIZATION (tie → first)."""
    top = orgs.sort_values("UTILIZATION", ascending=False, kind="stable").iloc[0]
    log.info(
        "Chosen hospital: %s (%s) — UTILIZATION=%s",
        top["NAME"], top["Id"], top["UTILIZATION"],
    )
    return top


def build_doctor_generations(
    providers: pd.DataFrame,
    hospital_id: str,
    min_year: int,
    max_year: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """
    Build a reduced provider pool such that, for every year in
    [min_year, max_year], exactly ACTIVE_DOCTORS_PER_YEAR doctors are active.

    Each kept provider gets a (career_start, career_end) pair assigned
    in-memory. Only the pool actually used is returned; unused source
    providers are dropped.
    """
    pool = providers.sample(frac=1.0, random_state=RANDOM_SEED).reset_index(drop=True)
    pool_iter = iter(pool.to_dict("records"))

    def _next_source():
        try:
            return next(pool_iter)
        except StopIteration as exc:
            raise RuntimeError(
                "Exhausted the source provider pool before filling all years. "
                "Increase source data or lower ACTIVE_DOCTORS_PER_YEAR."
            ) from exc

    kept: list[dict] = []

    # Seed cohort: careers already overlapping at min_year, so the hospital is
    # fully staffed on day one.
    for _ in range(ACTIVE_DOCTORS_PER_YEAR):
        row = _next_source()
        career_length = int(rng.integers(CAREER_MIN_YEARS, CAREER_MAX_YEARS + 1))
        career_start = int(rng.integers(
            min_year - CAREER_MAX_YEARS + 1,
            min_year + 1,
        ))
        row["career_start"] = career_start
        row["career_end"] = career_start + career_length
        kept.append(row)

    # Walk forward year-by-year; whenever staffing drops below target, hire.
    for year in range(min_year, max_year + 1):
        active = sum(
            1 for d in kept if d["career_start"] <= year <= d["career_end"]
        )
        while active < ACTIVE_DOCTORS_PER_YEAR:
            row = _next_source()
            career_length = int(rng.integers(CAREER_MIN_YEARS, CAREER_MAX_YEARS + 1))
            row["career_start"] = year
            row["career_end"] = year + career_length
            kept.append(row)
            active += 1

    out = pd.DataFrame(kept)
    out["ORGANIZATION"] = hospital_id

    log.info(
        "Generated %d doctors covering %d–%d (target %d active/year)",
        len(out), min_year, max_year, ACTIVE_DOCTORS_PER_YEAR,
    )
    return out


def reassign_encounters(
    encounters: pd.DataFrame,
    doctors: pd.DataFrame,
    hospital_id: str,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Set every encounter's PROVIDER to a doctor active in its START year."""

    enc = encounters.copy()
    enc["_year"] = pd.to_datetime(enc["START"], utc=True, errors="coerce").dt.year

    missing = enc["_year"].isna().sum()
    if missing:
        log.warning("Dropping %d encounters with unparseable START dates", missing)
        enc = enc.dropna(subset=["_year"])
    enc["_year"] = enc["_year"].astype(int)

    active_by_year: dict[int, np.ndarray] = {}
    for year in range(enc["_year"].min(), enc["_year"].max() + 1):
        mask = (doctors["career_start"] <= year) & (doctors["career_end"] >= year)
        active_by_year[year] = doctors.loc[mask, "Id"].to_numpy()

    # Vectorized per-year random choice.
    new_providers = np.empty(len(enc), dtype=object)
    for year, group in enc.groupby("_year", sort=False):
        pool = active_by_year.get(int(year))
        if pool is None or len(pool) == 0:
            raise RuntimeError(f"No active doctors for year {year} — should not happen.")
        new_providers[group.index] = rng.choice(pool, size=len(group))

    enc["PROVIDER"] = new_providers
    enc["ORGANIZATION"] = hospital_id
    return enc.drop(columns="_year")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("Source: %s", SOURCE_DIR)
    log.info("Output: %s", OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RANDOM_SEED)

    log.info("Loading CSVs …")
    orgs = pd.read_csv(SOURCE_DIR / "organizations.csv")
    providers = pd.read_csv(SOURCE_DIR / "providers.csv")
    encounters = pd.read_csv(SOURCE_DIR / "encounters.csv")
    log.info(
        "Loaded: %d orgs, %d providers, %d encounters",
        len(orgs), len(providers), len(encounters),
    )

    hospital = pick_hospital(orgs)
    hospital_id = hospital["Id"]

    years = pd.to_datetime(encounters["START"], utc=True, errors="coerce").dt.year
    min_year, max_year = int(years.min()), int(years.max())
    log.info("Encounter years: %d – %d (%d years)", min_year, max_year, max_year - min_year + 1)

    doctors = build_doctor_generations(
        providers, hospital_id, min_year, max_year, rng,
    )

    new_encounters = reassign_encounters(encounters, doctors, hospital_id, rng)

    # -- write outputs -------------------------------------------------------
    new_orgs = hospital.to_frame().T.reset_index(drop=True)
    new_orgs.to_csv(OUTPUT_DIR / "organizations.csv", index=False)

    # Strip the in-memory career cols; preserve Synthea schema exactly.
    synthea_provider_cols = [
        "Id", "ORGANIZATION", "NAME", "GENDER", "SPECIALITY",
        "ADDRESS", "CITY", "STATE", "ZIP", "LAT", "LON", "UTILIZATION",
    ]
    doctors[synthea_provider_cols].to_csv(OUTPUT_DIR / "providers.csv", index=False)

    new_encounters.to_csv(OUTPUT_DIR / "encounters.csv", index=False)

    # -- sanity report -------------------------------------------------------
    active_hist = {
        y: int(((doctors["career_start"] <= y) & (doctors["career_end"] >= y)).sum())
        for y in (min_year, (min_year + max_year) // 2, max_year)
    }
    distinct_used = new_encounters["PROVIDER"].nunique()

    log.info("--- summary ---")
    log.info("organizations.csv rows : %d", len(new_orgs))
    log.info("providers.csv rows     : %d", len(doctors))
    log.info("encounters.csv rows    : %d", len(new_encounters))
    log.info("distinct providers used: %d", distinct_used)
    log.info("active/year sample     : %s", active_hist)
    log.info("Done.")


if __name__ == "__main__":
    main()
