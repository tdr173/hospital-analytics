"use client";

import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import SearchIcon from "@mui/icons-material/Search";
import useClasses from "@/utils/useClasses";
import theme from "@/utils/theme";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledDropdown from "@/components/generic_components/StyledDropdown/StyledDropdown";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import {
  SequenceResourcesResponse,
  SequenceSortOption,
} from "@/models/generic/sequences";
import { ClusterSummary } from "@/models/generic/clusters";
import { SequenceFiltersStyles } from "./SequenceFiltersStyles";
import ClusterMultiSelect from "../ClusterMultiSelect/ClusterMultiSelect";

interface Props {
  search: string;
  minLength: number;
  rangeMin: number;
  rangeMax: number;
  sortBy: string;
  sortType: "asc" | "desc";
  resources: SequenceResourcesResponse | null;
  onSearchChange: (value: string) => void;
  onSearchApply: () => void;
  onSearchClear: () => void;
  onMinLengthChange: (value: number) => void;
  onSortByChange: (value: string) => void;
  onSortTypeChange: (value: "asc" | "desc") => void;
  activeTab?: "global" | "cluster";
  clusters?: ClusterSummary[];
  selectedClusterIds?: number[];
  onClusterIdsChange?: (ids: number[]) => void;
}

export default function SequenceFilters({
  search,
  minLength,
  rangeMin,
  rangeMax,
  sortBy,
  sortType,
  resources,
  onSearchChange,
  onSearchApply,
  onSearchClear,
  onMinLengthChange,
  onSortByChange,
  onSortTypeChange,
  activeTab = "global",
  clusters = [],
  selectedClusterIds = [],
  onClusterIdsChange,
}: Props) {
  const classes = useClasses(SequenceFiltersStyles, {
    name: "SequenceFilters",
  });

  const minLen = rangeMin;
  const maxLen = rangeMax;
  const lengthOptions = Array.from(
    { length: Math.max(0, maxLen - minLen + 1) },
    (_, i) => {
      const v = minLen + i;
      return { value: v, label: `${v} steps` };
    },
  );

  const sortOptions: SequenceSortOption[] = resources?.sortOptions ?? [
    { value: "support", label: "Most Common" },
    { value: "length", label: "Sequence Steps" },
  ];

  const showClusterPicker = activeTab === "cluster";

  return (
    <div
      className={classes.bar}
      style={{
        gridTemplateColumns: showClusterPicker
          ? "minmax(0, 2fr) minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1.4fr) minmax(0, 1fr) minmax(0, 1fr)"
          : "minmax(0, 2fr) minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr)",
      }}
    >
      <div className={classes.fieldGroup}>
        <label className={classes.fieldLabel}>Search</label>
        <StyledInput
          label=""
          placeholder="Search care sequences..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") onSearchApply();
          }}
          startIcon={<SearchIcon fontSize="small" />}
          clearIcon={search.length > 0}
          onClear={onSearchClear}
          height={"40px"}
          fullWidth
        />
      </div>

      <div className={classes.fieldGroup}>
        <label className={classes.fieldLabel}>Min Steps</label>
        <StyledDropdown
          label=""
          value={minLength}
          onChange={(v) => onMinLengthChange(Number(v))}
          options={lengthOptions}
          fullWidth
          height={"40px"}
          onClear={() => onMinLengthChange(minLen)}
        />
      </div>

      <div className={classes.fieldGroup}>
        <label className={classes.fieldLabel}>Sort By</label>
        <StyledDropdown
          label=""
          value={sortBy}
          onChange={(v) => onSortByChange(String(v))}
          options={sortOptions}
          fullWidth
          height={"40px"}
          onClear={() => onSortByChange("support")}
        />
      </div>

      {showClusterPicker && onClusterIdsChange && (
        <div className={classes.fieldGroup}>
          <label className={classes.fieldLabel}>Clusters</label>
          <ClusterMultiSelect
            clusters={clusters}
            selectedIds={selectedClusterIds}
            onChange={onClusterIdsChange}
          />
        </div>
      )}

      <div className={classes.fieldGroup}>
        <label className={classes.fieldLabel}>Order</label>
        <button
          type="button"
          className={classes.sortDirectionButton}
          onClick={() => onSortTypeChange(sortType === "desc" ? "asc" : "desc")}
          title={sortType === "desc" ? "Descending" : "Ascending"}
          style={{ height: "40px", width: "100%" }}
        >
          {sortType === "desc" ? (
            <>
              <ArrowDownwardIcon fontSize="small" /> Desc
            </>
          ) : (
            <>
              <ArrowUpwardIcon fontSize="small" /> Asc
            </>
          )}
        </button>
      </div>

      <div className={classes.fieldGroup}>
        <label className={classes.fieldLabel} aria-hidden>
          &nbsp;
        </label>
        <StyledButton
          onClick={onSearchApply}
          sx={{
            width: "100%",
            height: "40px !important",
            background: theme.colors.button.primary,
            boxShadow: "none",
            border: "none",
            color: "#ffffff",
            "&:hover": {
              background: theme.colors.button.primaryHover,
              boxShadow: "none",
              transform: "none",
            },
            "&:active": {
              background: theme.colors.button.primaryActive,
              boxShadow: "none",
              transform: "none",
            },
          }}
        >
          Search
        </StyledButton>
      </div>
    </div>
  );
}
