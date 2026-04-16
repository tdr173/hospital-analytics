"use client";

import useClasses from "@/utils/useClasses";
import { TopSequence } from "@/models/generic/clusters";
import { ClusterTopSequencesStyles } from "./ClusterTopSequencesStyles";
import { colorWithAlpha } from "../../utils/colorWithAlpha";

interface Props {
  seq: TopSequence;
  color: string;
}

export default function SequenceItem({ seq, color }: Props) {
  const classes = useClasses(ClusterTopSequencesStyles, {
    name: "ClusterTopSequences",
  });

  const tinted = colorWithAlpha(color, 0.12);
  const tintedStrong = colorWithAlpha(color, 0.9);

  return (
    <div className={classes.item}>
      <span
        className={classes.rankBadge}
        style={{ backgroundColor: tinted, color: tintedStrong }}
      >
        {seq.rank}
      </span>
      <div className={classes.itemBody}>
        <p className={classes.pattern}>{seq.patternStr}</p>
        <div className={classes.metaRow}>
          <span className={classes.chip}>
            <span className={classes.chipLabel}>Length:</span>
            <span className={classes.chipValue}>{seq.length}</span>
          </span>
          <span className={classes.chip}>
            <span className={classes.chipLabel}>In cluster:</span>
            <span className={classes.chipValue}>
              {seq.clusterSupportCount.toLocaleString()} patients
            </span>
          </span>
          <span className={classes.chip}>
            <span className={classes.chipLabel}>Population support:</span>
            <span className={classes.chipValue}>{seq.supportPct}%</span>
          </span>
        </div>
      </div>
    </div>
  );
}
