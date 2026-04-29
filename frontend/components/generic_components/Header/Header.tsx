"use client";

import { useSelector } from "react-redux";
import useClasses from "@/utils/useClasses";
import headerStyles from "./HeaderStyles";
import UserTypeTag from "../../UserTypeTag/UserTypeTag";
import { usePathname } from "next/navigation";
import type { RootState } from "@/store";

const ROUTE_TITLES: Record<string, string> = {
  "/statistics": "Statistics",
  "/clusters/summaries": "Patient Groups",
  "/clusters/statistics": "Group Statistics",
  "/clusters": "Patient Groups",
  "/register-user": "Add User",
};

function capitalize(str: string) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export default function Header() {
  const classes = useClasses(headerStyles, { name: "HeaderStyles" });
  const pathname = usePathname();
  const role = useSelector((s: RootState) => s.auth.user?.role) || "MANAGER";

  const matchedKey = Object.keys(ROUTE_TITLES)
    .sort((a, b) => b.length - a.length)
    .find((key) => pathname.startsWith(key));

  const title = matchedKey
    ? ROUTE_TITLES[matchedKey]
    : pathname.split("/").filter(Boolean).map(capitalize).join(" - ");

  return (
    <div className={classes.headerContainer}>
      <span className={classes.pageTitle}>{title}</span>
      <UserTypeTag userType={role} />
    </div>
  );
}
