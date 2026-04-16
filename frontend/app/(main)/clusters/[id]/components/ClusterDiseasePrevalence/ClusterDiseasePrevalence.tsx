"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from "recharts";
import useClasses from "@/utils/useClasses";
import { DiseasePrevalence } from "@/models/generic/clusters";
import { ClusterDiseasePrevalenceStyles } from "./ClusterDiseasePrevalenceStyles";

interface Props {
  prevalence: DiseasePrevalence;
  color: string;
}

export default function ClusterDiseasePrevalence({ prevalence, color }: Props) {
  const classes = useClasses(ClusterDiseasePrevalenceStyles, {
    name: "ClusterDiseasePrevalence",
  });

  const data = [
    { name: "Diabetes", value: prevalence.diabetesPct },
    { name: "Hypertension", value: prevalence.hypertensionPct },
    { name: "Heart Disease", value: prevalence.heartDiseasePct },
    { name: "Cancer", value: prevalence.cancerPct },
    { name: "Respiratory", value: prevalence.respiratoryPct },
    { name: "Mental Health", value: prevalence.mentalHealthPct },
    { name: "Polypharmacy", value: prevalence.polypharmacyPct },
  ];

  return (
    <div className={classes.card}>
      <p className={classes.sectionTitle}>Disease Prevalence</p>
      <div className={classes.chartWrapper}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 5, right: 40, left: 20, bottom: 5 }}
          >
            <CartesianGrid horizontal={false} strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              type="number"
              domain={[0, 100]}
              tick={{ fontSize: 11, fontFamily: '"Inter", sans-serif' }}
              stroke="#6B7280"
              tickFormatter={(v: number) => `${v}%`}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 12, fontFamily: '"Inter", sans-serif' }}
              stroke="#6B7280"
              width={110}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload as { name: string; value: number };
                  return (
                    <div className={classes.tooltip}>
                      <div className={classes.tooltipLabel}>{d.name}</div>
                      <div>{d.value}%</div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="value" fill={color} radius={[0, 4, 4, 0]}>
              <LabelList
                dataKey="value"
                position="right"
                formatter={(v) => `${v}%`}
                fontSize={11}
                fill="#6B7280"
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
