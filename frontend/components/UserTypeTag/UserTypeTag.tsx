"use client";

import useClasses from "@/utils/useClasses";
import userTypeTagStyles from "./UserTypeTagStyles";
import { hexToHexa } from "@/utils/functions";

const rolesColorsMap: Record<string, string> = {
  admin: "#E8674A",
  doctor: "#5B8DB8",
  patient: "#6AAF6A",
};

interface userTypeTagProps {
  userType: "admin" | "doctor" | "patient";
}

export default function UserTypeTag({ userType }: userTypeTagProps) {
  const classes = useClasses(userTypeTagStyles, { name: "UserTypeTagStyles" });
  const color = rolesColorsMap[userType];

  return (
    <div
      className={classes.tagContainer}
      style={{
        backgroundColor: hexToHexa(color, 0.12),
        color: color,
      }}
    >
      <span className={classes.dot} style={{ backgroundColor: color }} />
      {userType}
    </div>
  );
}
