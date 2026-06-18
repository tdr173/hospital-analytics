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
import { formatDay, formatMonth } from "../../utils/formatters";

interface Props {
  data: DailyEncounterItem[];
  title?: string;
  monthly?: boolean;
  hideXLabels?: boolean;
}

export default function DailyEncounterChart({
  data,
  title,
  monthly,
  hideXLabels,
}: Props) {
  const classes = useClasses(DailyEncounterChartStyles, {
    name: "DailyEncounterChart",
  });
  const chartData = data.map((d) => ({
    name: monthly ? formatMonth(d.day) : formatDay(d.day),
    value: d.count,
  }));

  return (
    <div className={classes.card}>
      <p className={classes.title}>{title ?? "Visit Volume"}</p>
      {chartData.length === 0 ? (
        <div className={classes.empty}>No visits recorded in this period.</div>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <LineChart
            data={chartData}
            margin={{ top: 4, right: 16, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="name"
              tick={
                hideXLabels
                  ? false
                  : {
                      fontSize: 11,
                      fontFamily: theme.typography.fontFamily,
                      fill: "#6B7280",
                    }
              }
              stroke="#E5E7EB"
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{
                fontSize: 11,
                fontFamily: theme.typography.fontFamily,
                fill: "#6B7280",
              }}
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
                      <div>{v.toLocaleString()} visits</div>
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
