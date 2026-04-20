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
import AccountBalanceOutlinedIcon from "@mui/icons-material/AccountBalanceOutlined";
import TimelineIcon from "@mui/icons-material/Timeline";
import PersonAddOutlinedIcon from "@mui/icons-material/PersonAddOutlined";

import ChatBubbleOutlineIcon from "@mui/icons-material/ChatBubbleOutline";

import React from "react";
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
    allowedRoles: ["MANAGER"],
  },
  {
    name: "Care Sequences",
    icon: TimelineIcon,
    forward: "/sequences",
    allowedRoles: ["MANAGER"],
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
    name: "Facilities",
    icon: AccountBalanceOutlinedIcon,
    forward: "/organizations",
    allowedRoles: ["MANAGER"],
  },
  {
    name: "Ask",
    icon: ChatBubbleOutlineIcon,
    forward: "/ask",
    allowedRoles: ["DOCTOR"],
  },
  {
    name: "Add User",
    icon: PersonAddOutlinedIcon,
    forward: "/register-user",
    allowedRoles: ["MANAGER", "DOCTOR", "PATIENT"],
    labelByRole: {
      DOCTOR: "Register Patient",
      PATIENT: "Invite Family",
    },
  },
];

export default function Sidebar() {
  const classes = useClasses(sidebarStyles, { name: "SidebarStyles" });

  const router = useRouter();
  const pathname = usePathname();
  const dispatch = useAppDispatch();
  const role = useSelector((s: RootState) => s.auth.user?.role);
  const visibleElements = role
    ? sidebarElements.filter((el) => el.allowedRoles.includes(role))
    : sidebarElements;

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
