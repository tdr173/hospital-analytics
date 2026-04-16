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
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import useClasses from "@/utils/useClasses";
import { PatientsPageStyles } from "./styles";
import theme from "@/utils/theme";
import { clearName } from "@/utils/functions";

import GenderBadge from "./components/GenderBadge/GenderBadge";
import StatusBadge from "./components/StatusBadge/StatusBadge";
import ClusterBadge from "./components/ClusterBadge/ClusterBadge";
import PatientFilters from "./components/PatientFilters/PatientFilters";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const COLUMNS = [
  { key: "lastName", label: "Name", sortable: true, width: 210 },
  { key: "age", label: "Age", sortable: true, width: 60, align: "right" as const },
  { key: "gender", label: "Gender", width: 80 },
  { key: "city", label: "City", sortable: true, width: 150 },
  { key: "race", label: "Race / Ethnicity", width: 190 },
  { key: "marital", label: "Marital", width: 100 },
  { key: "status", label: "Status", width: 100 },
  { key: "cluster", label: "Cluster", width: 160 },
];

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
  }, [dispatch, resources]);

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
  }, [searchParams, page, rows, sortBy, sortType, dispatch]);

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

  const setParam = (updates: Record<string, string | null>, resetPage = true) => {
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

  const applyFilters = () => {
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
        <GenderBadge gender={p.gender} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <TruncatedText text={p.city ?? "-"} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <TruncatedText
          text={p.race ? (p.ethnicity ? `${p.race} · ${p.ethnicity}` : p.race) : "-"}
        />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        {p.marital
          ? (resources?.maritalStatuses.find((o) => o.value === p.marital)?.label ?? p.marital)
          : "-"}
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <StatusBadge deathdate={p.deathdate} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <ClusterBadge color={p.clusterColor} title={p.clusterTitle} />
      </TableCell>
    </StyledTableRow>
  );

  if (resourcesLoading || !resources) {
    return <div className={classes.loading}>Loading...</div>;
  }

  return (
    <div className={classes.pageContainer}>
      <PatientFilters
        resources={resources}
        search={search}
        gender={gender}
        ageGroup={ageGroup}
        status={status}
        race={race}
        marital={marital}
        onSearchChange={setSearch}
        onGenderChange={setGender}
        onAgeGroupChange={setAgeGroup}
        onStatusChange={setStatus}
        onRaceChange={setRace}
        onMaritalChange={setMarital}
        onApply={applyFilters}
      />

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
