import { PatientDetail } from "@/models/generic/patients";
import theme from "@/utils/theme";
import { formatDate, clearName } from "@/utils/functions";
import manImage from "@/public/man_icon.svg";
import womanImage from "@/public/woman_icon.svg";

const MARITAL_LABELS: Record<string, string> = {
  M: "Married",
  S: "Single",
  D: "Divorced",
  W: "Widowed",
};

const GENDER_LABELS: Record<string, string> = {
  M: "Male",
  F: "Female",
};

export default function IdentityCard({
  patient,
  classes,
}: {
  patient: PatientDetail;
  classes: any;
}) {
  if (!patient) return null;

  const alive = !patient.deathdate;

  const details = [
    { label: "Age", value: patient?.age ? `${patient.age} years` : null },
    { label: "Gender", value: GENDER_LABELS[patient?.gender ?? ""] },
    { label: "Date of Birth", value: formatDate(patient?.birthdate) },
    { label: "Race", value: patient?.race },
    { label: "Ethnicity", value: patient?.ethnicity },
    {
      label: "Marital Status",
      value: MARITAL_LABELS[patient?.marital ?? ""] || patient?.marital,
    },
    { label: "City", value: patient?.city },
  ];

  return (
    <div
      className={classes.identityCard}
      style={{
        borderLeft: `4px solid ${patient.clusterColor ?? theme.colors.primary.main}`,
      }}
    >
      <div className={classes.imageBlock}>
        <img
          src={patient.gender === "M" ? manImage.src : womanImage.src}
          alt={patient.gender === "M" ? "Man Icon" : "Woman Icon"}
          className={classes.avatarImage}
        />
      </div>
      <div className={classes.nameBlock}>
        <p className={classes.profileLabel}>Patient Profile</p>
        <h1 className={classes.patientFullName}>
          {clearName(patient.firstName, patient.lastName) || "Unknown Name"}
        </h1>
        <div className={classes.badgesRow}>
          <span
            className={
              alive ? classes.idStatusBadgeAlive : classes.idStatusBadgeDeceased
            }
          >
            {alive ? "Alive" : `Deceased · ${formatDate(patient.deathdate)}`}
          </span>
          {patient.clusterColor && patient.clusterTitle && (
            <span
              className={classes.idClusterBadge}
              style={{
                color: patient.clusterColor,
                backgroundColor: `${patient.clusterColor}18`,
              }}
            >
              <span
                className={classes.idClusterBadgeDot}
                style={{ backgroundColor: patient.clusterColor }}
              />
              {patient.clusterTitle}
            </span>
          )}
        </div>
      </div>

      <div className={classes.detailsGrid}>
        {details.map(({ label, value }) => (
          <div key={label}>
            <p className={classes.detailLabel}>{label}</p>
            <p className={classes.detailValue}>{value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
