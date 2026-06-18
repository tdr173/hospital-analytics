"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import useClasses from "@/utils/useClasses";
import theme from "@/utils/theme";
import { TopConditionItem } from "@/models/generic/dashboard";
import { TopConditionsBarStyles } from "./TopConditionsBarStyles";
import { truncate } from "../../utils/formatters";

interface Props {
  data: TopConditionItem[];
  title?: string;
}

export default function TopConditionsBar({ data, title }: Props) {
  const classes = useClasses(TopConditionsBarStyles, {
    name: "TopConditionsBar",
  });

  const total = data.reduce((acc, d) => acc + d.count, 0);
  const chartData = data.map((d) => ({
    name: truncate(d.description, 50),
    fullName: d.description,
    value: d.count,
    pct: total > 0 ? (d.count / total) * 100 : 0,
  }));

  // Explicit height so the chart renders regardless of the parent's height.
  const chartHeight = Math.max(240, chartData.length * 34);

  return (
    <div className={classes.card}>
      <p className={classes.title}>{title ?? "Top 10 Conditions"}</p>
      {chartData.length === 0 ? (
        <div className={classes.empty}>
          No conditions recorded in this period.
        </div>
      ) : (
        <div className={classes.chartWrapper}>
          <ResponsiveContainer width="100%" height={chartHeight}>
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 4, right: 24, left: 8, bottom: 4 }}
            >
              <CartesianGrid
                horizontal={false}
                strokeDasharray="3 3"
                stroke="#E5E7EB"
              />
              <XAxis type="number" hide domain={[0, "dataMax"]} />
              <YAxis
                type="category"
                dataKey="name"
                tick={{
                  fontSize: 11,
                  fontFamily: theme.typography.fontFamily,
                  fill: "#6B7280",
                }}
                stroke="#E5E7EB"
                width={240}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const p = payload[0].payload as {
                      fullName: string;
                      value: number;
                      pct: number;
                    };
                    return (
                      <div className={classes.tooltip}>
                        <div className={classes.tooltipLabel}>{p.fullName}</div>
                        <div>
                          {p.value.toLocaleString()} ({p.pct.toFixed(1)}%)
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Bar
                dataKey="value"
                fill={theme.colors.primary.main}
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
