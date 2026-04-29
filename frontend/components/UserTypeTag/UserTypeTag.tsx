"use client";

import useClasses from "@/utils/useClasses";
import userTypeTagStyles from "./UserTypeTagStyles";
import { hexToHexa } from "@/utils/functions";
import type { UserRole } from "@/store/slices/auth/thunks";

const rolesColorsMap: Record<UserRole, string> = {
  MANAGER: "#E8674A",
  DOCTOR: "#5B8DB8",
  PATIENT: "#6AAF6A",
};

interface userTypeTagProps {
  userType: UserRole;
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
      {userType.toLowerCase()}
    </div>
  );
}
