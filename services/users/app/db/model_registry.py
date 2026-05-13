"""Maps SERVICE_NAME -> the set of SQLModel tables that service owns.

Used at startup to call `SQLModel.metadata.create_all(engine, tables=[...])`
with only the subset of tables that belong to this service's database. This
keeps each service's DB scoped to its real ownership.

Tables not listed for a service are still importable in code (so the LLM SQL
agent and analytics code paths work via cross-DB read engines), but they
are not auto-created on this service's primary engine.
"""
from __future__ import annotations

from sqlmodel import SQLModel

# Side-effect import: ensures every model class is registered on
# SQLModel.metadata so we can pluck individual Table objects out by name.
from domain import models as _all_models  # noqa: F401


# Owner table sets, by service name. Members are __tablename__ strings.
SERVICE_TABLES: dict[str, set[str]] = {
    "auth": {"auth_user"},
    "users": {"user_profile"},
    "clinical-core": {
        "patient", "provider", "organization", "patient_provider",
        "encounter", "condition", "medication", "allergy",
        "careplan", "observation", "immunization", "procedure",
    },
    "analytics": set(),  # owns only materialized views (created via raw SQL)
    "ml-batch": {
        "cluster", "cluster_meta", "cluster_patient",
        "prefix_span_pattern", "prefix_span_patient_pattern",
    },
    "mail-service": set(),
    "queue-service": set(),  # APScheduler manages its own table on first run
    # Monolith: every table.
    "monolith": {t.name for t in SQLModel.metadata.tables.values()},
}


def tables_for(service_name: str) -> list:
    """Return the list of Table objects this service should auto-create."""
    names = SERVICE_TABLES.get(service_name, set())
    return [t for t in SQLModel.metadata.tables.values() if t.name in names]
