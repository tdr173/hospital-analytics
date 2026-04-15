"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useRouter } from "next/navigation";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from "recharts";

import { RootState, AppDispatch } from "@/store";
import { fetchDashboard } from "@/store/slices/dashboard/thunks";
import { DashboardData, RecentEncounterItem } from "@/models/generic/dashboard";

import useClasses from "@/utils/useClasses";
import { HomePageStyles } from "./styles";
import theme from "@/utils/theme";
import { formatDate } from "@/utils/functions";
import PieChartComponent from "@/components/generic_components/PieChartComponent/PieChartComponent";

import PeopleOutlinedIcon from "@mui/icons-material/PeopleOutlined";
import FavoriteBorderOutlinedIcon from "@mui/icons-material/FavoriteBorderOutlined";
import BadgeOutlinedIcon from "@mui/icons-material/BadgeOutlined";
import AccountBalanceOutlinedIcon from "@mui/icons-material/AccountBalanceOutlined";
import EventNoteOutlinedIcon from "@mui/icons-material/EventNoteOutlined";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const ENCOUNTER_CLASS_COLORS: Record<string, string> = {
  emergency: "#ef4444",
  ambulatory: theme.colors.primary.main,
  inpatient: "#8b5cf6",
  wellness: "#10b981",
  urgentcare: "#f59e0b",
};

const DEFAULT_PIE_COLORS = [
  theme.colors.primary.main,
  "#028fb0",
  "#6cd3f7",
  "#515f74",
  "#b7eaff",
];

const GENDER_COLORS: Record<string, string> = {
  M: "#2563eb",
  F: "#9333ea",
};

const KPI_CONFIG = [
  {
    key: "totalPatients" as const,
    label: "Total Patients",
    sub: (d: DashboardData) => `${d.kpis.activePatients.toLocaleString()} active`,
    Icon: PeopleOutlinedIcon,
  },
  {
    key: "activePatients" as const,
    label: "Active Patients",
    sub: null,
    Icon: FavoriteBorderOutlinedIcon,
  },
  {
    key: "totalProviders" as const,
    label: "Total Providers",
    sub: null,
    Icon: BadgeOutlinedIcon,
  },
  {
    key: "totalOrganizations" as const,
    label: "Organizations",
    sub: null,
    Icon: AccountBalanceOutlinedIcon,
  },
  {
    key: "totalEncounters" as const,
    label: "Total Encounters",
    sub: null,
    Icon: EventNoteOutlinedIcon,
  },
];

function formatMonth(m: string) {
  const [year, month] = m.split("-");
  const d = new Date(Number(year), Number(month) - 1);
  return d.toLocaleString("en", { month: "short", year: "2-digit" });
}

function KpiCards({ data, classes }: { data: DashboardData; classes: any }) {
  return (
    <div className={classes.kpiRow}>
      {KPI_CONFIG.map(({ key, label, sub, Icon }) => (
        <div key={key} className={classes.kpiCard}>
          <div className={classes.kpiIconRow}>
            <Icon sx={{ color: theme.colors.primary.main, fontSize: "1.3rem" }} />
          </div>
          <p className={classes.kpiLabel}>{label}</p>
          <p className={classes.kpiValue}>{data.kpis[key].toLocaleString()}</p>
          {sub && <p className={classes.kpiSub}>{sub(data)}</p>}
        </div>
      ))}
    </div>
  );
}

function MonthlyChart({ data, classes }: { data: DashboardData["monthlyEncounters"]; classes: any }) {
  const chartData = data.map((d) => ({ name: formatMonth(d.month), value: d.count }));
  return (
    <div className={classes.card}>
      <p className={classes.cardTitle}>Encounter Volume — Last 12 Months</p>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fontFamily: theme.typography.fontFamily, fill: "#6B7280" }}
            stroke="#E5E7EB"
          />
          <YAxis
            tick={{ fontSize: 11, fontFamily: theme.typography.fontFamily, fill: "#6B7280" }}
            stroke="#E5E7EB"
            width={45}
          />
          <Tooltip
            contentStyle={{
              fontFamily: theme.typography.fontFamily,
              fontSize: "0.8rem",
              borderRadius: theme.borderRadius.md,
              border: `1px solid ${theme.colors.border.main}`,
              boxShadow: theme.shadows.md,
            }}
            formatter={(v: number) => [v.toLocaleString(), "Encounters"]}
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
    </div>
  );
}

