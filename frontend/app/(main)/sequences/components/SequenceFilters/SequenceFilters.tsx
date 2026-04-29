"use client";

import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import SearchIcon from "@mui/icons-material/Search";
import useClasses from "@/utils/useClasses";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledDropdown from "@/components/generic_components/StyledDropdown/StyledDropdown";
import {
  SequenceResourcesResponse,
  SequenceSortOption,
} from "@/models/generic/sequences";
import { SequenceFiltersStyles } from "./SequenceFiltersStyles";

interface Props {
  search: string;
  minLength: number;
  sortBy: string;
  sortType: "asc" | "desc";
  resources: SequenceResourcesResponse | null;
  onSearchChange: (value: string) => void;
  onMinLengthChange: (value: number) => void;
  onSortByChange: (value: string) => void;
  onSortTypeChange: (value: "asc" | "desc") => void;
}

export default function SequenceFilters({
  search,
  minLength,
  sortBy,
  sortType,
  resources,
  onSearchChange,
  onMinLengthChange,
  onSortByChange,
  onSortTypeChange,
}: Props) {
  const classes = useClasses(SequenceFiltersStyles, {
    name: "SequenceFilters",
  });

  const minLen = resources?.minLength ?? 1;
  const maxLen = resources?.maxLength ?? 1;
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

  return (
    <div className={classes.bar}>
      <div className={classes.fieldGroup}>
        <label className={classes.fieldLabel}>Search</label>
        <StyledInput
          label=""
          placeholder="Search care sequences..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          startIcon={<SearchIcon fontSize="small" />}
          clearIcon={search.length > 0}
          onClear={() => onSearchChange("")}
          height={36}
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
          width={140}
          height={36}
        />
      </div>

      <div className={classes.fieldGroup}>
        <label className={classes.fieldLabel}>Sort By</label>
        <StyledDropdown
          label=""
          value={sortBy}
          onChange={(v) => onSortByChange(String(v))}
          options={sortOptions}
          width={180}
          height={36}
        />
      </div>

      <div className={classes.fieldGroup}>
        <label className={classes.fieldLabel}>Order</label>
        <button
          type="button"
          className={classes.sortDirectionButton}
          onClick={() => onSortTypeChange(sortType === "desc" ? "asc" : "desc")}
          title={sortType === "desc" ? "Descending" : "Ascending"}
          style={{ height: 36 }}
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
    </div>
  );
}
