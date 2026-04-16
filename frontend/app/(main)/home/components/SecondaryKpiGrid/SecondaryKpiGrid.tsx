"use client";

import LocalHospitalOutlinedIcon from "@mui/icons-material/LocalHospitalOutlined";
import AssignmentOutlinedIcon from "@mui/icons-material/AssignmentOutlined";
import MedicalServicesOutlinedIcon from "@mui/icons-material/MedicalServicesOutlined";
import AccountBalanceOutlinedIcon from "@mui/icons-material/AccountBalanceOutlined";
import useClasses from "@/utils/useClasses";
import theme from "@/utils/theme";
import { KpiCards } from "@/models/generic/dashboard";
import { SecondaryKpiGridStyles } from "./SecondaryKpiGridStyles";

interface Props {
  kpis: KpiCards;
}

export default function SecondaryKpiGrid({ kpis }: Props) {
  const classes = useClasses(SecondaryKpiGridStyles, { name: "SecondaryKpiGrid" });

  const items = [
    { key: "totalConditions", label: "Total Conditions", value: kpis.totalConditions, Icon: LocalHospitalOutlinedIcon },
    { key: "totalCareplans", label: "Total Careplans", value: kpis.totalCareplans, Icon: AssignmentOutlinedIcon },
    { key: "totalProcedures", label: "Total Procedures", value: kpis.totalProcedures, Icon: MedicalServicesOutlinedIcon },
    { key: "totalOrganizations", label: "Total Organizations", value: kpis.totalOrganizations, Icon: AccountBalanceOutlinedIcon },
  ];

  return (
    <div className={classes.grid}>
      {items.map(({ key, label, value, Icon }) => (
        <div key={key} className={classes.card}>
          <div className={classes.iconRow}>
            <Icon sx={{ color: theme.colors.primary.main, fontSize: "1.15rem" }} />
            <p className={classes.label}>{label}</p>
          </div>
          <p className={classes.value}>{value.toLocaleString()}</p>
        </div>
      ))}
    </div>
  );
}
