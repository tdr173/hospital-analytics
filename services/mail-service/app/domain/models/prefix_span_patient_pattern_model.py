from sqlmodel import SQLModel, Field


class PrefixSpanPatientPatternModel(SQLModel, table=True):
    """
    Junction table: which patients contain each mined pattern.

    Access patterns:
      - patient → sequences : filter by patient_id
      - sequence → patients : filter by pattern_id
      - cluster → sequences : join with cluster_patient on patient_id,
                              then group by pattern_id
    """
    __tablename__ = "prefix_span_patient_pattern"
    __table_args__ = {"extend_existing": True}

    pattern_id: int = Field(foreign_key="prefix_span_pattern.id", primary_key=True)
    patient_id: str = Field(primary_key=True, index=True)
