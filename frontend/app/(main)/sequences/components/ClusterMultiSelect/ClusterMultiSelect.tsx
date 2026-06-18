"use client";

import Select, { SelectChangeEvent } from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import Checkbox from "@mui/material/Checkbox";
import IconButton from "@mui/material/IconButton";
import CloseIcon from "@mui/icons-material/Close";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import theme from "@/utils/theme";
import useClasses from "@/utils/useClasses";
import { ClusterSummary } from "@/models/generic/clusters";
import { ClusterMultiSelectStyles } from "./ClusterMultiSelectStyles";

interface Props {
  clusters: ClusterSummary[];
  selectedIds: number[];
  onChange: (ids: number[]) => void;
}

export default function ClusterMultiSelect({ clusters, selectedIds, onChange }: Props) {
  const classes = useClasses(ClusterMultiSelectStyles, { name: "ClusterMultiSelect" });

  const handleChange = (e: SelectChangeEvent<number[]>) => {
    const val = e.target.value;
    onChange(typeof val === "string" ? val.split(",").map(Number) : (val as number[]));
  };

  const renderValue = (selected: number[]) => {
    if (selected.length === 0) {
      return <span className={classes.placeholder}>Select clusters...</span>;
    }
    // Compact display: just the colored dots, no labels, so the field never
    // grows past its column.
    return (
      <div className={classes.chipRow}>
        {selected.map((id) => {
          const cluster = clusters.find((c) => c.clusterId === id);
          if (!cluster) return null;
          const label = id === -1 ? "Outliers" : `Cluster ${id}`;
          return (
            <span
              key={id}
              className={classes.colorDot}
              style={{ backgroundColor: cluster.color }}
              title={label}
            />
          );
        })}
      </div>
    );
  };

  const hasSelection = selectedIds.length > 0;

  return (
    <Select
      multiple
      value={selectedIds}
      onChange={handleChange}
      displayEmpty
      renderValue={renderValue}
      className={classes.select}
      MenuProps={{ PaperProps: { style: { maxHeight: 300 } } }}
      IconComponent={() =>
        hasSelection ? (
          <IconButton
            size="small"
            onMouseDown={(e) => {
              e.stopPropagation();
              e.preventDefault();
              onChange([]);
            }}
            sx={{
              position: "absolute",
              right: "4px",
              padding: "3px",
              color: theme.colors.text.secondary,
            }}
          >
            <CloseIcon sx={{ fontSize: "1rem" }} />
          </IconButton>
        ) : (
          <ExpandMoreIcon
            sx={{
              fontSize: "1.25rem",
              color: theme.colors.text.secondary,
              position: "absolute",
              right: "8px",
              pointerEvents: "none",
            }}
          />
        )
      }
    >
      {clusters.map((cluster) => {
        const label = cluster.clusterId === -1 ? "Outliers" : `Cluster ${cluster.clusterId}`;
        return (
          <MenuItem key={cluster.clusterId} value={cluster.clusterId} className={classes.menuItem}>
            <Checkbox
              checked={selectedIds.includes(cluster.clusterId)}
              size="small"
              sx={{ padding: "2px", color: cluster.color, "&.Mui-checked": { color: cluster.color } }}
            />
            <span
              className={classes.colorDot}
              style={{ backgroundColor: cluster.color }}
            />
            {label}
          </MenuItem>
        );
      })}
    </Select>
  );
}
