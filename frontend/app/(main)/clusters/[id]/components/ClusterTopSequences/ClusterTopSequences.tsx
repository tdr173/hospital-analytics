"use client";

import useClasses from "@/utils/useClasses";
import { TopSequence } from "@/models/generic/clusters";
import { ClusterTopSequencesStyles } from "./ClusterTopSequencesStyles";
import SequenceItem from "./SequenceItem";

interface Props {
  sequences: TopSequence[];
  color: string;
}

export default function ClusterTopSequences({ sequences, color }: Props) {
  const classes = useClasses(ClusterTopSequencesStyles, {
    name: "ClusterTopSequences",
  });

  return (
    <div className={classes.card}>
      <p className={classes.sectionTitle}>Top 5 Sequential Patterns</p>
      {sequences.length === 0 ? (
        <div className={classes.empty}>No sequential patterns computed yet.</div>
      ) : (
        <div className={classes.list}>
          {sequences.map((seq) => (
            <SequenceItem key={seq.rank} seq={seq} color={color} />
          ))}
        </div>
      )}
    </div>
  );
}
