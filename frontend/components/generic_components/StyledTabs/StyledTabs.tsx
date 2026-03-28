"use client";

import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import { useRouter, usePathname } from "next/navigation";
import useClasses from "@/utils/useClasses";
import styledTabsStyles from "./StyledTabsStyles";

interface TabItem {
  name: string;
  forward: string;
}

interface StyledTabsProps {
  items: TabItem[];
}

export default function StyledTabs({ items }: StyledTabsProps) {
  const classes = useClasses(styledTabsStyles, { name: "StyledTabsStyles" });
  const router = useRouter();
  const pathname = usePathname();

  const activeIndex = items.findIndex((item) => pathname.startsWith(item.forward));
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
        "& .MuiTabs-flexContainer": { gap: "0px", width: "100%" },
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
          className={activeIndex === index ? classes.activeTab : classes.tab}
        />
      ))}
    </Tabs>
  );
}
