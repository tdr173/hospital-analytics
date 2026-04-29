"use client";

import { useDispatch, useSelector } from "react-redux";
import { RootState, AppDispatch } from "@/store";
import { closeAnalysis } from "@/store/slices/clusters/ai-analysis-slice";
import { ClusterSummary, AiAnalysisResponse } from "@/models/generic/clusters";
import useClasses from "@/utils/useClasses";
import { ClusterAnalysisModalStyles } from "./ClusterAnalysisModalStyles";
import { colorWithAlpha } from "../../utils/colorWithAlpha";
import { RISK_STYLE } from "../../utils/riskStyle";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

interface Props {
  cluster: ClusterSummary;
}

export default function ClusterAnalysisModal({ cluster }: Props) {
  const classes = useClasses(ClusterAnalysisModalStyles, {
    name: "ClusterAnalysisModal",
  });
  const dispatch = useAppDispatch();
  const { cache, currentClusterId, loading, error } = useSelector(
    (state: RootState) => state.aiAnalysis,
  );

  const isOpen = currentClusterId === cluster.clusterId;
  const data: AiAnalysisResponse | undefined = cache[cluster.clusterId];
  const color = cluster.color;

  if (!isOpen) return null;

  const riskStyle = data
    ? (RISK_STYLE[data.riskLevel] ?? RISK_STYLE.moderate)
    : null;

  const close = () => dispatch(closeAnalysis());

  return (
    <div className={classes.overlay} onClick={close}>
      <div
        className={classes.modal}
        style={{ borderTopColor: color }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={classes.header}>
          <div className={classes.titleArea}>
            <p className={classes.label} style={{ color }}>
              AI Analysis · Cluster {cluster.clusterId}
            </p>
            <h2 className={classes.title}>{cluster.title}</h2>
            <div className={classes.meta}>
              <span className={classes.patientCount}>
                {cluster.count.toLocaleString()} patients · {cluster.percentage}%
              </span>
              {riskStyle && (
                <span
                  className={classes.riskBadge}
                  style={{
                    backgroundColor: riskStyle.bg,
                    color: riskStyle.color,
                  }}
                >
                  <span
                    className={classes.riskDot}
                    style={{ backgroundColor: riskStyle.dot }}
                  />
                  {riskStyle.label}
                </span>
              )}
            </div>
          </div>
          <button className={classes.closeBtn} onClick={close}>
            ✕
          </button>
        </div>

        <div className={classes.body}>
          {loading && (
            <div className={classes.loading} style={{ color }}>
              <style>{`@keyframes clusterModalSpin { to { transform: rotate(360deg); } }`}</style>
              <div className={classes.spinner} />
              <span className={classes.loadingText}>
                Generating analysis - this may take a moment...
              </span>
            </div>
          )}
          {error && <p className={classes.errorText}>{error}</p>}
          {data && !loading && <AnalysisContent data={data} color={color} />}
        </div>
      </div>
    </div>
  );
}

function AnalysisContent({
  data,
  color,
}: {
  data: AiAnalysisResponse;
  color: string;
}) {
  const classes = useClasses(ClusterAnalysisModalStyles, {
    name: "ClusterAnalysisModal",
  });
  const tinted = colorWithAlpha(color, 0.12);
  const tintedDark = colorWithAlpha(color, 0.9);

  return (
    <>
      <div className={classes.twoCol}>
        <div className={classes.section}>
          <p className={classes.sectionTitle}>Clinical Interpretation</p>
          <div className={classes.sectionDivider} style={{ backgroundColor: color }} />
          <p className={classes.sectionText}>{data.medicalInterpretation}</p>
        </div>
        <div className={classes.section}>
          <p className={classes.sectionTitle}>In Plain Language</p>
          <div className={classes.sectionDivider} style={{ backgroundColor: color }} />
          <p className={classes.sectionText}>{data.laypersonSummary}</p>
        </div>
      </div>

      <div className={classes.sectionAuto}>
        <p className={classes.sectionTitle}>Key Characteristics</p>
        <div className={classes.sectionDivider} style={{ backgroundColor: color }} />
        <div className={classes.characteristicsGrid}>
          {data.keyCharacteristics.map((c) => (
            <div key={c} className={classes.characteristicTag}>
              <span
                className={classes.characteristicDot}
                style={{ backgroundColor: color }}
              />
              {c}
            </div>
          ))}
        </div>
      </div>

      <div className={classes.sectionAuto}>
        <p className={classes.sectionTitle}>Priority Interventions</p>
        <div className={classes.sectionDivider} style={{ backgroundColor: color }} />
        <div className={classes.actionList}>
          {data.priorityInterventions.map((iv, i) => (
            <div key={iv} className={classes.actionItem}>
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

      <div className={classes.sectionAuto}>
        <p className={classes.sectionTitle}>Care Recommendations</p>
        <div className={classes.sectionDivider} style={{ backgroundColor: color }} />
        <div className={classes.actionList}>
          {data.careRecommendations.map((r, i) => (
            <div key={r} className={classes.actionItem}>
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
