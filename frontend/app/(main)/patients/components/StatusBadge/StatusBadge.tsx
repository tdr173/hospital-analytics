"use client";

import useClasses from "@/utils/useClasses";
import { StatusBadgeStyles } from "./StatusBadgeStyles";

interface Props {
  deathdate: string | null;
}

export default function StatusBadge({ deathdate }: Props) {
  const classes = useClasses(StatusBadgeStyles, { name: "StatusBadge" });
  const alive = !deathdate;
  return (
    <span className={alive ? classes.alive : classes.deceased}>
      {alive ? "Alive" : "Deceased"}
    </span>
  );
}
