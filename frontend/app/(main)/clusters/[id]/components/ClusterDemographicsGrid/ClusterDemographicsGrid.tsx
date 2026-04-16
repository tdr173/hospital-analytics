"use client";

import {
  PieChart,
  Pie,
  Cell,
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
import { ClusterDemographics } from "@/models/generic/clusters";
import { ClusterDemographicsGridStyles } from "./ClusterDemographicsGridStyles";

interface Props {
  demographics: ClusterDemographics;
  color: string;
}

const MARITAL_LABELS: Record<string, string> = {
  M: "Married",
  S: "Single",
  D: "Divorced",
  W: "Widowed",
};

const SMOKING_LABELS: Record<string, string> = {
  current: "Current",
  former: "Former",
  never: "Never",
};

const BURDEN_LABELS: Record<string, string> = {
  none: "None",
  low: "Low",
  moderate: "Moderate",
  high: "High",
  very_high: "Very High",
};

const BURDEN_ORDER = ["none", "low", "moderate", "high", "very_high"];
const MARITAL_ORDER = ["M", "S", "D", "W"];
const SMOKING_ORDER = ["current", "former", "never"];

const BURDEN_COLORS = ["#16A34A", "#84CC16", "#EAB308", "#F97316", "#DC2626"];

function mapDistribution(
  dist: Record<string, number>,
  labels: Record<string, string>,
  order: string[],
) {
  return order.map((key) => ({
    name: labels[key] ?? key,
    value: dist[key] ?? 0,
  }));
}

export default function ClusterDemographicsGrid({ demographics, color }: Props) {
  const classes = useClasses(ClusterDemographicsGridStyles, {
    name: "ClusterDemographicsGrid",
  });

  const femalePct = demographics.gender.F ?? 0;
  const malePct = demographics.gender.M ?? 0;
  const genderData = [
    { name: "Female", value: femalePct, fill: theme.colors.gender.female },
    { name: "Male", value: malePct, fill: theme.colors.gender.male },
  ];

  const maritalData = mapDistribution(demographics.marital, MARITAL_LABELS, MARITAL_ORDER);
  const smokingData = mapDistribution(demographics.smoking, SMOKING_LABELS, SMOKING_ORDER);
  const burdenData = mapDistribution(demographics.conditionBurden, BURDEN_LABELS, BURDEN_ORDER);

  const renderBar = (
    data: { name: string; value: number }[],
    colors?: string[],
  ) => (
    <div className={classes.chartWrapper}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fontFamily: '"Inter", sans-serif' }}
            stroke="#6B7280"
            interval={0}
          />
          <YAxis
            tick={{ fontSize: 11, fontFamily: '"Inter", sans-serif' }}
            stroke="#6B7280"
            tickFormatter={(v: number) => `${v}%`}
            domain={[0, 100]}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const d = payload[0].payload as { name: string; value: number };
                return (
                  <div className={classes.tooltip}>
                    <div style={{ fontWeight: 600 }}>{d.name}</div>
                    <div>{d.value}%</div>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="value" fill={color} radius={[4, 4, 0, 0]}>
            {colors &&
              data.map((d, i) => <Cell key={d.name} fill={colors[i] ?? color} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );

  return (
    <div className={classes.card}>
      <p className={classes.sectionTitle}>Demographics</p>
      <div className={classes.grid}>
        <div className={classes.tile}>
          <p className={classes.tileTitle}>Gender</p>
          <div className={classes.donutCenter}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={genderData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={2}
                  stroke="none"
                >
                  {genderData.map((d) => (
                    <Cell key={d.name} fill={d.fill} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const p = payload[0] as unknown as {
                        name: string;
                        value: number;
                      };
                      return (
                        <div className={classes.tooltip}>
                          <div style={{ fontWeight: 600 }}>{p.name}</div>
                          <div>{p.value}%</div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className={classes.donutCenterLabel}>
              <div className={classes.donutCenterValue} style={{ color }}>
                {femalePct}%
              </div>
              <div className={classes.donutCenterCaption}>Female</div>
            </div>
          </div>
          <div className={classes.legendRow}>
            {genderData.map((d) => (
              <span key={d.name} className={classes.legendItem}>
                <span className={classes.legendDot} style={{ backgroundColor: d.fill }} />
                {d.name}: {d.value}%
              </span>
            ))}
          </div>
        </div>

        <div className={classes.tile}>
          <p className={classes.tileTitle}>Marital Status</p>
          {renderBar(maritalData)}
        </div>

        <div className={classes.tile}>
          <p className={classes.tileTitle}>Smoking Status</p>
          {renderBar(smokingData)}
        </div>

        <div className={classes.tile}>
          <p className={classes.tileTitle}>Condition Burden</p>
          {renderBar(burdenData, BURDEN_COLORS)}
        </div>
      </div>
    </div>
  );
}
