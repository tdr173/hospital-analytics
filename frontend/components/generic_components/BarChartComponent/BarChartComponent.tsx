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
import useClasses from "@/utils/useClasses";
import { BarChartStyles } from "./BarChartStyles";

interface ChartEntry {
  name: string;
  value: number;
  tooltip: string;
}

interface BarChartComponentProps {
  data: ChartEntry[];
  title: string;
  color?: string;
  colors?: string[];
  showLabel?: boolean;
  bottomBorder?: number;
  fillHeight?: boolean;
}

function TruncatedTick({
  x,
  y,
  payload,
  data,
  rotated,
}: {
  x: number;
  y: number;
  payload: { value: string };
  data: ChartEntry[];
  rotated: boolean;
}) {
  const entry = data.find((d) => d.name === payload.value);
  const maxLen = rotated ? 15 : 20;
  const label =
    payload.value.length > maxLen
      ? payload.value.slice(0, maxLen - 2) + "…"
      : payload.value;

  return (
    <g transform={`translate(${x},${y})${rotated ? " rotate(-40)" : ""}`}>
      <title>{entry?.tooltip || payload.value}</title>
      <text
        x={0}
        y={0}
        dy={12}
        textAnchor={rotated ? "end" : "middle"}
        fill="#6B7280"
        fontSize={10}
        fontFamily='"Balsamiq Sans", cursive'
      >
        {label}
      </text>
    </g>
  );
}

export default function BarChartComponent({
  data,
  title,
  color = "#006780",
  colors,
  showLabel = false,
  bottomBorder = 5,
  fillHeight = false,
}: BarChartComponentProps) {
  const classes = useClasses(BarChartStyles, { name: "BarChart" });

  return (
    <div
      className={
        fillHeight ? `${classes.container} ${classes.containerFill}` : classes.container
      }
    >
      {title && <h3 className={classes.title}>{title}</h3>}
      <ResponsiveContainer width="100%" height={fillHeight ? "100%" : 300}>
        <BarChart
          data={data}
          margin={{
            top: 10,
            right: 20,
            left: 0,
            bottom: bottomBorder,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey="name"
            tick={
              showLabel
                ? (props: any) => (
                    <TruncatedTick
                      {...props}
                      data={data}
                      rotated={data.length > 6}
                    />
                  )
                : data.length <= 6
                  ? { fontSize: 12, fontFamily: '"Inter", sans-serif' }
                  : false
            }
            tickLine={showLabel || data.length <= 6}
            stroke="#6B7280"
            interval={0}
            height={showLabel && data.length > 6 ? 80 : showLabel ? 40 : 30}
          />
          <YAxis
            tick={{ fontSize: 12, fontFamily: '"Inter", sans-serif' }}
            stroke="#6B7280"
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const entry = payload[0].payload as ChartEntry;
                return (
                  <div className={classes.tooltip}>
                    <div className={classes.tooltipName}>{entry.name}</div>
                    <div className={classes.tooltipValue}>
                      Count: {entry.value.toLocaleString()}
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="value" fill={color} radius={[4, 4, 0, 0]}>
            {colors
              ? data.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={colors[index % colors.length]}
                  />
                ))
              : null}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
