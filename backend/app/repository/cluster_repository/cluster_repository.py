import base64
from pathlib import Path
from sqlalchemy import func, case, cast, Numeric, text
from sqlalchemy.orm import Session

from domain import (
    ClusterModel, ClusterDetails, GetClustersDetails, ClusterPatientModel,
    ClusterMetaModel, PcaPoint, GetClusterStatistics, ChartEntry,
    FeatureChartData, GetNumericalFeaturesStatistics, CategoricalClusterEntry,
    CategoricalFeatureChartData, GetCategoricalFeaturesStatistics,
    AiAnalysisResponse, ClusterDetailResponse, ClusterSizeSchema,
    ClusterVitalsSchema, SeverityComponentsSchema, ClusterUtilizationSchema,
    DiseasePrevalenceSchema, DemographicsSchema, TopSequenceSchema,
)
from repository.cluster_repository.cluster_feature_helpers import (
    cluster_size,
    get_vitals,
    get_utilization,
    get_disease_prevalence,
    get_dominant_categoricals,
    get_gender_distribution,
    get_marital_distribution,
    get_smoking_distribution,
    get_condition_burden_distribution,
    get_population_stats,
)


_OUTPUTS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "clustering_algorithms" / "k_prototypes" / "outputs"
)


def _read_latest_images() -> tuple[str | None, str | None]:
    """Read heatmap + FAMD PNGs: outputs -> first version dir -> first run dir."""
    try:
        version_dirs = sorted(d for d in _OUTPUTS_DIR.iterdir() if d.is_dir())
        if not version_dirs:
            return None, None
        run_dirs = sorted(d for d in version_dirs[0].iterdir() if d.is_dir())
        if not run_dirs:
            return None, None
        run_dir = run_dirs[0]

        def _b64(pattern: str) -> str | None:
            p = next(run_dir.glob(pattern), None)
            return base64.b64encode(p.read_bytes()).decode() if p else None

        return _b64("heatmap_*.png"), _b64("famd_*.png")
    except Exception:
        return None, None


