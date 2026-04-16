"use client";

import useClasses from "@/utils/useClasses";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import { ClusterBadgeStyles } from "./ClusterBadgeStyles";

interface Props {
  color: string | null;
  title: string | null;
}

export default function ClusterBadge({ color, title }: Props) {
  const classes = useClasses(ClusterBadgeStyles, { name: "ClusterBadge" });
  if (!color || !title) return <span className={classes.empty}>-</span>;
  return (
    <span className={classes.container}>
      <span className={classes.dot} style={{ backgroundColor: color }} />
      <TruncatedText text={title} />
    </span>
  );
}
