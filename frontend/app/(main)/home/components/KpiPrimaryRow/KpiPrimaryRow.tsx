"use client";

import PeopleOutlinedIcon from "@mui/icons-material/PeopleOutlined";
import MonitorHeartOutlinedIcon from "@mui/icons-material/MonitorHeartOutlined";
import BadgeOutlinedIcon from "@mui/icons-material/BadgeOutlined";
import EventNoteOutlinedIcon from "@mui/icons-material/EventNoteOutlined";
import useClasses from "@/utils/useClasses";
import theme from "@/utils/theme";
import { KpiCards } from "@/models/generic/dashboard";
import { KpiPrimaryRowStyles } from "./KpiPrimaryRowStyles";

interface Props {
  kpis: KpiCards;
}

export default function KpiPrimaryRow({ kpis }: Props) {
  const classes = useClasses(KpiPrimaryRowStyles, { name: "KpiPrimaryRow" });

  const items = [
    {
      key: "totalPatients",
      label: "Total Patients",
      value: kpis.totalPatients.toLocaleString(),
      sub: `${kpis.mortalityRate}% mortality`,
      Icon: PeopleOutlinedIcon,
    },
    {
      key: "mortalityRate",
      label: "Mortality Rate",
      value: `${kpis.mortalityRate}%`,
      sub: null,
      Icon: MonitorHeartOutlinedIcon,
    },
    {
      key: "totalProviders",
      label: "Total Providers",
      value: kpis.totalProviders.toLocaleString(),
      sub: null,
      Icon: BadgeOutlinedIcon,
    },
    {
      key: "totalEncounters",
      label: "Total Encounters",
      value: kpis.totalEncounters.toLocaleString(),
      sub: null,
      Icon: EventNoteOutlinedIcon,
    },
  ];

  return (
    <div className={classes.row}>
      {items.map(({ key, label, value, sub, Icon }) => (
        <div key={key} className={classes.card}>
          <div className={classes.iconRow}>
            <Icon sx={{ color: theme.colors.primary.main, fontSize: "1.3rem" }} />
          </div>
          <p className={classes.label}>{label}</p>
          <p className={classes.value}>{value}</p>
          {sub && <p className={classes.sub}>{sub}</p>}
        </div>
      ))}
    </div>
  );
}
