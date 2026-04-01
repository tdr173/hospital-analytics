"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useRouter } from "next/navigation";
import { RootState, AppDispatch } from "@/store";
import { getClusterRuns, getAiAnalysis } from "@/store/slices/clusters/thunks";
import {
  openAnalysis,
  closeAnalysis,
} from "@/store/slices/clusters/ai-analysis-slice";
import useClasses from "@/utils/useClasses";
import { ClustersPageStyles } from "../ClustersPageStyles";
import { ClusterSummary, AiAnalysisResponse } from "@/models/generic/clusters";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import AssignmentOutlinedIcon from "@mui/icons-material/AssignmentOutlined";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const RISK_STYLE: Record<
  string,
  { bg: string; color: string; dot: string; label: string }
> = {
  high: { bg: "#fee2e2", color: "#991b1b", dot: "#ef4444", label: "High Risk" },
  moderate: {
    bg: "#fef9c3",
    color: "#854d0e",
    dot: "#eab308",
    label: "Moderate Risk",
  },
  low: { bg: "#dcfce7", color: "#166534", dot: "#22c55e", label: "Low Risk" },
};

// Derive a tinted background from the cluster color for numbered badges
function colorWithAlpha(hex: string, alpha: number) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function AiAnalysisModal({
  cluster,
  classes,
}: {
  cluster: ClusterSummary;
  classes: ReturnType<typeof useClasses<typeof ClustersPageStyles>>;
}) {
  const dispatch = useAppDispatch();
  const { cache, currentClusterId, loading, error } = useSelector(
    (state: RootState) => state.aiAnalysis,
  );

  const isOpen = currentClusterId === cluster.cluster_id;
  const data: AiAnalysisResponse | undefined = cache[cluster.cluster_id];
  const color = cluster.color;

  if (!isOpen) return null;

  const riskStyle = data
    ? (RISK_STYLE[data.risk_level] ?? RISK_STYLE.moderate)
    : null;

  return (
    <div
      className={classes.modalOverlay}
      onClick={() => dispatch(closeAnalysis())}
    >
      <div
        className={classes.modal}
        style={{ borderTop: `4px solid ${color}` }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header - matches card design: white bg, colored top border */}
        <div className={classes.modalHeader}>
          <div className={classes.modalTitleArea}>
            <p className={classes.modalLabel} style={{ color }}>
              AI Analysis · Cluster {cluster.cluster_id}
            </p>
            <h2 className={classes.modalTitle}>{cluster.title}</h2>
            <div className={classes.modalMeta}>
              <span className={classes.modalPatientCount}>
                {cluster.count.toLocaleString()} patients · {cluster.percentage}
                %
              </span>
              {riskStyle && (
                <span
                  className={classes.riskBadgeInline}
                  style={{
                    backgroundColor: riskStyle.bg,
                    color: riskStyle.color,
                  }}
                >
                  <span
                    style={{
                      width: 7,
                      height: 7,
                      borderRadius: "50%",
                      backgroundColor: riskStyle.dot,
                      display: "inline-block",
                      flexShrink: 0,
                    }}
                  />
                  {riskStyle.label}
                </span>
              )}
            </div>
          </div>
          <button
            className={classes.modalCloseBtn}
            onClick={() => dispatch(closeAnalysis())}
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className={classes.modalBody}>
          {loading && (
            <div className={classes.modalLoading} style={{ color }}>
              <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
              <div className={classes.spinner} />
              <span style={{ color: "var(--text-secondary, #64748b)" }}>
                Generating analysis - this may take a moment...
              </span>
            </div>
          )}
          {error && (
            <p style={{ color: "#dc2626", fontSize: "0.875rem", margin: 0 }}>
              {error}
            </p>
          )}
          {data && !loading && (
            <AnalysisContent data={data} color={color} classes={classes} />
          )}
        </div>
      </div>
    </div>
  );
}

