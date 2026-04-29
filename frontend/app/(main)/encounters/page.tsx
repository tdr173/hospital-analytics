"use client";

import { Suspense, useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useSearchParams, useRouter } from "next/navigation";
import TableCell from "@mui/material/TableCell";
import IconButton from "@mui/material/IconButton";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";

import { RootState, AppDispatch } from "@/store";
import {
  fetchEncounters,
  fetchEncounterResources,
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
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import useClasses from "@/utils/useClasses";
import { EncountersPageStyles } from "./styles";
import theme from "@/utils/theme";
import { formatDate } from "@/utils/functions";

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
  { key: "actions", label: "Actions", width: 80, align: "center" as const },
];

function EncountersPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const dispatch = useAppDispatch();
  const classes = useClasses(EncountersPageStyles, { name: "EncountersPage" });

  const { items, total, loading, resources, resourcesLoading } = useSelector(
    (state: RootState) => state.encounters,
  );

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
          height={36}
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
          height={36}
        />

        <StyledDatePicker
          label="To"
          value={dateTo}
          onChange={setDateTo}
          fullWidth
          height={36}
        />

        <StyledButton
          onClick={handleSearch}
          sx={{
            alignSelf: "flex-end",
            background: theme.colors.button.primary,
            boxShadow: "none",
            border: "none",
            color: "#ffffff",
            height: "36px !important",
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
