"use client";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import useClasses from "@/utils/useClasses";
import theme from "@/utils/theme";
import { PieChartStyles } from "./PieChartStyles";

interface ChartEntry {
  name: string;
  value: number;
  tooltip: string;
}

interface PieChartComponentProps {
  data: ChartEntry[];
  title: string;
  colors?: string[];
}

const DEFAULT_COLORS = theme.colors.charts.defaultPalette;

const RADIAN = Math.PI / 180;
const LABEL_THRESHOLD = 0.02;

interface PieLabelProps {
  cx: number;
  cy: number;
  midAngle: number;
  outerRadius: number;
  percent: number;
  value: number;
  index: number;
}

export default function PieChartComponent({
  data,
  title,
  colors = DEFAULT_COLORS,
}: PieChartComponentProps) {
  const classes = useClasses(PieChartStyles, { name: "PieChart" });

  const renderLabel = (props: PieLabelProps) => {
    const { cx, cy, midAngle, outerRadius, percent, value, index } = props;
    if (percent < LABEL_THRESHOLD) return null;

    const cos = Math.cos(-RADIAN * midAngle);
    const sin = Math.sin(-RADIAN * midAngle);
    const sx = cx + outerRadius * cos;
    const sy = cy + outerRadius * sin;
    const mx = cx + (outerRadius + 26) * cos;
    const my = cy + (outerRadius + 26) * sin;
    const onRight = cos >= 0;
    const ex = mx + (onRight ? 1 : -1) * 30;
    const ey = my;
    const color = colors[index % colors.length];

    return (
      <g>
        <polyline
          points={`${sx},${sy} ${mx},${my} ${ex},${ey}`}
          stroke={color}
          strokeWidth={1.5}
          fill="none"
        />
        <text
          x={ex + (onRight ? 1 : -1) * 6}
          y={ey}
          textAnchor={onRight ? "start" : "end"}
          dominantBaseline="central"
          fill={theme.colors.text.primary}
          fontFamily={theme.typography.fontFamily}
          fontSize={13}
          fontWeight={500}
        >
          {`${(percent * 100).toFixed(0)}% (${value.toLocaleString()})`}
        </text>
      </g>
    );
  };

  return (
    <div className={classes.container}>
      <h3 className={classes.title}>{title}</h3>
      <ResponsiveContainer width="100%" height={380}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="45%"
            outerRadius={110}
            dataKey="value"
            nameKey="name"
            stroke="#ffffff"
            strokeWidth={2}
            labelLine={false}
            label={renderLabel}
          >
            {data.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={colors[index % colors.length]}
              />
            ))}
          </Pie>
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const entry = payload[0].payload as ChartEntry;
                return <div className={classes.tooltip}>{entry.tooltip}</div>;
              }
              return null;
            }}
          />
          <Legend
            wrapperStyle={{
              fontFamily: '"Inter", sans-serif',
              fontSize: "12px",
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
