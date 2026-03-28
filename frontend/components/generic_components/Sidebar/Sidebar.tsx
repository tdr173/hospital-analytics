"use client";

import useClasses from "@/utils/useClasses";
import sidebarStyles from "./SidebarStyles";
import UserTypeTag from "../../UserTypeTag/UserTypeTag";
import AddIcon from "@mui/icons-material/Add";

import AnalyticsIcon from "@mui/icons-material/Analytics";
import DashboardIcon from "@mui/icons-material/Dashboard";

import React from "react";
import { useRouter, usePathname } from "next/navigation";

const sidebarElements = [
  // { name: "Home", icon: DashboardIcon, forward: "/home" },
  // { name: "Dashboard", icon: DashboardIcon, forward: "/dashboard" },
  {
    name: "Dataset Statistics",
    icon: AnalyticsIcon,
    forward: "/statistics",
  },
];

export default function Sidebar() {
  const classes = useClasses(sidebarStyles, { name: "SidebarStyles" });

  const router = useRouter();
  const pathname = usePathname();

  const isRouteActive = (path: string) => {
    return pathname.includes(path);
  };

  const sidebarElement = (
    key: number,
    Icon: React.ElementType,
    name: string,
    forward: string,
  ) => {
    return (
      <div
        key={key}
        className={classes.sidebarElement}
        style={
          isRouteActive(forward)
            ? {
                backgroundColor: "rgba(183, 234, 255, 0.2)",
                color: "#ffffff",
              }
            : undefined
        }
        onClick={() => router.push(forward)}
      >
        <Icon />
        {name}
      </div>
    );
  };

  return (
    <div className={classes.sidebarContainer}>
      <div className={classes.sidebarHeader}>
        <div className={classes.headerInfo}>
          <div className={classes.appNameRow}>
            <AddIcon
              sx={{
                color: "#ffffff",
                fontSize: "32px",
                fontWeight: "bold",
                stroke: "#ffffff",
                strokeWidth: 2,
              }}
            />
            <span className={classes.appName}>HospitAI</span>
          </div>
          <div className={classes.appNameRow} style={{ marginTop: 4 }}>
            <UserTypeTag userType="admin" />
          </div>
        </div>
      </div>
      <div className={classes.sidebarContent}>
        {sidebarElements.map((element, index) =>
          sidebarElement(index, element.icon, element.name, element.forward),
        )}
      </div>
    </div>
  );
}
