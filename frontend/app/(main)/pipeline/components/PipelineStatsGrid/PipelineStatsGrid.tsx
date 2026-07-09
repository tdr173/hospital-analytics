"use client";

import Groups3Icon from "@mui/icons-material/Groups3";
import TimelineIcon from "@mui/icons-material/Timeline";
import PeopleOutlinedIcon from "@mui/icons-material/PeopleOutlined";
import MedicationOutlinedIcon from "@mui/icons-material/MedicationOutlined";
import VaccinesOutlinedIcon from "@mui/icons-material/VaccinesOutlined";
import AssignmentOutlinedIcon from "@mui/icons-material/AssignmentOutlined";
import MonitorHeartOutlinedIcon from "@mui/icons-material/MonitorHeartOutlined";
import useClasses from "@/utils/useClasses";
import theme from "@/utils/theme";
import { PipelineOverview } from "@/models/generic/pipeline";
import { PipelineStatsGridStyles } from "./PipelineStatsGridStyles";

interface Props {
  overview: PipelineOverview;
}

export default function PipelineStatsGrid({ overview }: Props) {
  const classes = useClasses(PipelineStatsGridStyles, { name: "PipelineStatsGrid" });

  const { counts } = overview;

  const interpretationItems = [
    {
      key: "clusters",
      label: "Interpreted Clusters",
      value: `${overview.interpretedClusters}/${overview.totalClusters}`,
      Icon: Groups3Icon,
    },
    {
      key: "sequences",
      label: "Interpreted Sequences",
      value: `${overview.interpretedSequences}/${overview.totalSequences}`,
      Icon: TimelineIcon,
    },
  ];

  const countItems = [
    { key: "patients", label: "Patients", value: counts.patients, Icon: PeopleOutlinedIcon },
    { key: "medications", label: "Medications", value: counts.medications, Icon: MedicationOutlinedIcon },
    { key: "procedures", label: "Procedures", value: counts.procedures, Icon: VaccinesOutlinedIcon },
    { key: "careplans", label: "Care Plans", value: counts.careplans, Icon: AssignmentOutlinedIcon },
    { key: "conditions", label: "Conditions", value: counts.conditions, Icon: MonitorHeartOutlinedIcon },
  ];

  return (
    <div className={classes.wrapper}>
      <div className={classes.section}>
        <p className={classes.sectionTitle}>AI Interpretation</p>
        <div className={classes.grid}>
          {interpretationItems.map(({ key, label, value, Icon }) => (
            <div key={key} className={classes.card}>
              <div className={classes.iconRow}>
                <Icon sx={{ color: theme.colors.primary.main, fontSize: "1.3rem" }} />
              </div>
              <p className={classes.label}>{label}</p>
              <p className={classes.value}>{value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className={classes.section}>
        <p className={classes.sectionTitle}>Data Volume</p>
        <div className={classes.grid}>
          {countItems.map(({ key, label, value, Icon }) => (
            <div key={key} className={classes.card}>
              <div className={classes.iconRow}>
                <Icon sx={{ color: theme.colors.primary.main, fontSize: "1.3rem" }} />
              </div>
              <p className={classes.label}>{label}</p>
              <p className={classes.value}>{(value ?? 0).toLocaleString()}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