function EncounterClassChart({ data, classes }: { data: DashboardData["encounterByClass"]; classes: any }) {
  const pieData = data.map((d) => ({
    name: d.encounterClass.charAt(0).toUpperCase() + d.encounterClass.slice(1),
    value: d.count,
    tooltip: `${d.encounterClass}: ${d.count.toLocaleString()}`,
  }));
  const colors = data.map((d) => ENCOUNTER_CLASS_COLORS[d.encounterClass] ?? theme.colors.secondary.main);
  return (
    <div className={classes.card}>
      <p className={classes.cardTitle}>Encounters by Class</p>
      <PieChartComponent data={pieData} title="" colors={colors} />
    </div>
  );
}

function DemographicsCard({ data, classes }: { data: DashboardData; classes: any }) {
  const genderData = data.genderDistribution.map((d) => ({
    name: d.gender === "M" ? "Male" : d.gender === "F" ? "Female" : d.gender,
    value: d.count,
    color: GENDER_COLORS[d.gender] ?? theme.colors.primary.main,
  }));

  const ageData = data.ageGroups.map((d) => ({
    name: d.ageGroup,
    value: d.count,
  }));

  return (
    <div className={classes.demographicsCard}>
      <div>
        <p className={classes.demographicsSectionTitle}>Gender</p>
        <ResponsiveContainer width="100%" height={80}>
          <BarChart data={genderData} layout="vertical" margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 11, fontFamily: theme.typography.fontFamily, fill: "#6B7280" }}
              stroke="none"
              width={42}
            />
            <Tooltip
              contentStyle={{
                fontFamily: theme.typography.fontFamily,
                fontSize: "0.8rem",
                borderRadius: theme.borderRadius.md,
                border: `1px solid ${theme.colors.border.main}`,
              }}
              formatter={(v: number) => [v.toLocaleString(), "Patients"]}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {genderData.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div>
        <p className={classes.demographicsSectionTitle}>Age Groups</p>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={ageData} layout="vertical" margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 11, fontFamily: theme.typography.fontFamily, fill: "#6B7280" }}
              stroke="none"
              width={80}
            />
            <Tooltip
              contentStyle={{
                fontFamily: theme.typography.fontFamily,
                fontSize: "0.8rem",
                borderRadius: theme.borderRadius.md,
                border: `1px solid ${theme.colors.border.main}`,
              }}
              formatter={(v: number) => [v.toLocaleString(), "Patients"]}
            />
            <Bar dataKey="value" fill={theme.colors.primary.main} radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function RecentEncounters({
  data,
  classes,
  onPatientClick,
}: {
  data: RecentEncounterItem[];
  classes: any;
  onPatientClick: (id: string) => void;
}) {
  return (
    <div className={classes.recentCard}>
      <p className={classes.cardTitle}>Recent Encounters</p>
      <div className={`${classes.recentGrid} ${classes.recentHeader}`}>
        <div>Patient</div>
        <div>Provider</div>
        <div>Organization</div>
        <div>Date</div>
        <div>Class</div>
        <div>Description</div>
      </div>
      {data.map((r, i) => (
        <div
          key={r.encounterId}
          className={`${classes.recentGrid} ${i % 2 === 0 ? classes.recentRowEven : classes.recentRowOdd}`}
        >
          <div className={classes.recentClickable} onClick={() => onPatientClick(r.patientId)}>
            {r.patientName}
          </div>
          <div className={classes.recentSecondary}>{r.providerName}</div>
          <div className={classes.recentSecondary}>{r.organizationName ?? "—"}</div>
          <div className={classes.recentSecondary}>{formatDate(r.startDate)}</div>
          <div>
            <span className={classes.encounterTypeBadge}>
              {r.encounterClass}
            </span>
          </div>
          <div className={classes.recentSecondary}>{r.description}</div>
        </div>
      ))}
    </div>
  );
}

export default function HomePage() {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const classes = useClasses(HomePageStyles, { name: "HomePage" });

  const { data, loading, error } = useSelector((state: RootState) => state.dashboard);

  useEffect(() => {
    if (!data) dispatch(fetchDashboard());
  }, []);

  if (loading) return <div className={classes.loading}>Loading dashboard...</div>;
  if (error) return <div className={classes.error}>{error}</div>;
  if (!data) return null;

  return (
    <div className={classes.container}>
      <KpiCards data={data} classes={classes} />

      <div className={classes.chartRow}>
        <MonthlyChart data={data.monthlyEncounters} classes={classes} />
        <EncounterClassChart data={data.encounterByClass} classes={classes} />
      </div>

      <div className={classes.bottomRow}>
        <DemographicsCard data={data} classes={classes} />
        <RecentEncounters
          data={data.recentEncounters}
          classes={classes}
          onPatientClick={(id) => router.push(`/patients/${id}`)}
        />
      </div>
    </div>
  );
}
