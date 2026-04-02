"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { CategoricalFeatureChartData } from "@/models/generic/clusters";
import useClasses from "@/utils/useClasses";
import { StackedBarChartComponentStyles } from "./StackedBarChartComponentStyles";

const ORDERED_COLORS = [
  "#DC2626", // red
  "#2563EB", // blue
  "#16A34A", // green
  "#F97316", // orange
  "#06B6D4", // cyan
  "#7C3AED", // purple
  "#92400E", // brown
  "#EAB308", // yellow
  "#9CA3AF", // gray
  "#BE185D", // pink
];

function getCategoryColors(count: number): string[] {
  return ORDERED_COLORS.slice(0, count);
}

function toTitleCase(str: string): string {
  return str
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

interface StackedBarChartComponentProps {
  featureData: CategoricalFeatureChartData;
}

export default function StackedBarChartComponent({ featureData }: StackedBarChartComponentProps) {
  const { feature, categories, data } = featureData;
  const colors = getCategoryColors(categories.length);
  const classes = useClasses(StackedBarChartComponentStyles, { name: "StackedBarChartComponent" });

  const chartData = data.map((entry) => ({
    name: `Cluster ${entry.clusterId}`,
    ...entry.proportions,
  }));

  return (
    <div className={classes.card}>
      <p className={classes.title}>
        {toTitleCase(feature)}
      </p>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 12, fontFamily: "Inter, sans-serif", textAnchor: "middle" }}
            stroke="#6B7280"
          />
          <YAxis
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            domain={[0, 1]}
            tick={{ fontSize: 12, fontFamily: "Inter, sans-serif" }}
            stroke="#6B7280"
          />
          <Tooltip
            formatter={(value: number, name: string) => [
              `${(value * 100).toFixed(1)}%`,
              toTitleCase(name),
            ]}
            contentStyle={{
              fontFamily: "Inter, sans-serif",
              fontSize: 13,
              borderRadius: 6,
              boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
              border: "none",
            }}
          />
          <Legend
            align="center"
            formatter={(value) => toTitleCase(value)}
            wrapperStyle={{ fontFamily: "Inter, sans-serif", fontSize: 12, textAlign: "center", width: "100%" }}
          />
          {categories.map((cat, i) => (
            <Bar key={cat} dataKey={cat} stackId="a" fill={colors[i]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
