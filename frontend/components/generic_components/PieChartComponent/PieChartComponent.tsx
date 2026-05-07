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

export default function PieChartComponent({
  data,
  title,
  colors = DEFAULT_COLORS,
}: PieChartComponentProps) {
  const classes = useClasses(PieChartStyles, { name: "PieChart" });

  return (
    <div className={classes.container}>
      <h3 className={classes.title}>{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="45%"
            outerRadius={100}
            dataKey="value"
            nameKey="name"
            stroke="#ffffff"
            strokeWidth={2}
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