function AnalysisContent({
  data,
  color,
  classes,
}: {
  data: AiAnalysisResponse;
  color: string;
  classes: ReturnType<typeof useClasses<typeof ClustersPageStyles>>;
}) {
  const tinted = colorWithAlpha(color, 0.12);
  const tintedDark = colorWithAlpha(color, 0.9);

  return (
    <>
      {/* Clinical Interpretation + Plain Language - equal height */}
      <div className={classes.twoCol}>
        <div className={classes.section}>
          <p className={classes.sectionTitle}>Clinical Interpretation</p>
          <div
            className={classes.sectionDivider}
            style={{ backgroundColor: color }}
          />
          <p className={classes.sectionText}>{data.medical_interpretation}</p>
        </div>
        <div className={classes.section}>
          <p className={classes.sectionTitle}>In Plain Language</p>
          <div
            className={classes.sectionDivider}
            style={{ backgroundColor: color }}
          />
          <p className={classes.sectionText}>{data.layperson_summary}</p>
        </div>
      </div>

      {/* Key Characteristics - 2×2 compact grid */}
      <div className={classes.section} style={{ height: "auto" }}>
        <p className={classes.sectionTitle}>Key Characteristics</p>
        <div
          className={classes.sectionDivider}
          style={{ backgroundColor: color }}
        />
        <div className={classes.characteristicsGrid}>
          {data.key_characteristics.map((c, i) => (
            <div key={i} className={classes.characteristicTag}>
              <span
                className={classes.characteristicDot}
                style={{ backgroundColor: color }}
              />
              {c}
            </div>
          ))}
        </div>
      </div>

      {/* Priority Interventions - full width, numbered */}
      <div className={classes.section} style={{ height: "auto" }}>
        <p className={classes.sectionTitle}>Priority Interventions</p>
        <div
          className={classes.sectionDivider}
          style={{ backgroundColor: color }}
        />
        <div className={classes.actionList}>
          {data.priority_interventions.map((iv, i) => (
            <div key={i} className={classes.actionItem}>
              <span
                className={classes.actionNumber}
                style={{ backgroundColor: tinted, color: tintedDark }}
              >
                {i + 1}
              </span>
              <p className={classes.actionText}>{iv}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Care Recommendations - full width, numbered */}
      <div className={classes.section} style={{ height: "auto" }}>
        <p className={classes.sectionTitle}>Care Recommendations</p>
        <div
          className={classes.sectionDivider}
          style={{ backgroundColor: color }}
        />
        <div className={classes.actionList}>
          {data.care_recommendations.map((r, i) => (
            <div key={i} className={classes.actionItem}>
              <span
                className={classes.actionNumber}
                style={{ backgroundColor: tinted, color: tintedDark }}
              >
                {i + 1}
              </span>
              <p className={classes.actionText}>{r}</p>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

function ClusterCard({
  cluster,
  classes,
}: {
  cluster: ClusterSummary;
  classes: ReturnType<typeof useClasses<typeof ClustersPageStyles>>;
}) {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const { cache } = useSelector((state: RootState) => state.aiAnalysis);
  const color = cluster.color;
  const isOutlier = cluster.cluster_id === -1;
  const label = isOutlier ? "Outliers" : `Cluster ${cluster.cluster_id}`;

  const handleAnalyse = () => {
    dispatch(openAnalysis(cluster.cluster_id));
    if (!cache[cluster.cluster_id]) {
      dispatch(getAiAnalysis(cluster.cluster_id));
    }
  };

  return (
    <div className={classes.card} style={{ borderLeftColor: color }}>
      <div className={classes.cardHeader}>
        <div className={classes.cardTitleArea}>
          <h3 className={classes.cardTitle}>
            {label}: {cluster.title}
          </h3>
          <p className={classes.cardPatientCount}>
            {cluster.count.toLocaleString()} patients total
          </p>
        </div>
        <div
          className={classes.badge}
          style={{
            backgroundColor: isOutlier ? "#FEE2E2" : `${color}18`,
            color: isOutlier ? "#991B1B" : color,
          }}
        >
          <div className={classes.badgePercentage}>{cluster.percentage}%</div>
          <div className={classes.badgeLabel}>patients</div>
        </div>
      </div>

      <p className={classes.cardDescription}>{cluster.description}</p>

      <div className={classes.statsGrid}>
        <div className={classes.statBox}>
          <div className={classes.statLabel}>Avg Age</div>
          <div className={classes.statValue}>
            {cluster.avg_age}
            <span className={classes.statUnit}>years</span>
          </div>
        </div>
        <div className={classes.statBox}>
          <div className={classes.statLabel}>Avg QALY</div>
          <div className={classes.statValue}>{cluster.avg_qaly}</div>
        </div>
        <div className={classes.statBox}>
          <div className={classes.statLabel}>Chronic Illness</div>
          <div className={classes.statValue}>
            {cluster.chronic_illness_pct}
            <span className={classes.statUnit}>%</span>
          </div>
        </div>
        <div className={classes.statBox}>
          <div className={classes.statLabel}>Avg Meds</div>
          <div className={classes.statValue}>{cluster.avg_meds}</div>
        </div>
      </div>

      <div className={classes.cardFooter}>
        <div className={classes.footerRow}>
          <CheckCircleOutlineIcon
            className={classes.footerIcon}
            style={{ color }}
          />
          <span>
            <span className={classes.footerLabel}>Insights: </span>
            {cluster.insight}
          </span>
        </div>
        <div className={classes.footerRow}>
          <AssignmentOutlinedIcon
            className={classes.footerIcon}
            style={{ color }}
          />
          <span>
            <span className={classes.footerLabel}>Recommendation: </span>
            {cluster.recommendation}
          </span>
        </div>
      </div>

      <div className={classes.cardActions}>
        <button
          className={classes.analyseButton}
          style={{ color, borderColor: color }}
          onClick={handleAnalyse}
        >
          <AutoAwesomeIcon style={{ width: 15, height: 15 }} />
          Analyse with AI
        </button>
        <button
          className={classes.viewButton}
          style={{ backgroundColor: color, flex: 1, margin: 0 }}
          onClick={() => router.push(`/clusters/${cluster.cluster_id}`)}
        >
          View Details
        </button>
      </div>

      <AiAnalysisModal cluster={cluster} classes={classes} />
    </div>
  );
}

export default function ClusterSummariesPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.clusters,
  );
  const dispatch = useAppDispatch();
  const classes = useClasses(ClustersPageStyles, { name: "ClustersPage" });

  useEffect(() => {
    dispatch(getClusterRuns());
  }, [dispatch]);

  if (loading)
    return <div className={classes.loading}>Loading cluster data...</div>;
  if (error) return <div className={classes.error}>{error}</div>;
  if (!data || data.clusters.length === 0)
    return <div className={classes.empty}>No cluster data available.</div>;

  return (
    <div className={classes.content}>
      <div className={classes.grid}>
        {data.clusters.map((cluster) => (
          <ClusterCard
            key={cluster.cluster_id}
            cluster={cluster}
            classes={classes}
          />
        ))}
      </div>
    </div>
  );
}
