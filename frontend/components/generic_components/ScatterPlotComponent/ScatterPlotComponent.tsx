"use client";

import ReactECharts from "echarts-for-react";
import { PcaPoint } from "@/models/generic/clusters";

const CLUSTER_COLORS = [
  "#2563EB",
  "#16A34A",
  "#EAB308",
  "#7C3AED",
  "#0891B2",
];
const OUTLIER_COLOR = "#EF4444";

function getClusterColor(clusterId: number, index: number): string {
  if (clusterId === -1) return OUTLIER_COLOR;
  return CLUSTER_COLORS[index % CLUSTER_COLORS.length];
}

interface ScatterPlotComponentProps {
  points: PcaPoint[];
  title?: string;
  clusterColors?: Record<number, string>;
}

export default function ScatterPlotComponent({ points, title = "PCA Scatter Plot", clusterColors }: ScatterPlotComponentProps) {
  const clusterIds = Array.from(new Set(points.map((p) => p.cluster))).filter((id) => id !== -1).sort((a, b) => a - b);

  const series = clusterIds.map((clusterId, idx) => ({
    name: `Cluster ${clusterId}`,
    type: "scatter" as const,
    data: points
      .filter((p) => p.cluster === clusterId)
      .map((p) => [p.x, p.y]),
    symbolSize: 5,
    itemStyle: {
      color: clusterColors?.[clusterId] ?? getClusterColor(clusterId, idx),
      opacity: 0.75,
    },
  }));

  const option = {
    tooltip: {
      trigger: "item",
      formatter: (params: { seriesName: string; data: number[] }) =>
        `${params.seriesName}<br/>PC1: ${params.data[0].toFixed(3)}<br/>PC2: ${params.data[1].toFixed(3)}`,
    },
    legend: {
      bottom: 0,
      textStyle: { fontFamily: "Inter, sans-serif", fontSize: 12 },
    },
    xAxis: {
      name: "PC1",
      nameLocation: "middle" as const,
      nameGap: 25,
      splitLine: { lineStyle: { type: "dashed" as const, color: "#e5e7eb" } },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: {
      name: "PC2",
      nameLocation: "middle" as const,
      nameGap: 35,
      splitLine: { lineStyle: { type: "dashed" as const, color: "#e5e7eb" } },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    grid: { top: 48, bottom: 56, left: 56, right: 24 },
    series,
  };

  return (
    <div
      style={{
        backgroundColor: "#ffffff",
        borderRadius: 12,
        boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
        padding: "16px",
      }}
    >
      <p style={{ fontFamily: "Inter, sans-serif", fontSize: "1rem", fontWeight: 600, color: "#191c1e", margin: "0 0 8px 0" }}>
        {title}
      </p>
      <ReactECharts option={option} style={{ height: 480 }} />
    </div>
  );
}
