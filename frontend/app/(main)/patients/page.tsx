"use client";

import { Suspense, useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useSearchParams, useRouter } from "next/navigation";
import TableCell from "@mui/material/TableCell";

import { RootState, AppDispatch } from "@/store";
import {
  fetchPatients,
  fetchPatientResources,
} from "@/store/slices/patients/thunks";
import { PatientListItem } from "@/models/generic/patients";

import StyledTable, {
  StyledTableRow,
  bodyCellSx,
} from "@/components/generic_components/StyledTable/StyledTable";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import SearchIcon from "@mui/icons-material/Search";
import StyledMultiDropdown from "@/components/generic_components/StyledMultiDropdown/StyledMultiDropdown";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import useClasses from "@/utils/useClasses";
import { PatientsPageStyles } from "./styles";
import theme from "@/utils/theme";
import { clearName } from "@/utils/functions";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const COLUMNS = [
  { key: "lastName", label: "Name", sortable: true, width: 210 },
  {
    key: "age",
    label: "Age",
    sortable: true,
    width: 60,
    align: "right" as const,
  },
  { key: "gender", label: "Gender", width: 80 },
  { key: "city", label: "City", sortable: true, width: 150 },
  { key: "race", label: "Race / Ethnicity", width: 190 },
  { key: "marital", label: "Marital", width: 100 },
  { key: "status", label: "Status", width: 100 },
  { key: "cluster", label: "Cluster", width: 160 },
];

function GenderBadge({
  gender,
  classes,
}: {
  gender: string | null;
  classes: any;
}) {
  if (!gender) return <span className={classes.genderBadgeEmpty}>-</span>;
  const isFemale = gender === "F";
  return (
    <span
      className={isFemale ? classes.genderBadgeFemale : classes.genderBadgeMale}
    >
      {isFemale ? "F" : "M"}
    </span>
  );
}

function StatusBadge({
  deathdate,
  classes,
}: {
  deathdate: string | null;
  classes: any;
}) {
  const alive = !deathdate;
  return (
    <span
      className={alive ? classes.statusBadgeAlive : classes.statusBadgeDeceased}
    >
      {alive ? "Alive" : "Deceased"}
    </span>
  );
}

function ClusterBadge({
  color,
  title,
  classes,
}: {
  color: string | null;
  title: string | null;
  classes: any;
}) {
  if (!color || !title)
    return <span className={classes.clusterBadgeEmpty}>-</span>;
  return (
    <span className={classes.clusterBadgeContainer}>
      <span
        className={classes.clusterBadgeDot}
        style={{ backgroundColor: color }}
      />
      <TruncatedText text={title} />
    </span>
  );
}

function PatientsPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const dispatch = useAppDispatch();
  const classes = useClasses(PatientsPageStyles, { name: "PatientsPage" });

  const { items, total, loading, resources, resourcesLoading } = useSelector(
    (state: RootState) => state.patients,
  );

  useEffect(() => {
    if (!resources) dispatch(fetchPatientResources());
  }, []);

  const page = Math.max(1, parseInt(searchParams.get("page") ?? "1", 10));
  const rows = parseInt(searchParams.get("rows") ?? "25", 10);
  const sortBy = searchParams.get("sortBy") ?? "lastName";
  const sortType = (searchParams.get("sortType") ?? "asc") as "asc" | "desc";

  useEffect(() => {
    dispatch(
      fetchPatients({
        search: searchParams.get("search") || undefined,
        gender: searchParams.get("gender")?.split(",").filter(Boolean),
        ageGroup: searchParams.get("ageGroup")?.split(",").filter(Boolean),
        status: searchParams.get("status")?.split(",").filter(Boolean),
        race: searchParams.get("race")?.split(",").filter(Boolean),
        marital: searchParams.get("marital")?.split(",").filter(Boolean),
        page,
        rows,
        sortBy,
        sortType,
      }),
    );
  }, [searchParams, page, rows, sortBy, sortType]);

  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const [gender, setGender] = useState<string[]>(
    searchParams.get("gender")?.split(",").filter(Boolean) ?? [],
  );
  const [ageGroup, setAgeGroup] = useState<string[]>(
    searchParams.get("ageGroup")?.split(",").filter(Boolean) ?? [],
  );
  const [status, setStatus] = useState<string[]>(
    searchParams.get("status")?.split(",").filter(Boolean) ?? [],
  );
  const [race, setRace] = useState<string[]>(
    searchParams.get("race")?.split(",").filter(Boolean) ?? [],
  );
  const [marital, setMarital] = useState<string[]>(
    searchParams.get("marital")?.split(",").filter(Boolean) ?? [],
  );

  const setParam = (
    updates: Record<string, string | null>,
    resetPage = true,
  ) => {
    const p = new URLSearchParams(searchParams.toString());
    Object.entries(updates).forEach(([k, v]) => {
      if (v) p.set(k, v);
      else p.delete(k);
    });
    if (resetPage) p.set("page", "1");
    router.push(`/patients?${p.toString()}`);
  };

  const handleSort = (key: string, dir: "asc" | "desc") =>
    setParam({ sortBy: key, sortType: dir });

  const handlePageChange = (newPage: number) =>
    setParam({ page: (newPage + 1).toString() }, false);

  const handleRowsPerPageChange = (newRows: number) =>
    setParam({ rows: newRows.toString(), page: "1" }, false);

  const renderRow = (p: PatientListItem, i: number) => (
    <StyledTableRow
      key={p.patientId}
      index={i}
      onClick={() => router.push(`/patients/${p.patientId}`)}
    >
      <TableCell
        sx={{
          ...bodyCellSx,
          fontWeight: theme.typography.fontWeight.semibold,
          color: theme.colors.primary.main,
        }}
      >
        <TruncatedText text={clearName(p.firstName, p.lastName)} />
      </TableCell>
      <TableCell sx={bodyCellSx} align="right">
        {p.age}
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <GenderBadge gender={p.gender} classes={classes} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <TruncatedText text={p.city ?? "-"} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <TruncatedText
          text={
            p.race ? (p.ethnicity ? `${p.race} · ${p.ethnicity}` : p.race) : "-"
          }
        />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        {p.marital
          ? (resources?.maritalStatuses.find((o) => o.value === p.marital)
              ?.label ?? p.marital)
          : "-"}
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <StatusBadge deathdate={p.deathdate} classes={classes} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <ClusterBadge
          color={p.clusterColor}
          title={p.clusterTitle}
          classes={classes}
        />
      </TableCell>
    </StyledTableRow>
  );

  const handleSearch = () => {
    const p = new URLSearchParams(searchParams.toString());
    const strFilters: Record<string, string> = { search };
    const arrFilters: Record<string, string[]> = {
      gender,
      ageGroup,
      status,
      race,
      marital,
    };

    Object.entries(strFilters).forEach(([k, v]) => {
      if (v) p.set(k, v);
      else p.delete(k);
    });

    Object.entries(arrFilters).forEach(([k, v]) => {
      if (v.length) p.set(k, v.join(","));
      else p.delete(k);
    });

    p.set("page", "1");
    router.push(`/patients?${p.toString()}`);
  };

  if (resourcesLoading || !resources) {
    return <div className={classes.loading}>Loading...</div>;
  }

  return (
    <div className={classes.pageContainer}>
      <div className={classes.filterBar}>
        <StyledInput
          label="Search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search patients by name"
          startIcon={
            <SearchIcon sx={{ fontSize: "1.1rem", color: "#6b7280" }} />
          }
          clearIcon
          onClear={() => setSearch("")}
          height={36}
        />

        <StyledMultiDropdown
          label="Gender"
          value={gender}
          onChange={(v) => setGender(v as string[])}
          onClear={() => setGender([])}
          options={resources.genders}
          placeholder="All"
          width={"auto"}
        />

        <StyledMultiDropdown
          label="Age Group"
          value={ageGroup}
          onChange={(v) => setAgeGroup(v as string[])}
          onClear={() => setAgeGroup([])}
          options={resources.ageGroups}
          placeholder="All"
          width={"auto"}
        />

        <StyledMultiDropdown
          label="Status"
          value={status}
          onChange={(v) => setStatus(v as string[])}
          onClear={() => setStatus([])}
          options={resources.statuses}
          placeholder="All"
          width={"auto"}
        />

        <StyledMultiDropdown
          label="Race"
          value={race}
          onChange={(v) => setRace(v as string[])}
          onClear={() => setRace([])}
          options={resources.races}
          placeholder="All"
          width={"auto"}
        />

        <StyledMultiDropdown
          label="Marital"
          value={marital}
          onChange={(v) => setMarital(v as string[])}
          onClear={() => setMarital([])}
          options={resources.maritalStatuses}
          placeholder="All"
          width={"auto"}
        />

        <StyledButton
          onClick={() => handleSearch()}
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

      <div className={classes.tableArea}>
        <StyledTable
          columns={COLUMNS}
          data={items}
          renderRow={renderRow}
          loading={loading}
          total={total}
          page={page - 1}
          rowsPerPage={rows}
          onPageChange={handlePageChange}
          onRowsPerPageChange={handleRowsPerPageChange}
          sortBy={sortBy}
          sortType={sortType}
          onSort={handleSort}
          emptyMessage="No patients found matching the selected filters."
        />
      </div>
    </div>
  );
}

export default function PatientsPage() {
  return (
    <Suspense>
      <PatientsPageContent />
    </Suspense>
  );
}
