"use client";

import { Suspense, useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useSearchParams, useRouter } from "next/navigation";
import TableCell from "@mui/material/TableCell";
import IconButton from "@mui/material/IconButton";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";

import { RootState, AppDispatch } from "@/store";
import {
  fetchProviders,
  fetchProviderResources,
  createProvider,
  updateProvider,
  deleteProvider,
  ProviderCreatePayload,
} from "@/store/slices/providers/thunks";
import { ProviderListItem, ProviderDetail } from "@/models/generic/providers";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import AddIcon from "@mui/icons-material/Add";
import DoctorFormModal from "./components/DoctorFormModal/DoctorFormModal";
import FormModal from "@/components/generic_components/FormModal/FormModal";

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
import { ProvidersPageStyles } from "./styles";
import theme from "@/utils/theme";
import { clearName } from "@/utils/functions";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const COLUMNS = [
  { key: "lastName", label: "Name", sortable: true, width: 160 },
  { key: "speciality", label: "Specialty", sortable: true, width: 160 },
  { key: "gender", label: "Gender", width: 70 },
  { key: "city", label: "City", sortable: true, width: 140 },
  { key: "organizationName", label: "Facility", width: 200 },
  {
    key: "encounters",
    label: "Visits",
    sortable: true,
    width: 100,
    align: "right" as const,
  },
  { key: "actions", label: "Actions", width: 110, align: "center" as const },
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
      {isFemale ? "Female" : "Male"}
    </span>
  );
}

function ProvidersPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const dispatch = useAppDispatch();
  const classes = useClasses(ProvidersPageStyles, { name: "ProvidersPage" });

  const { items, total, loading, resources, resourcesLoading } = useSelector(
    (state: RootState) => state.providers,
  );
  const role = useSelector((state: RootState) => state.auth.user?.role);
  const canManageDoctors = role === "MANAGER";

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<ProviderListItem | null>(null);
  const [deleting, setDeleting] = useState<ProviderListItem | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (!resources) dispatch(fetchProviderResources());
  }, [dispatch, resources]);

  const page = Math.max(1, parseInt(searchParams.get("page") ?? "1", 10));
  const rows = parseInt(searchParams.get("rows") ?? "25", 10);
  const sortBy = searchParams.get("sortBy") ?? "lastName";
  const sortType = (searchParams.get("sortType") ?? "asc") as "asc" | "desc";

  useEffect(() => {
    dispatch(
      fetchProviders({
        search: searchParams.get("search") || undefined,
        gender: searchParams.get("gender")?.split(",").filter(Boolean),
        speciality: searchParams.get("speciality")?.split(",").filter(Boolean),
        page,
        rows,
        sortBy,
        sortType,
      }),
    );
  }, [dispatch, searchParams, page, rows, sortBy, sortType]);

  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const [gender, setGender] = useState<string[]>(
    searchParams.get("gender")?.split(",").filter(Boolean) ?? [],
  );
  const [speciality, setSpeciality] = useState<string[]>(
    searchParams.get("speciality")?.split(",").filter(Boolean) ?? [],
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
    router.push(`/providers?${p.toString()}`);
  };

  const handleSort = (key: string, dir: "asc" | "desc") =>
    setParam({ sortBy: key, sortType: dir });

  const handlePageChange = (newPage: number) =>
    setParam({ page: (newPage + 1).toString() }, false);

  const handleRowsPerPageChange = (newRows: number) =>
    setParam({ rows: newRows.toString(), page: "1" }, false);

  const handleSearch = () => {
    const p = new URLSearchParams(searchParams.toString());
    if (search) p.set("search", search);
    else p.delete("search");
    if (gender.length) p.set("gender", gender.join(","));
    else p.delete("gender");
    if (speciality.length) p.set("speciality", speciality.join(","));
    else p.delete("speciality");
    p.set("page", "1");
    router.push(`/providers?${p.toString()}`);
  };

  const refreshList = () =>
    dispatch(
      fetchProviders({
        search: searchParams.get("search") || undefined,
        gender: searchParams.get("gender")?.split(",").filter(Boolean),
        speciality: searchParams.get("speciality")?.split(",").filter(Boolean),
        page,
        rows,
        sortBy,
        sortType,
      }),
    );

  const handleSubmitDoctor = async (payload: ProviderCreatePayload) => {
    setSubmitting(true);
    setFormError(null);
    const result = await (editing
      ? dispatch(updateProvider({ providerId: editing.providerId, payload }))
      : dispatch(createProvider(payload)));
    setSubmitting(false);
    if ((result as any).error) {
      setFormError((result as any).payload?.message ?? "Save failed");
      return;
    }
    setModalOpen(false);
    setEditing(null);
    if (!editing && page !== 1) {
      const p = new URLSearchParams(searchParams.toString());
      p.set("page", "1");
      router.push(`/providers?${p.toString()}`);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleting) return;
    setSubmitting(true);
    const result = await dispatch(deleteProvider(deleting.providerId));
    setSubmitting(false);
    setDeleting(null);
    if (!(result as any).error) refreshList();
  };

  const renderRow = (p: ProviderListItem, i: number) => (
    <StyledTableRow key={p.providerId} index={i}>
      <TableCell
        sx={{
          ...bodyCellSx,
          fontWeight: theme.typography.fontWeight.semibold,
          color: theme.colors.primary.main,
        }}
      >
        <TruncatedText text={clearName(p.firstName, p.lastName)} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <TruncatedText text={p.speciality ?? "-"} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <GenderBadge gender={p.gender} classes={classes} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <TruncatedText text={p.city ?? "-"} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <TruncatedText text={p.organizationName ?? "-"} />
      </TableCell>
      <TableCell sx={bodyCellSx} align="right">
        {p.encounters}
      </TableCell>
      <TableCell sx={bodyCellSx} align="center">
        <IconButton
          size="small"
          onClick={() => router.push(`/providers/${p.providerId}`)}
          aria-label="View doctor"
          sx={{
            padding: "4px",
            color: theme.colors.primary.main,
            "&:hover": { backgroundColor: "rgba(0, 103, 128, 0.08)" },
          }}
        >
          <VisibilityOutlinedIcon sx={{ fontSize: "1.05rem" }} />
        </IconButton>
        {canManageDoctors && (
          <>
            <IconButton
              size="small"
              onClick={() => {
                setEditing(p);
                setFormError(null);
                setModalOpen(true);
              }}
              aria-label="Edit doctor"
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
              aria-label="Delete doctor"
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

  const initialForModal: ProviderDetail | null = editing
    ? {
        providerId: editing.providerId,
        firstName: editing.firstName,
        lastName: editing.lastName,
        gender: editing.gender,
        speciality: editing.speciality,
        city: editing.city,
        encounters: editing.encounters,
        organizationId: "",
        organizationName: editing.organizationName,
      }
    : null;

  return (
    <div className={classes.pageContainer}>
      <DoctorFormModal
        open={modalOpen}
        initial={initialForModal}
        resources={resources}
        submitting={submitting}
        errorMessage={formError}
        onClose={() => {
          setModalOpen(false);
          setEditing(null);
        }}
        onSubmit={handleSubmitDoctor}
      />

      <FormModal
        open={!!deleting}
        title="Delete doctor"
        submitLabel="Delete"
        destructive
        submitting={submitting}
        onClose={() => setDeleting(null)}
        onSubmit={handleConfirmDelete}
        layout="single"
      >
        <div>
          Delete{" "}
          <strong>
            {deleting?.firstName} {deleting?.lastName}
          </strong>
          ? This cannot be undone. Doctors with linked encounters cannot be
          deleted.
        </div>
      </FormModal>

      <div className={classes.filterBar}>
        <StyledInput
          label="Search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search doctors by name"
          startIcon={
            <SearchIcon sx={{ fontSize: "1.1rem", color: "#6b7280" }} />
          }
          clearIcon
          onClear={() => setSearch("")}
          height={"40px"}
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
          label="Specialty"
          value={speciality}
          onChange={(v) => setSpeciality(v as string[])}
          onClear={() => setSpeciality([])}
          options={resources.specialities}
          placeholder="All"
          width={"auto"}
        />

        <StyledButton
          onClick={handleSearch}
          sx={{
            width: "100%",
            alignSelf: "flex-end",
            background: theme.colors.button.primary,
            boxShadow: "none",
            border: "none",
            color: "#ffffff",
            height: "40px !important",
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
        <StyledButton
          onClick={() => {
            setEditing(null);
            setFormError(null);
            setModalOpen(true);
          }}
          sx={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            height: "40px",
            padding: "6px",
            background: theme.colors.button.add,
            boxShadow: "none",
            border: "none",
            color: "#ffffff",
            "&:hover": {
              background: theme.colors.button.addHover,
              boxShadow: "none",
              transform: "none",
            },
            "&:active": {
              background: theme.colors.button.addActive,
              boxShadow: "none",
              transform: "none",
            },
          }}
        >
          <AddIcon sx={{ fontSize: "1.05rem" }} />
          Add doctor
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
          emptyMessage="No doctors match the selected filters."
        />
      </div>
    </div>
  );
}

export default function ProvidersPage() {
  return (
    <Suspense>
      <ProvidersPageContent />
    </Suspense>
  );
}
