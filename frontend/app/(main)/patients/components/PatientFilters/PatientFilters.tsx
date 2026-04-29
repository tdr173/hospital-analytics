"use client";

import SearchIcon from "@mui/icons-material/Search";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledMultiDropdown from "@/components/generic_components/StyledMultiDropdown/StyledMultiDropdown";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import useClasses from "@/utils/useClasses";
import theme from "@/utils/theme";
import { PatientResources } from "@/models/generic/patients";
import { PatientFiltersStyles } from "./PatientFiltersStyles";

interface Props {
  resources: PatientResources;
  search: string;
  gender: string[];
  ageGroup: string[];
  status: string[];
  race: string[];
  marital: string[];
  onSearchChange: (v: string) => void;
  onGenderChange: (v: string[]) => void;
  onAgeGroupChange: (v: string[]) => void;
  onStatusChange: (v: string[]) => void;
  onRaceChange: (v: string[]) => void;
  onMaritalChange: (v: string[]) => void;
  onApply: () => void;
}

export default function PatientFilters({
  resources,
  search,
  gender,
  ageGroup,
  status,
  race,
  marital,
  onSearchChange,
  onGenderChange,
  onAgeGroupChange,
  onStatusChange,
  onRaceChange,
  onMaritalChange,
  onApply,
}: Props) {
  const classes = useClasses(PatientFiltersStyles, { name: "PatientFilters" });

  return (
    <div className={classes.bar}>
      <StyledInput
        label="Search"
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        placeholder="Search patients by name"
        startIcon={<SearchIcon sx={{ fontSize: "1.1rem", color: "#6b7280" }} />}
        clearIcon
        onClear={() => onSearchChange("")}
        height={36}
      />
      <StyledMultiDropdown
        label="Gender"
        value={gender}
        onChange={(v) => onGenderChange(v as string[])}
        onClear={() => onGenderChange([])}
        options={resources.genders}
        placeholder="All"
        width="auto"
      />
      <StyledMultiDropdown
        label="Age Group"
        value={ageGroup}
        onChange={(v) => onAgeGroupChange(v as string[])}
        onClear={() => onAgeGroupChange([])}
        options={resources.ageGroups}
        placeholder="All"
        width="auto"
      />
      <StyledMultiDropdown
        label="Status"
        value={status}
        onChange={(v) => onStatusChange(v as string[])}
        onClear={() => onStatusChange([])}
        options={resources.statuses}
        placeholder="All"
        width="auto"
      />
      <StyledMultiDropdown
        label="Race"
        value={race}
        onChange={(v) => onRaceChange(v as string[])}
        onClear={() => onRaceChange([])}
        options={resources.races}
        placeholder="All"
        width="auto"
      />
      <StyledMultiDropdown
        label="Marital"
        value={marital}
        onChange={(v) => onMaritalChange(v as string[])}
        onClear={() => onMaritalChange([])}
        options={resources.maritalStatuses}
        placeholder="All"
        width="auto"
      />
      <StyledButton
        onClick={onApply}
        sx={{
          width: "100%",
          alignSelf: "flex-end",
          background: theme.colors.button.primary,
          boxShadow: "none",
          border: "none",
          color: "#ffffff",
          height: "36px !important",
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
  );
}
