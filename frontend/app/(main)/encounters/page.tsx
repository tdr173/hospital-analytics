"use client";

import { Suspense, useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useSearchParams, useRouter } from "next/navigation";
import TableCell from "@mui/material/TableCell";
import IconButton from "@mui/material/IconButton";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import AddIcon from "@mui/icons-material/Add";

import { RootState, AppDispatch } from "@/store";
import {
  fetchEncounters,
  fetchEncounterResources,
  createEncounter,
  updateEncounter,
  deleteEncounter,
} from "@/store/slices/encounters/thunks";
import { EncounterListItem } from "@/models/generic/encounters";

import StyledTable, {
  StyledTableRow,
  bodyCellSx,
} from "@/components/generic_components/StyledTable/StyledTable";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import SearchIcon from "@mui/icons-material/Search";
import StyledMultiDropdown from "@/components/generic_components/StyledMultiDropdown/StyledMultiDropdown";
import StyledDatePicker from "@/components/generic_components/StyledDatePicker/StyledDatePicker";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import FormModal from "@/components/generic_components/FormModal/FormModal";
import useClasses from "@/utils/useClasses";
import { EncountersPageStyles } from "./styles";
import theme from "@/utils/theme";
import { formatDate } from "@/utils/functions";

import EncounterFormModal, {
  EncounterFormValue,
} from "./components/EncounterFormModal/EncounterFormModal";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const COLUMNS = [
  { key: "startDate", label: "Date", sortable: true, width: 110 },
  { key: "encounterClass", label: "Type", sortable: true, width: 110 },
  { key: "patientName", label: "Patient", width: 160 },
  { key: "providerName", label: "Doctor", width: 160 },
  { key: "organizationName", label: "Facility", width: 180 },
  { key: "description", label: "Description", width: 180 },
  {
    key: "duration",
    label: "Duration",
    sortable: true,
    width: 140,
    align: "center" as const,
  },
  { key: "actions", label: "Actions", width: 110, align: "center" as const },
];

function EncountersPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const dispatch = useAppDispatch();
  const classes = useClasses(EncountersPageStyles, { name: "EncountersPage" });

  const { items, total, loading, resources, resourcesLoading } = useSelector(
    (state: RootState) => state.encounters,
  );
  const role = useSelector((state: RootState) => state.auth.user?.role);
  const canManage = role === "MANAGER" || role === "DOCTOR";

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<EncounterListItem | null>(null);
  const [deleting, setDeleting] = useState<EncounterListItem | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (!resources) dispatch(fetchEncounterResources());
  }, [dispatch, resources]);

  const page = Math.max(1, parseInt(searchParams.get("page") ?? "1", 10));
  const rows = parseInt(searchParams.get("rows") ?? "25", 10);
  const sortBy = searchParams.get("sortBy") ?? "startDate";
  const sortType = (searchParams.get("sortType") ?? "desc") as "asc" | "desc";

  useEffect(() => {
    dispatch(
      fetchEncounters({
        search: searchParams.get("search") || undefined,
        encounterClass: searchParams
          .get("encounterClass")
          ?.split(",")
          .filter(Boolean),
        dateFrom: searchParams.get("dateFrom") || undefined,
        dateTo: searchParams.get("dateTo") || undefined,
        page,
        rows,
        sortBy,
        sortType,
      }),
    );
  }, [dispatch, searchParams, page, rows, sortBy, sortType]);

  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const [encounterClass, setEncounterClass] = useState<string[]>(
    searchParams.get("encounterClass")?.split(",").filter(Boolean) ?? [],
  );
  const [dateFrom, setDateFrom] = useState(searchParams.get("dateFrom") ?? "");
  const [dateTo, setDateTo] = useState(searchParams.get("dateTo") ?? "");

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
    router.push(`/encounters?${p.toString()}`);
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
    if (encounterClass.length)
      p.set("encounterClass", encounterClass.join(","));
    else p.delete("encounterClass");
    if (dateFrom) p.set("dateFrom", dateFrom);
    else p.delete("dateFrom");
    if (dateTo) p.set("dateTo", dateTo);
    else p.delete("dateTo");
    p.set("page", "1");
    router.push(`/encounters?${p.toString()}`);
  };

  const refreshList = () =>
    dispatch(
      fetchEncounters({
        search: searchParams.get("search") || undefined,
        encounterClass: searchParams
          .get("encounterClass")
          ?.split(",")
          .filter(Boolean),
        dateFrom: searchParams.get("dateFrom") || undefined,
        dateTo: searchParams.get("dateTo") || undefined,
        page,
        rows,
        sortBy,
        sortType,
      }),
    );

  const handleSubmit = async (value: EncounterFormValue) => {
    setSubmitting(true);
    setFormError(null);
    const { patientId: pid, ...rest } = value;
    const result = await (editing
      ? dispatch(
          updateEncounter({ encounterId: editing.encounterId, payload: rest }),
        )
      : dispatch(createEncounter({ patientId: pid!, ...rest })));
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
      router.push(`/encounters?${p.toString()}`);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleting) return;
    setSubmitting(true);
    const result = await dispatch(deleteEncounter(deleting.encounterId));
    setSubmitting(false);
    setDeleting(null);
    if (!(result as any).error) refreshList();
  };

  const renderRow = (e: EncounterListItem, i: number) => (
    <StyledTableRow key={e.encounterId} index={i}>
      <TableCell sx={{ ...bodyCellSx, color: theme.colors.text.secondary }}>
        {formatDate(e.startDate)}
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <span className={classes.encounterTypeBadge}>{e.encounterClass}</span>
      </TableCell>
      <TableCell
        sx={{
          ...bodyCellSx,
          fontWeight: theme.typography.fontWeight.semibold,
          color: theme.colors.primary.main,
        }}
      >
        <TruncatedText text={e.patientName} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <TruncatedText text={e.providerName} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <TruncatedText text={e.organizationName ?? "-"} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <TruncatedText text={e.description} />
      </TableCell>
      <TableCell sx={bodyCellSx} align="center">
        {e.duration != null ? `${Math.round(e.duration)} min` : "-"}
      </TableCell>
      <TableCell sx={bodyCellSx} align="center">
        <IconButton
          size="small"
          onClick={() => router.push(`/encounters/${e.encounterId}`)}
          aria-label="View visit"
          sx={{
            padding: "4px",
            color: theme.colors.primary.main,
            "&:hover": { backgroundColor: "rgba(0, 103, 128, 0.08)" },
          }}
        >
          <VisibilityOutlinedIcon sx={{ fontSize: "1.05rem" }} />
        </IconButton>
        {canManage && (
          <>
            <IconButton
              size="small"
              onClick={() => {
                setEditing(e);
                setFormError(null);
                setModalOpen(true);
              }}
              aria-label="Edit visit"
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
              onClick={() => setDeleting(e)}
              aria-label="Delete visit"
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

  const classOptions = resources.encounterClasses.map((c) => ({
    value: c.value,
    label: c.value.charAt(0).toUpperCase() + c.value.slice(1),
  }));

  return (
    <div className={classes.pageContainer}>
      {canManage && (
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
              height: "40px",
            }}
          >
            <AddIcon sx={{ fontSize: "1.05rem" }} />
            Add visit
          </StyledButton>
        </div>
      )}

      <EncounterFormModal
        open={modalOpen}
        showPatientId={!editing}
        initial={
          editing
            ? {
                startDate: editing.startDate,
                endDate:
                  editing.duration != null
                    ? new Date(
                        new Date(editing.startDate).getTime() +
                          editing.duration * 60 * 1000,
                      ).toISOString()
                    : undefined,
                encounterClass: editing.encounterClass,
                description: editing.description,
                reasonDescription: editing.reasonDescription,
              }
            : null
        }
        submitting={submitting}
        errorMessage={formError}
        onClose={() => {
          setModalOpen(false);
          setEditing(null);
        }}
        onSubmit={handleSubmit}
      />

      <FormModal
        open={!!deleting}
        title="Delete visit"
        submitLabel="Delete"
        destructive
        submitting={submitting}
        onClose={() => setDeleting(null)}
        onSubmit={handleConfirmDelete}
        layout="single"
      >
        <div>
          Delete visit <strong>{deleting?.description}</strong>? This cannot be
          undone. Visits with linked records cannot be deleted.
        </div>
      </FormModal>

      <div className={classes.filterBar}>
        <StyledInput
          label="Search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by patient name"
          startIcon={
            <SearchIcon sx={{ fontSize: "1.1rem", color: "#6b7280" }} />
          }
          clearIcon
          onClear={() => setSearch("")}
          height={"40px"}
        />

        <StyledMultiDropdown
          label="Type"
          value={encounterClass}
          onChange={(v) => setEncounterClass(v as string[])}
          onClear={() => setEncounterClass([])}
          options={classOptions}
          placeholder="All"
          width="auto"
        />

        <StyledDatePicker
          label="From"
          value={dateFrom}
          onChange={setDateFrom}
          fullWidth
          height={"40px"}
        />

        <StyledDatePicker
          label="To"
          value={dateTo}
          onChange={setDateTo}
          fullWidth
          height={"40px"}
        />

        <StyledButton
          onClick={handleSearch}
          sx={{
            alignSelf: "flex-end",
            background: theme.colors.button.primary,
            boxShadow: "none",
            border: "none",
            color: "#ffffff",
            height: "40px !important",
            whiteSpace: "nowrap",
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
          emptyMessage="No visits match the selected filters."
        />
      </div>
    </div>
  );
}

export default function EncountersPage() {
  return (
    <Suspense>
      <EncountersPageContent />
    </Suspense>
  );
}
