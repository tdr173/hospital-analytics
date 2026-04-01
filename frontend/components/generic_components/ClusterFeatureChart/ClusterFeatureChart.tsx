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

export default function ClusterFeatureChart({ feature, data, clusterColors }: ClusterFeatureChartProps) {
  return (
    <div
      style={{
        backgroundColor: "#ffffff",
        borderRadius: 12,
        boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
        padding: "16px",
      }}
    >
      <p
        style={{
          fontFamily: "Inter, sans-serif",
          fontSize: "1rem",
          fontWeight: 600,
          color: "#191c1e",
          margin: "0 0 8px 0",
        }}
      >
        {toTitleCase(feature)}
      </p>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
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
                  <div
                    style={{
                      backgroundColor: "#ffffff",
                      borderRadius: 6,
                      boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                      padding: "8px 12px",
                      fontFamily: "Inter, sans-serif",
                      fontSize: 13,
                      color: "#191c1e",
                      maxWidth: 220,
                    }}
                  >
                    {entry.tooltip.split(" · ").map((line, i) => (
                      <div key={i} style={{ fontWeight: i === 0 ? 600 : 400, marginBottom: i === 0 ? 4 : 2 }}>
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
              const color = clusterColors?.[clusterId] ?? getClusterColor(index);
              return <Cell key={index} fill={color} />;
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
