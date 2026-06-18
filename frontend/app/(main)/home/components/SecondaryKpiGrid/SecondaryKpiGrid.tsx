"use client";

import LocalHospitalOutlinedIcon from "@mui/icons-material/LocalHospitalOutlined";
import AssignmentOutlinedIcon from "@mui/icons-material/AssignmentOutlined";
import MedicalServicesOutlinedIcon from "@mui/icons-material/MedicalServicesOutlined";
import AccountBalanceOutlinedIcon from "@mui/icons-material/AccountBalanceOutlined";
import TrendingUpOutlinedIcon from "@mui/icons-material/TrendingUpOutlined";
import AssignmentTurnedInOutlinedIcon from "@mui/icons-material/AssignmentTurnedInOutlined";
import PersonAddAlt1OutlinedIcon from "@mui/icons-material/PersonAddAlt1Outlined";
import CakeOutlinedIcon from "@mui/icons-material/CakeOutlined";
import useClasses from "@/utils/useClasses";
import theme from "@/utils/theme";
import { KpiCards } from "@/models/generic/dashboard";
import { SecondaryKpiGridStyles } from "./SecondaryKpiGridStyles";

interface Props {
  kpis: KpiCards;
  periodLabel?: string;
}

export default function SecondaryKpiGrid({ kpis, periodLabel }: Props) {
  const classes = useClasses(SecondaryKpiGridStyles, { name: "SecondaryKpiGrid" });

  const items = [
    { key: "totalConditions", label: "Total Conditions", value: kpis.totalConditions.toLocaleString(), Icon: LocalHospitalOutlinedIcon },
    { key: "totalCareplans", label: "Total Care Plans", value: kpis.totalCareplans.toLocaleString(), Icon: AssignmentOutlinedIcon },
    { key: "totalProcedures", label: "Total Procedures", value: kpis.totalProcedures.toLocaleString(), Icon: MedicalServicesOutlinedIcon },
    { key: "totalOrganizations", label: "Total Facilities", value: kpis.totalOrganizations.toLocaleString(), Icon: AccountBalanceOutlinedIcon },
    { key: "avgEncountersPerPatient", label: "Avg Visits / Patient", value: kpis.avgEncountersPerPatient.toFixed(2), Icon: TrendingUpOutlinedIcon },
    { key: "activeCareplans", label: "Active Care Plans", value: kpis.activeCareplans.toLocaleString(), Icon: AssignmentTurnedInOutlinedIcon },
    { key: "newPatientsInPeriod", label: `New Patients (${periodLabel ?? "Period"})`, value: kpis.newPatientsInPeriod.toLocaleString(), Icon: PersonAddAlt1OutlinedIcon },
    { key: "avgPatientAge", label: "Avg Patient Age", value: `${kpis.avgPatientAge.toFixed(1)} yrs`, Icon: CakeOutlinedIcon },
  ];

  return (
    <div className={classes.grid}>
      {items.map(({ key, label, value, Icon }) => (
        <div key={key} className={classes.card}>
          <div className={classes.iconRow}>
            <Icon sx={{ color: theme.colors.primary.main, fontSize: "1.15rem" }} />
            <p className={classes.label}>{label}</p>
          </div>
          <p className={classes.value}>{value}</p>
        </div>
      ))}
    </div>
  );
}
