"use client";

import { useEffect, useState } from "react";
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
  "/providers": "Doctors",
  "/encounters": "Visits",
};

function capitalize(str: string) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export default function Header() {
  const classes = useClasses(headerStyles, { name: "HeaderStyles" });
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // auth hydrates from localStorage (absent during SSR), so the server always
  // renders the default "MANAGER" tag. Use the real role only after mount to
  // avoid a hydration mismatch on the user tag.
  const realRole = useSelector((s: RootState) => s.auth.user?.role) || "MANAGER";
  const role = mounted ? realRole : "MANAGER";

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
