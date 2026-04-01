"use client";

import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import { useRouter, usePathname } from "next/navigation";
import theme from "@/utils/theme";

interface TabItem {
  name: string;
  forward: string;
}

interface StyledTabsProps {
  items: TabItem[];
}

const baseTabSx = {
  fontFamily: theme.typography.fontFamily,
  fontSize: "0.7rem",
  fontWeight: theme.typography.fontWeight.semibold,
  textTransform: "uppercase",
  backgroundColor: "transparent",
  border: "none",
  borderBottom: "2px solid transparent",
  borderRadius: "0",
  padding: "10px 6px",
  minHeight: "unset",
  flex: "1 0 auto",
  maxWidth: "none",
  cursor: "pointer",
  transition: "color 0.15s, border-color 0.15s",
  letterSpacing: "0.3px",
  whiteSpace: "nowrap",
  "&:hover": {
    backgroundColor: "transparent",
    color: theme.colors.text.primary,
  },
  minWidth: 100,
};

const activeTabSx = {
  ...baseTabSx,
  fontWeight: theme.typography.fontWeight.bold,
  color: theme.colors.primary.light,
  borderBottom: `2px solid ${theme.colors.primary.light}`,
  padding: "10px 8px",
  "&:hover": {
    backgroundColor: "transparent",
    color: theme.colors.primary.light,
  },
  minWidth: 100,
};

const inactiveTabSx = {
  ...baseTabSx,
  color: theme.colors.text.secondary,
};

export default function StyledTabs({ items }: StyledTabsProps) {
  const router = useRouter();
  const pathname = usePathname();

  const activeIndex = items.findIndex((item) =>
    pathname.startsWith(item.forward),
  );
  const currentValue = activeIndex >= 0 ? activeIndex : false;

  return (
    <Tabs
      value={currentValue}
      onChange={(_e, newValue: number) => router.push(items[newValue].forward)}
      variant="scrollable"
      scrollButtons="auto"
      slotProps={{ indicator: { style: { display: "none" } } }}
      sx={{
        minHeight: "unset",
        width: "100%",
        borderBottom: "1px solid rgba(198, 198, 205, 0.3)",
        "& .MuiTabs-flexContainer": { gap: "0px" },
        "& .MuiTabs-scrollButtons": {
          color: "#6b7280",
          "&.Mui-disabled": { opacity: 0.3 },
        },
      }}
    >
      {items.map((item, index) => (
        <Tab
          key={item.forward}
          label={item.name}
          disableRipple
          sx={activeIndex === index ? activeTabSx : inactiveTabSx}
        />
      ))}
    </Tabs>
  );
}
