"use client";

import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { ClusterChartEntry } from "@/models/generic/clusters";
import useClasses from "@/utils/useClasses";
import { ClusterFeatureChartStyles } from "./ClusterFeatureChartStyles";

const CLUSTER_COLORS = ["#2563EB", "#16A34A", "#EAB308", "#7C3AED", "#0891B2"];

function getClusterColor(index: number): string {
  return CLUSTER_COLORS[index % CLUSTER_COLORS.length];
}

function toTitleCase(str: string): string {
  return str
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

interface ClusterFeatureChartProps {
  feature: string;
  data: ClusterChartEntry[];
  clusterColors?: Record<number, string>;
}

export default function ClusterFeatureChart({
  feature,
  data,
  clusterColors,
}: ClusterFeatureChartProps) {
  const classes = useClasses(ClusterFeatureChartStyles, {
    name: "ClusterFeatureChart",
  });

  return (
    <div className={classes.card}>
      <p className={classes.title}>{toTitleCase(feature)}</p>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart
          data={data}
          margin={{ top: 8, right: 16, left: 0, bottom: 4 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 12, fontFamily: "Inter, sans-serif" }}
            stroke="#6B7280"
          />
          <YAxis
            tick={{ fontSize: 12, fontFamily: "Inter, sans-serif" }}
            stroke="#6B7280"
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const entry = payload[0].payload as ClusterChartEntry;
                return (
                  <div className={classes.tooltipBox}>
                    {entry.tooltip.split(" · ").map((line, i) => (
                      <div
                        key={i}
                        className={
                          i === 0
                            ? classes.tooltipLineFirst
                            : classes.tooltipLineRest
                        }
                      >
                        {line}
                      </div>
                    ))}
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => {
              const clusterId = parseInt(entry.name.replace("Cluster ", ""));
              const color =
                clusterColors?.[clusterId] ?? getClusterColor(index);
              return <Cell key={index} fill={color} />;
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
