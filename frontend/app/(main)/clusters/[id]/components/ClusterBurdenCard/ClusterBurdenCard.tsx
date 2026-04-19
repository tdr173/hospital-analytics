"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from "recharts";
import useClasses from "@/utils/useClasses";
import { ClusterUtilization } from "@/models/generic/clusters";
import { ClusterBurdenCardStyles } from "./ClusterBurdenCardStyles";
import { colorWithAlpha } from "../../utils/colorWithAlpha";

interface Props {
  utilization: ClusterUtilization;
  color: string;
}

export default function ClusterBurdenCard({ utilization, color }: Props) {
  const classes = useClasses(ClusterBurdenCardStyles, { name: "ClusterBurdenCard" });

  const stats = [
    { label: "Active Conditions", value: utilization.avgActiveConditions },
    { label: "Medications", value: utilization.avgMedications },
    { label: "Procedures", value: utilization.avgProcedures },
    { label: "Days Since Last Visit", value: utilization.avgDaysSinceEncounter },
    { label: "Different Clinicians", value: utilization.avgDistinctProviders },
  ];

  const careTypes = [
    { key: "routine", label: "Routine", value: utilization.avgRoutineCare, fill: color },
    { key: "wellness", label: "Wellness", value: utilization.avgWellnessCare, fill: colorWithAlpha(color, 0.7) },
    { key: "acute", label: "Acute", value: utilization.avgAcuteCare, fill: colorWithAlpha(color, 0.45) },
    { key: "severe", label: "Severe", value: utilization.avgSevereCare, fill: colorWithAlpha(color, 0.25) },
  ];

  const stackedData = [
    careTypes.reduce(
      (acc, c) => ({ ...acc, [c.key]: c.value }),
      { name: "care" } as Record<string, number | string>,
    ),
  ];

  return (
    <div className={classes.card}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <p className={classes.sectionTitle}>Clinical Burden Profile</p>
        <div className={classes.severityBlock}>
          <div className={classes.severityValue}>{utilization.avgClinicalSeverityScore}</div>
          <div className={classes.severityCaption}>Clinical Severity Score</div>
        </div>
      </div>

      <div className={classes.twoCol}>
        <div className={classes.statsList}>
          {stats.map((s) => (
            <div key={s.label} className={classes.statRow}>
              <span className={classes.statLabel}>{s.label}</span>
              <span className={classes.statValue}>{s.value}</span>
            </div>
          ))}
        </div>

        <div className={classes.rightColumn}>
          <div>
            <p className={classes.sectionTitle} style={{ marginBottom: 8 }}>
              Care Type Breakdown (per Patient)
            </p>
            <div className={classes.chartWrapper}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  layout="vertical"
                  data={stackedData}
                  margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
                  stackOffset="expand"
                >
                  <XAxis type="number" hide domain={[0, "dataMax"]} />
                  <YAxis type="category" dataKey="name" hide />
                  <Tooltip contentStyle={{ fontSize: 12 }} />
                  {careTypes.map((ct, idx) => (
                    <Bar
                      key={ct.key}
                      dataKey={ct.key}
                      stackId="care"
                      fill={ct.fill}
                      radius={
                        idx === 0
                          ? [4, 0, 0, 4]
                          : idx === careTypes.length - 1
                            ? [0, 4, 4, 0]
                            : 0
                      }
                    >
                      <LabelList
                        dataKey={ct.key}
                        position="center"
                        fill="#ffffff"
                        fontSize={11}
                        fontWeight={600}
                      />
                    </Bar>
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className={classes.legendRow} style={{ marginTop: 8 }}>
              {careTypes.map((ct) => (
                <span key={ct.key} className={classes.legendItem}>
                  <span className={classes.legendDot} style={{ backgroundColor: ct.fill }} />
                  {ct.label}: {ct.value}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
