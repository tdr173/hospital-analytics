"use client";

import useClasses from "@/utils/useClasses";
import sidebarStyles from "./SidebarStyles";
import AddIcon from "@mui/icons-material/Add";
import LogoutIcon from "@mui/icons-material/Logout";
import StyledButton from "../StyledButton/StyledButton";

import HomeOutlinedIcon from "@mui/icons-material/HomeOutlined";
import AnalyticsIcon from "@mui/icons-material/Analytics";
import Groups3Icon from "@mui/icons-material/Groups3";
import GroupIcon from "@mui/icons-material/Group";
import BadgeOutlinedIcon from "@mui/icons-material/BadgeOutlined";
import EventNoteOutlinedIcon from "@mui/icons-material/EventNoteOutlined";
import TimelineIcon from "@mui/icons-material/Timeline";
import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";

import React, { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useDispatch, useSelector } from "react-redux";
import { logout } from "@/store/slices/auth/auth-slice";
import type { AppDispatch, RootState } from "@/store";
import type { UserRole } from "@/store/slices/auth/thunks";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

type SidebarElement = {
  name: string;
  icon: React.ElementType;
  forward: string;
  allowedRoles: UserRole[];
  labelByRole?: Partial<Record<UserRole, string>>;
};

const sidebarElements: SidebarElement[] = [
  {
    name: "Home",
    icon: HomeOutlinedIcon,
    forward: "/home",
    allowedRoles: ["MANAGER", "DOCTOR", "PATIENT"],
  },
  {
    name: "Statistics",
    icon: AnalyticsIcon,
    forward: "/statistics",
    allowedRoles: ["MANAGER"],
  },
  {
    name: "Patient Groups",
    icon: Groups3Icon,
    forward: "/clusters",
    allowedRoles: ["MANAGER", "DOCTOR"],
  },
  {
    name: "Care Sequences",
    icon: TimelineIcon,
    forward: "/sequences",
    allowedRoles: ["MANAGER", "DOCTOR"],
  },
  {
    name: "Patients",
    icon: GroupIcon,
    forward: "/patients",
    allowedRoles: ["MANAGER", "DOCTOR"],
  },
  {
    name: "Visits",
    icon: EventNoteOutlinedIcon,
    forward: "/encounters",
    allowedRoles: ["MANAGER", "DOCTOR", "PATIENT"],
    labelByRole: { PATIENT: "My Visits" },
  },
  {
    name: "Doctors",
    icon: BadgeOutlinedIcon,
    forward: "/providers",
    allowedRoles: ["MANAGER"],
  },
  {
    name: "Pipeline",
    icon: AccountTreeOutlinedIcon,
    forward: "/pipeline",
    allowedRoles: ["MANAGER"],
  },
];

export default function Sidebar() {
  const classes = useClasses(sidebarStyles, { name: "SidebarStyles" });
  const [mounted, setMounted] = useState(false);

  const router = useRouter();
  const pathname = usePathname();
  const dispatch = useAppDispatch();
  // The store hydrates auth from localStorage, which is absent during SSR.
  // So the server always renders with the default "MANAGER" role; if we use
  // the real client-side role on the first render, the menus differ and React
  // throws a hydration mismatch (which tears down & regenerates this whole
  // layout subtree). Gate the real role behind `mounted` so the first client
  // render matches the server, then switch to the real role after mount.
  const realRole = useSelector((s: RootState) => s.auth.user?.role) || "MANAGER";
  const role = mounted ? realRole : "MANAGER";
  const visibleElements = sidebarElements.filter((el) => el.allowedRoles.includes(role));

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleLogout = () => {
    dispatch(logout());
    router.push("/login");
  };

  const isRouteActive = (path: string) => {
    return pathname.startsWith(path);
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
        </div>
      </div>
      <div className={classes.sidebarContent}>
        {visibleElements.map((element, index) =>
          sidebarElement(
            index,
            element.icon,
            (role && element.labelByRole?.[role]) || element.name,
            element.forward,
          ),
        )}
      </div>
      <div className={classes.sidebarFooter}>
        <StyledButton
          variant="ghost"
          startIcon={<LogoutIcon sx={{ fontSize: "18px !important" }} />}
          sx={{
            color: "rgba(255, 255, 255, 0.75)",
            fontSize: "0.8rem",
            padding: "6px 14px",
            border: "1px solid rgba(255, 255, 255, 0.15)",
            "&:hover": {
              backgroundColor: "rgba(239, 68, 68, 0.15)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              color: "#EF4444",
            },
          }}
          onClick={handleLogout}
        >
          Logout
        </StyledButton>
      </div>
    </div>
  );
}
