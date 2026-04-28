"use client";

import { Suspense, useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useSearchParams, useRouter } from "next/navigation";
import TableCell from "@mui/material/TableCell";
import IconButton from "@mui/material/IconButton";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";

import { RootState, AppDispatch } from "@/store";
import {
  fetchPatients,
  fetchPatientResources,
  createPatient,
  updatePatient,
  deletePatient,
  PatientCreatePayload,
} from "@/store/slices/patients/thunks";
import { PatientListItem } from "@/models/generic/patients";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import AddIcon from "@mui/icons-material/Add";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import PatientFormModal from "./components/PatientFormModal/PatientFormModal";
import FormModal from "@/components/generic_components/FormModal/FormModal";

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
  { key: "lastName", label: "Name", sortable: true, width: 140 },
  {
    key: "age",
    label: "Age",
    sortable: true,
    width: 70,
    align: "right" as const,
  },
  { key: "gender", label: "Gender", width: 100 },
  { key: "city", label: "City", sortable: true, width: 120 },
  { key: "race", label: "Race / Ethnicity", width: 120 },
  { key: "marital", label: "Marital Status", width: 100 },
  { key: "status", label: "Status", width: 80 },
  { key: "cluster", label: "Group", width: 180 },
  { key: "actions", label: "Actions", width: 80, align: "center" as const },
];

function PatientsPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const dispatch = useAppDispatch();
  const classes = useClasses(PatientsPageStyles, { name: "PatientsPage" });

  const { items, total, loading, resources, resourcesLoading } = useSelector(
    (state: RootState) => state.patients,
  );
  const role = useSelector((state: RootState) => state.auth.user?.role);
  const canManagePatients = role === "MANAGER" || role === "DOCTOR";

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<PatientListItem | null>(null);
  const [deleting, setDeleting] = useState<PatientListItem | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

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

  const refreshList = () =>
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

  const handleSubmitPatient = async (payload: PatientCreatePayload) => {
    setSubmitting(true);
    setFormError(null);
    const result = await (editing
      ? dispatch(updatePatient({ patientId: editing.patientId, payload }))
      : dispatch(createPatient(payload)));
    setSubmitting(false);
    if ((result as any).error) {
      setFormError((result as any).payload?.message ?? "Save failed");
      return;
    }
    setModalOpen(false);
    setEditing(null);
    refreshList();
  };

  const handleConfirmDelete = async () => {
    if (!deleting) return;
    setSubmitting(true);
    const result = await dispatch(deletePatient(deleting.patientId));
    setSubmitting(false);
    setDeleting(null);
    if (!(result as any).error) refreshList();
  };

  const renderRow = (p: PatientListItem, i: number) => (
    <StyledTableRow key={p.patientId} index={i}>
      <TableCell
        sx={{
          ...bodyCellSx,
          fontWeight: theme.typography.fontWeight.semibold,
          color: theme.colors.primary.main,
        }}
      >
        <TruncatedText text={clearName(p.firstName, p.lastName)} />
      </TableCell>
      <TableCell sx={bodyCellSx} align="center">
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
        <StatusBadge deathdate={p.deathdate} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <ClusterBadge color={p.clusterColor} title={p.clusterTitle} />
      </TableCell>
      <TableCell sx={bodyCellSx} align="center">
        <IconButton
          size="small"
          onClick={() => router.push(`/patients/${p.patientId}`)}
          aria-label="View patient"
          sx={{
            padding: "4px",
            color: theme.colors.primary.main,
            "&:hover": { backgroundColor: "rgba(0, 103, 128, 0.08)" },
          }}
        >
          <VisibilityOutlinedIcon sx={{ fontSize: "1.05rem" }} />
        </IconButton>
        {canManagePatients && (
          <>
            <IconButton
              size="small"
              onClick={() => {
                setEditing(p);
                setFormError(null);
                setModalOpen(true);
              }}
              aria-label="Edit patient"
              sx={{
                padding: "4px",
                color: theme.colors.text.secondary,
                "&:hover": { backgroundColor: "rgba(0, 103, 128, 0.08)" },
              }}
            >
              <EditOutlinedIcon sx={{ fontSize: "1.05rem" }} />
            </IconButton>
            <IconButton
              size="small"
              onClick={() => setDeleting(p)}
              aria-label="Delete patient"
              sx={{
                padding: "4px",
                color: theme.colors.status.error,
                "&:hover": { backgroundColor: "rgba(239, 68, 68, 0.08)" },
              }}
            >
              <DeleteOutlineIcon sx={{ fontSize: "1.05rem" }} />
            </IconButton>
          </>
        )}
      </TableCell>
    </StyledTableRow>
  );

  if (resourcesLoading || !resources) {
    return <div className={classes.loading}>Loading...</div>;
  }

  return (
    <div className={classes.pageContainer}>
      {canManagePatients && (
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <StyledButton
            onClick={() => {
              setEditing(null);
              setFormError(null);
              setModalOpen(true);
            }}
            sx={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              height: "36px",
            }}
          >
            <AddIcon sx={{ fontSize: "1.05rem" }} />
            Add patient
          </StyledButton>
        </div>
      )}

      <PatientFormModal
        open={modalOpen}
        initial={editing}
        resources={resources}
        submitting={submitting}
        errorMessage={formError}
        onClose={() => {
          setModalOpen(false);
          setEditing(null);
        }}
        onSubmit={handleSubmitPatient}
      />

      <FormModal
        open={!!deleting}
        title="Delete patient"
        submitLabel="Delete"
        destructive
        submitting={submitting}
        onClose={() => setDeleting(null)}
        onSubmit={handleConfirmDelete}
        layout="single"
      >
        <div>
          Delete <strong>{deleting?.firstName} {deleting?.lastName}</strong>? This
          cannot be undone. Patients with linked encounters cannot be deleted.
        </div>
      </FormModal>

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
          emptyMessage="No patients match the selected filters."
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
