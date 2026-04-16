"use client";

import useClasses from "@/utils/useClasses";
import { GenderBadgeStyles } from "./GenderBadgeStyles";

interface Props {
  gender: string | null;
}

export default function GenderBadge({ gender }: Props) {
  const classes = useClasses(GenderBadgeStyles, { name: "OrgGenderBadge" });
  if (!gender) return <span className={classes.empty}>-</span>;
  const isFemale = gender === "F";
  return (
    <span className={isFemale ? classes.female : classes.male}>
      {isFemale ? "F" : "M"}
    </span>
  );
}
