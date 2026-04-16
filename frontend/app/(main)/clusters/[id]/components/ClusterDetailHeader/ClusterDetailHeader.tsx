"use client";

import useClasses from "@/utils/useClasses";
import { ClusterDetailResponse } from "@/models/generic/clusters";
import { ClusterDetailHeaderStyles } from "./ClusterDetailHeaderStyles";

interface Props {
  cluster: ClusterDetailResponse;
}

export default function ClusterDetailHeader({ cluster }: Props) {
  const classes = useClasses(ClusterDetailHeaderStyles, { name: "ClusterDetailHeader" });
  const isOutlier = cluster.clusterId === -1;
  const label = isOutlier ? "Outliers" : `Cluster ${cluster.clusterId}`;
  const color = cluster.color;

  return (
    <div className={classes.card} style={{ borderLeftColor: color }}>
      <div className={classes.topRow}>
        <div className={classes.titleArea}>
          <p className={classes.label} style={{ color }}>{label}</p>
          <h1 className={classes.title}>{cluster.title}</h1>
        </div>
        <div
          className={classes.badge}
          style={{
            backgroundColor: isOutlier ? "#FEE2E2" : `${color}18`,
            color: isOutlier ? "#991B1B" : color,
          }}
        >
          <div className={classes.badgePercentage}>{cluster.size.percentage}%</div>
          <div className={classes.badgeLabel}>of population</div>
          <div className={classes.badgeCount}>
            {cluster.size.count.toLocaleString()} patients
          </div>
        </div>
      </div>

      <p className={classes.description}>{cluster.description}</p>

      <div className={classes.chipsRow}>
        <span className={classes.chip}>
          <span className={classes.chipLabel}>Careplan:</span>
          <span className={classes.chipValue}>{cluster.dominantCareplan}</span>
        </span>
        <span className={classes.chip}>
          <span className={classes.chipLabel}>Encounter Class:</span>
          <span className={classes.chipValue}>{cluster.dominantEncounterClass}</span>
        </span>
      </div>
    </div>
  );
}