class ClusterRepository:
    def __init__(self, db: Session):
        self.db = db

    def _get_meta(self) -> ClusterMetaModel | None:
        return self.db.query(ClusterMetaModel).first()

    def get_all_clusters(self):
        db_clusters = self.db.query(ClusterModel).all()
        if not db_clusters:
            return GetClustersDetails(total_patients=0, clusters=[])

        total_patients = self.db.query(ClusterPatientModel).count()
        if total_patients == 0:
            return GetClustersDetails(total_patients=0, clusters=[])

        stats_rows = (
            self.db.query(
                ClusterPatientModel.cluster_label,
                func.count().label("cnt"),
                func.round(func.avg(cast(ClusterPatientModel.features["age"].astext, Numeric)), 1).label("avg_age"),
                func.round(func.avg(cast(ClusterPatientModel.features["qaly"].astext, Numeric)), 1).label("avg_qaly"),
                func.round(func.avg(cast(ClusterPatientModel.features["total_medications"].astext, Numeric)), 1).label("avg_meds"),
                func.round(func.avg(cast(ClusterPatientModel.features["active_conditions_count"].astext, Numeric)), 1).label("avg_active_conditions"),
                func.round(
                    100.0 * func.count(case(
                        (ClusterPatientModel.features["condition_burden"].astext.in_(["moderate", "high", "very_high"]), 1)
                    )) / func.nullif(func.count(), 0),
                    1,
                ).label("chronic_illness_pct"),
            )
            .group_by(ClusterPatientModel.cluster_label)
            .all()
        )

        stats_map = {
            row.cluster_label: {
                "count": row.cnt,
                "avg_age": float(row.avg_age or 0),
                "avg_qaly": float(row.avg_qaly or 0),
                "avg_meds": float(row.avg_meds or 0),
                "avg_active_conditions": float(row.avg_active_conditions or 0),
                "chronic_illness_pct": float(row.chronic_illness_pct or 0),
            }
            for row in stats_rows
        }

        parsed_clusters = []
        for cluster in db_clusters:
            stats = stats_map.get(cluster.cluster_label, {})
            c_count = stats.get("count", 0)

            cluster_dict = cluster.model_dump()
            cluster_dict["count"] = c_count
            cluster_dict["percentage"] = round((c_count / total_patients) * 100, 2)
            cluster_dict["avg_age"] = stats.get("avg_age", 0)
            cluster_dict["avg_qaly"] = stats.get("avg_qaly", 0)
            cluster_dict["avg_meds"] = stats.get("avg_meds", 0)
            cluster_dict["avg_active_conditions"] = stats.get("avg_active_conditions", 0)
            cluster_dict["chronic_illness_pct"] = stats.get("chronic_illness_pct", 0)

            parsed_clusters.append(ClusterDetails.model_validate(cluster_dict))

        return GetClustersDetails(total_patients=total_patients, clusters=parsed_clusters)

    def _get_cluster_colors(self) -> dict:
        clusters = self.db.query(ClusterModel.cluster_label, ClusterModel.color).all()
        return {c.cluster_label: c.color for c in clusters}

    def get_cluster_statistics(self) -> GetClusterStatistics:
        rows = (
            self.db.query(
                ClusterPatientModel.pca_x,
                ClusterPatientModel.pca_y,
                ClusterPatientModel.cluster_label,
                ClusterPatientModel.is_outlier,
            )
            .filter(
                ClusterPatientModel.pca_x.isnot(None),
                ClusterPatientModel.pca_y.isnot(None),
            )
            .all()
        )

        points = [
            PcaPoint(x=row.pca_x, y=row.pca_y, cluster=row.cluster_label, is_outlier=row.is_outlier)
            for row in rows
        ]

        heatmap_b64, pca_image_b64 = _read_latest_images()
        cluster_colors = self._get_cluster_colors()

        return GetClusterStatistics(
            points=points,
            heatmap=heatmap_b64,
            pca_image=pca_image_b64,
            cluster_colors=cluster_colors,
        )

    def get_numerical_features_statistics(self) -> GetNumericalFeaturesStatistics:
        meta = self._get_meta()
        if not meta or not meta.numerical_features:
            return GetNumericalFeaturesStatistics(features=[])

        numerical_features = meta.numerical_features

        select_exprs = []
        for f in numerical_features:
            col = cast(ClusterPatientModel.features[f].astext, Numeric)
            select_exprs.append(func.avg(col).label(f"{f}_mean"))
            select_exprs.append(
                func.percentile_cont(0.5).within_group(col).label(f"{f}_median")
            )

        rows = (
            self.db.query(ClusterPatientModel.cluster_label, *select_exprs)
            .filter(ClusterPatientModel.is_outlier == False)
            .group_by(ClusterPatientModel.cluster_label)
            .order_by(ClusterPatientModel.cluster_label)
            .all()
        )

        result = []
        for feature in numerical_features:
            data = []
            for row in rows:
                mean_val = round(float(getattr(row, f"{feature}_mean") or 0), 2)
                label = row.cluster_label
                data.append(ChartEntry(
                    name=f"Cluster {label}",
                    value=mean_val,
                    tooltip=f"Cluster {label} · Mean: {mean_val}",
                ))
            result.append(FeatureChartData(feature=feature, data=data))

        cluster_colors = self._get_cluster_colors()
        return GetNumericalFeaturesStatistics(features=result, cluster_colors=cluster_colors)

    def get_categorical_features_statistics(self) -> GetCategoricalFeaturesStatistics:
        meta = self._get_meta()
        if not meta or not meta.categorical_features:
            return GetCategoricalFeaturesStatistics(features=[])

        categorical_features = meta.categorical_features
        result = []

        for feature in categorical_features:
            rows = (
                self.db.query(
                    ClusterPatientModel.cluster_label,
                    ClusterPatientModel.features[feature].astext.label("cat_val"),
                    func.count().label("cnt"),
                )
                .filter(ClusterPatientModel.is_outlier == False)
                .group_by(
                    ClusterPatientModel.cluster_label,
                    ClusterPatientModel.features[feature].astext,
                )
                .order_by(ClusterPatientModel.cluster_label)
                .all()
            )

            totals: dict[int, int] = {}
            counts: dict[int, dict[str, int]] = {}
            for row in rows:
                cl = row.cluster_label
                cat = row.cat_val or "unknown"
                cnt = int(row.cnt)
                totals[cl] = totals.get(cl, 0) + cnt
                counts.setdefault(cl, {})[cat] = cnt

            all_categories = sorted({row.cat_val or "unknown" for row in rows})

            data = []
            for cl in sorted(totals.keys()):
                total = totals[cl]
                proportions = {
                    cat: round(counts[cl].get(cat, 0) / total, 4)
                    for cat in all_categories
                }
                data.append(CategoricalClusterEntry(cluster_id=cl, proportions=proportions))

            result.append(CategoricalFeatureChartData(feature=feature, categories=all_categories, data=data))

        cluster_colors = self._get_cluster_colors()
        return GetCategoricalFeaturesStatistics(features=result, cluster_colors=cluster_colors)

    def get_cluster_detail(self, cluster_id: int) -> ClusterDetailResponse:
        cluster = self.db.query(ClusterModel).filter(
            ClusterModel.cluster_label == cluster_id,
        ).first()
        if not cluster:
            raise ValueError(f"Cluster {cluster_id} not found")

        size = cluster_size(self.db, cluster_id)
        vitals = get_vitals(self.db, cluster_id)
        utilization = get_utilization(self.db, cluster_id)
        prevalence = get_disease_prevalence(self.db, cluster_id)
        dominants = get_dominant_categoricals(self.db, cluster_id)

        demographics = DemographicsSchema(
            gender=get_gender_distribution(self.db, cluster_id),
            marital=get_marital_distribution(self.db, cluster_id),
            smoking=get_smoking_distribution(self.db, cluster_id),
            condition_burden=get_condition_burden_distribution(self.db, cluster_id),
        )

        top_sequences = self._get_top_sequences(cluster_id)

        severity_components = SeverityComponentsSchema(
            avg_active_conditions=utilization["avg_active_conditions"],
            avg_medications=utilization["avg_medications"],
            avg_procedures=utilization["avg_procedures"],
        )

        return ClusterDetailResponse(
            cluster_id=cluster_id,
            cluster_type="outlier" if cluster_id == -1 else "regular",
            title=cluster.title,
            description=cluster.description,
            insight=cluster.insight,
            recommendation=cluster.recommendation,
            color=cluster.color,
            size=ClusterSizeSchema(**size),
            vitals=ClusterVitalsSchema(**vitals),
            utilization=ClusterUtilizationSchema(**utilization, severity_components=severity_components),
            disease_prevalence=DiseasePrevalenceSchema(**prevalence),
            demographics=demographics,
            dominant_careplan=dominants["dominant_careplan"],
            dominant_encounter_class=dominants["dominant_encounter_class"],
            dominant_marital=dominants["dominant_marital"],
            top_sequences=top_sequences,
        )

    def _get_top_sequences(self, cluster_id: int) -> list[TopSequenceSchema]:
        if cluster_id == -1:
            sql = text("""
                SELECT p.rank, p.pattern_str, p.length, p.support_count, p.support_pct,
                       COUNT(DISTINCT pp.patient_id) AS cluster_support_count
                FROM prefix_span_patient_pattern pp
                JOIN cluster_patient cp ON pp.patient_id = cp.patient_id
                JOIN prefix_span_pattern p ON pp.pattern_id = p.id
                WHERE cp.is_outlier = true
                GROUP BY p.id, p.rank, p.pattern_str, p.length, p.support_count, p.support_pct
                ORDER BY cluster_support_count DESC
                LIMIT 5
            """)
            rows = self.db.execute(sql).mappings().all()
        else:
            sql = text("""
                SELECT p.rank, p.pattern_str, p.length, p.support_count, p.support_pct,
                       COUNT(DISTINCT pp.patient_id) AS cluster_support_count
                FROM prefix_span_patient_pattern pp
                JOIN cluster_patient cp ON pp.patient_id = cp.patient_id
                JOIN prefix_span_pattern p ON pp.pattern_id = p.id
                WHERE cp.cluster_label = :cluster_id AND cp.is_outlier = false
                GROUP BY p.id, p.rank, p.pattern_str, p.length, p.support_count, p.support_pct
                ORDER BY cluster_support_count DESC
                LIMIT 5
            """)
            rows = self.db.execute(sql, {"cluster_id": cluster_id}).mappings().all()

        return [
            TopSequenceSchema(
                rank=row["rank"],
                pattern_str=row["pattern_str"],
                length=row["length"],
                support_count=row["support_count"],
                support_pct=float(row["support_pct"]),
                cluster_support_count=int(row["cluster_support_count"]),
            )
            for row in rows
        ]

    def get_cluster_labels_missing_detail_cache(self) -> list[int]:
        rows = (
            self.db.query(ClusterModel.cluster_label)
            .filter(ClusterModel.detail_cache.is_(None))
            .order_by(ClusterModel.cluster_label)
            .all()
        )
        return [row[0] for row in rows]

    def get_cluster_detail_cache(self, cluster_id: int) -> ClusterDetailResponse | None:
        cluster = self.db.query(ClusterModel).filter(
            ClusterModel.cluster_label == cluster_id,
        ).first()
        if cluster and cluster.detail_cache:
            return ClusterDetailResponse.model_validate(cluster.detail_cache)
        return None

    def save_cluster_detail_cache(self, cluster_id: int, detail: ClusterDetailResponse) -> None:
        self.db.query(ClusterModel).filter(
            ClusterModel.cluster_label == cluster_id,
        ).update({"detail_cache": detail.model_dump()}, synchronize_session="fetch")
        self.db.commit()

    def get_cluster_ai_analysis(self, cluster_id: int) -> AiAnalysisResponse | None:
        cluster = self.db.query(ClusterModel).filter(
            ClusterModel.cluster_label == cluster_id,
        ).first()
        if not cluster:
            raise ValueError(f"Cluster {cluster_id} not found")
        if cluster.ai_analysis:
            return AiAnalysisResponse(**cluster.ai_analysis)
        return None

    def lock_cluster_ai_analysis(self, cluster_id: int) -> AiAnalysisResponse | None:
        """Acquire a row-level lock and return cached analysis if present.

        Caller must commit/rollback to release the lock - the service layer
        calls save_cluster_ai_analysis which commits.
        """
        cluster = self.db.query(ClusterModel).filter(
            ClusterModel.cluster_label == cluster_id,
        ).with_for_update().first()
        if not cluster:
            raise ValueError(f"Cluster {cluster_id} not found")
        if cluster.ai_analysis:
            return AiAnalysisResponse(**cluster.ai_analysis)
        return None

    def save_cluster_ai_analysis(self, cluster_id: int, analysis: dict) -> None:
        self.db.query(ClusterModel).filter(
            ClusterModel.cluster_label == cluster_id,
        ).update({"ai_analysis": analysis}, synchronize_session="fetch")
        self.db.commit()

    def get_ai_context(self, cluster_id: int) -> dict:
        meta = self._get_meta()
        if not meta:
            raise ValueError("No clustering data found")

        cluster = self.db.query(ClusterModel).filter(
            ClusterModel.cluster_label == cluster_id,
        ).first()
        if not cluster:
            raise ValueError(f"Cluster {cluster_id} not found")

        size = cluster_size(self.db, cluster_id)
        vitals = get_vitals(self.db, cluster_id)
        utilization = get_utilization(self.db, cluster_id)
        prevalence = get_disease_prevalence(self.db, cluster_id)
        dominants = get_dominant_categoricals(self.db, cluster_id)
        gender = get_gender_distribution(self.db, cluster_id)
        smoking = get_smoking_distribution(self.db, cluster_id)
        population = get_population_stats(self.db)

        return {
            "meta": {
                "n_patients": meta.n_patients,
                "n_clusters": meta.n_clusters,
                "metrics": meta.metrics or {},
            },
            "cluster": {
                "title": cluster.title,
                "description": cluster.description,
                "cluster_id": cluster_id,
            },
            "size": size,
            "vitals": vitals,
            "utilization": utilization,
            "prevalence": prevalence,
            "dominants": dominants,
            "gender": gender,
            "smoking": smoking,
            "population": population,
        }
