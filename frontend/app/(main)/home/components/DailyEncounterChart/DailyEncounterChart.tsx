"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import useClasses from "@/utils/useClasses";
import theme from "@/utils/theme";
import { DailyEncounterItem } from "@/models/generic/dashboard";
import { DailyEncounterChartStyles } from "./DailyEncounterChartStyles";
import { formatDay } from "../../utils/formatters";

interface Props {
  data: DailyEncounterItem[];
}

export default function DailyEncounterChart({ data }: Props) {
  const classes = useClasses(DailyEncounterChartStyles, { name: "DailyEncounterChart" });
  const chartData = data.map((d) => ({ name: formatDay(d.day), value: d.count }));

  return (
    <div className={classes.card}>
      <p className={classes.title}>Encounter Volume — Last 30 Days</p>
      {chartData.length === 0 ? (
        <div className={classes.empty}>No encounters in the last 30 days.</div>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fontFamily: theme.typography.fontFamily, fill: "#6B7280" }}
              stroke="#E5E7EB"
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 11, fontFamily: theme.typography.fontFamily, fill: "#6B7280" }}
              stroke="#E5E7EB"
              width={45}
            />
            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  const v = payload[0].value as number;
                  return (
                    <div className={classes.tooltip}>
                      <div className={classes.tooltipLabel}>{label}</div>
                      <div>{v.toLocaleString()} encounters</div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={theme.colors.primary.main}
              strokeWidth={2}
              dot={{ r: 3, fill: theme.colors.primary.main }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
