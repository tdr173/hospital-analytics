"use client";

import { useRouter } from "next/navigation";
import { useDispatch, useSelector } from "react-redux";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import AssignmentOutlinedIcon from "@mui/icons-material/AssignmentOutlined";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import { RootState, AppDispatch } from "@/store";
import { getAiAnalysis } from "@/store/slices/clusters/thunks";
import { openAnalysis } from "@/store/slices/clusters/ai-analysis-slice";
import { ClusterSummary } from "@/models/generic/clusters";
import useClasses from "@/utils/useClasses";
import { ClusterCardStyles } from "./ClusterCardStyles";
import ClusterAnalysisModal from "../ClusterAnalysisModal/ClusterAnalysisModal";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

interface Props {
  cluster: ClusterSummary;
}

export default function ClusterCard({ cluster }: Props) {
  const classes = useClasses(ClusterCardStyles, { name: "ClusterCard" });
  const router = useRouter();
  const dispatch = useAppDispatch();
  const { cache } = useSelector((state: RootState) => state.aiAnalysis);

  const color = cluster.color;
  const isOutlier = cluster.clusterId === -1;
  const label = isOutlier ? "Outliers" : `Cluster ${cluster.clusterId}`;

  const handleAnalyse = () => {
    dispatch(openAnalysis(cluster.clusterId));
    if (!cache[cluster.clusterId]) {
      dispatch(getAiAnalysis(cluster.clusterId));
    }
  };

  return (
    <div className={classes.card} style={{ borderLeftColor: color }}>
      <div className={classes.header}>
        <div className={classes.titleArea}>
          <h3 className={classes.title}>
            {label}: {cluster.title}
          </h3>
          <p className={classes.patientCount}>
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

      <p className={classes.description}>{cluster.description}</p>

      <div className={classes.statsGrid}>
        <div className={classes.statBox}>
          <div className={classes.statLabel}>Avg Age</div>
          <div className={classes.statValue}>
            {cluster.avgAge}
            <span className={classes.statUnit}>years</span>
          </div>
        </div>
        <div className={classes.statBox}>
          <div className={classes.statLabel}>Avg QALY</div>
          <div className={classes.statValue}>{cluster.avgQaly}</div>
        </div>
        <div className={classes.statBox}>
          <div className={classes.statLabel}>Chronic Illness</div>
          <div className={classes.statValue}>
            {cluster.chronicIllnessPct}
            <span className={classes.statUnit}>%</span>
          </div>
        </div>
        <div className={classes.statBox}>
          <div className={classes.statLabel}>Avg Meds</div>
          <div className={classes.statValue}>{cluster.avgMeds}</div>
        </div>
        <div className={classes.statBox}>
          <div className={classes.statLabel}>Active Conditions</div>
          <div className={classes.statValue}>{cluster.avgActiveConditions}</div>
        </div>
      </div>

      <div className={classes.footer}>
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

      <div className={classes.actions}>
        <button
          className={classes.analyseButton}
          style={{ color, borderColor: color }}
          onClick={handleAnalyse}
        >
          <AutoAwesomeIcon className={classes.analyseButtonIcon} />
          Analyse with AI
        </button>
        <button
          className={classes.viewButton}
          style={{ backgroundColor: color }}
          onClick={() => router.push(`/clusters/${cluster.clusterId}`)}
        >
          View Details
        </button>
      </div>

      <ClusterAnalysisModal cluster={cluster} />
    </div>
  );
}
