"use client";

import Select, { SelectChangeEvent } from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import Checkbox from "@mui/material/Checkbox";
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
    return (
      <div className={classes.chipRow}>
        {selected.map((id) => {
          const cluster = clusters.find((c) => c.clusterId === id);
          if (!cluster) return null;
          const label = id === -1 ? "Outliers" : `Cluster ${id}`;
          return (
            <span
              key={id}
              className={classes.chip}
              style={{
                backgroundColor: cluster.color + "22",
                color: cluster.color,
                border: `1px solid ${cluster.color}55`,
              }}
            >
              <span
                className={classes.colorDot}
                style={{ backgroundColor: cluster.color }}
              />
              {label}
            </span>
          );
        })}
      </div>
    );
  };

  return (
    <Select
      multiple
      value={selectedIds}
      onChange={handleChange}
      displayEmpty
      renderValue={renderValue}
      className={classes.select}
      MenuProps={{ PaperProps: { style: { maxHeight: 300 } } }}
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
