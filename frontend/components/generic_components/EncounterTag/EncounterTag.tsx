import useClasses from "@/utils/useClasses";
import { EncounterTagStyles } from "./EncounterTagStyles";

interface Props {
  type: string;
}

const LABELS: Record<string, string> = {
  ambulatory: "Ambulatory",
  emergency: "Emergency",
  home: "Home",
  hospice: "Hospice",
  inpatient: "Inpatient",
  outpatient: "Outpatient",
  snf: "SNF",
  urgentcare: "Urgent Care",
  virtual: "Virtual",
  wellness: "Wellness",
};

export default function EncounterTag({ type }: Props) {
  const key = type?.toLowerCase() ?? "other";
  const classes = useClasses(EncounterTagStyles, { name: "EncounterTag" });

  return (
    <span className={`${classes.base} ${classes[key as keyof typeof classes] ?? classes.other}`}>
      {LABELS[key] ?? type}
    </span>
  );
}
