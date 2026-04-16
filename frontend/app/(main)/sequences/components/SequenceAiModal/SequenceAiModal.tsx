"use client";

import { useSelector, useDispatch } from "react-redux";
import useClasses from "@/utils/useClasses";
import { RootState, AppDispatch } from "@/store";
import { closeSequenceAnalysis } from "@/store/slices/sequences/sequence-ai-slice";
import { SequenceListItem } from "@/models/generic/sequences";
import { SequenceAiModalStyles } from "./SequenceAiModalStyles";
import SequenceChipRow from "../SequenceChipRow/SequenceChipRow";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

interface Props {
  sequencesById: Record<number, SequenceListItem>;
  colors: Record<string, string>;
}

export default function SequenceAiModal({ sequencesById, colors }: Props) {
  const classes = useClasses(SequenceAiModalStyles, { name: "SequenceAiModal" });
  const dispatch = useAppDispatch();
  const { cache, currentPatternId, loading, error } = useSelector(
    (state: RootState) => state.sequenceAi,
  );

  if (currentPatternId === null) return null;
  const sequence = sequencesById[currentPatternId];
  if (!sequence) return null;

  const data = cache[currentPatternId];

  const close = () => dispatch(closeSequenceAnalysis());

  return (
    <div className={classes.overlay} onClick={close}>
      <div className={classes.modal} onClick={(e) => e.stopPropagation()}>
        <div className={classes.header}>
          <div className={classes.titleArea}>
            <p className={classes.label}>
              AI Analysis · Sequence #{sequence.rank}
            </p>
            <h2 className={classes.title}>Care Trajectory Pattern</h2>
            <p className={classes.meta}>
              {sequence.supportCount.toLocaleString()} patients · {sequence.supportPct}% ·{" "}
              {sequence.length} nodes
            </p>
          </div>
          <button className={classes.closeBtn} onClick={close} type="button">
            ✕
          </button>
        </div>

        <div className={classes.body}>
          <div className={classes.patternSection}>
            <SequenceChipRow patternStr={sequence.patternStr} colors={colors} />
          </div>

          {loading && (
            <div className={classes.loading}>
              <style>{`@keyframes seq-spin { to { transform: rotate(360deg); } }`}</style>
              <div className={classes.spinner} />
              <span>Generating analysis - this may take a moment...</span>
            </div>
          )}

          {error && <p className={classes.errorText}>{error}</p>}

          {data && !loading && (
            <>
              <div className={classes.twoCol}>
                <div className={classes.section}>
                  <p className={classes.sectionTitle}>Clinical Interpretation</p>
                  <div className={classes.sectionDivider} />
                  <p className={classes.sectionText}>
                    {data.clinicalInterpretation}
                  </p>
                </div>
                <div className={classes.section}>
                  <p className={classes.sectionTitle}>In Plain Language</p>
                  <div className={classes.sectionDivider} />
                  <p className={classes.sectionText}>{data.laypersonSummary}</p>
                </div>
              </div>

              <div className={classes.section}>
                <p className={classes.sectionTitle}>Risk Signals</p>
                <div className={classes.sectionDivider} />
                <div className={classes.actionList}>
                  {data.riskSignals.map((r, i) => (
                    <div key={r} className={classes.actionItem}>
                      <span className={classes.actionNumber}>{i + 1}</span>
                      <p className={classes.actionText}>{r}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className={classes.section}>
                <p className={classes.sectionTitle}>Recommendations</p>
                <div className={classes.sectionDivider} />
                <div className={classes.actionList}>
                  {data.recommendations.map((r, i) => (
                    <div key={r} className={classes.actionItem}>
                      <span className={classes.actionNumber}>{i + 1}</span>
                      <p className={classes.actionText}>{r}</p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
