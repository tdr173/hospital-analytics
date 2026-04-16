"use client";

import { Suspense, useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useSearchParams, useRouter } from "next/navigation";
import TableCell from "@mui/material/TableCell";

import { RootState, AppDispatch } from "@/store";
import { fetchOrganizations, fetchOrganizationResources } from "@/store/slices/organizations/thunks";
import { OrganizationListItem } from "@/models/generic/organizations";

import StyledTable, {
  StyledTableRow,
  bodyCellSx,
} from "@/components/generic_components/StyledTable/StyledTable";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import SearchIcon from "@mui/icons-material/Search";
import StyledDropdown from "@/components/generic_components/StyledDropdown/StyledDropdown";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import useClasses from "@/utils/useClasses";
import { OrganizationsPageStyles } from "./styles";
import theme from "@/utils/theme";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const COLUMNS = [
  { key: "name", label: "Name", sortable: true, width: 250 },
  { key: "city", label: "City", sortable: true, width: 160 },
  { key: "phone", label: "Phone", width: 140 },
  { key: "providerCount", label: "Providers", sortable: true, width: 100, align: "right" as const },
  { key: "utilization", label: "Utilization", sortable: true, width: 100, align: "right" as const },
];

function OrganizationsPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const dispatch = useAppDispatch();
  const classes = useClasses(OrganizationsPageStyles, { name: "OrganizationsPage" });

  const { items, total, loading, resources, resourcesLoading } = useSelector(
    (state: RootState) => state.organizations,
  );

  useEffect(() => {
    if (!resources) dispatch(fetchOrganizationResources());
  }, [dispatch, resources]);

  const page = Math.max(1, parseInt(searchParams.get("page") ?? "1", 10));
  const rows = parseInt(searchParams.get("rows") ?? "25", 10);
  const sortBy = searchParams.get("sortBy") ?? "name";
  const sortType = (searchParams.get("sortType") ?? "asc") as "asc" | "desc";

  useEffect(() => {
    dispatch(
      fetchOrganizations({
        search: searchParams.get("search") || undefined,
        city: searchParams.get("city") || undefined,
        page,
        rows,
        sortBy,
        sortType,
      }),
    );
  }, [dispatch, searchParams, page, rows, sortBy, sortType]);

  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const [city, setCity] = useState(searchParams.get("city") ?? "");

  const setParam = (updates: Record<string, string | null>, resetPage = true) => {
    const p = new URLSearchParams(searchParams.toString());
    Object.entries(updates).forEach(([k, v]) => {
      if (v) p.set(k, v);
      else p.delete(k);
    });
    if (resetPage) p.set("page", "1");
    router.push(`/organizations?${p.toString()}`);
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
    if (city) p.set("city", city);
    else p.delete("city");
    p.set("page", "1");
    router.push(`/organizations?${p.toString()}`);
  };

  const renderRow = (o: OrganizationListItem, i: number) => (
    <StyledTableRow
      key={o.organizationId}
      index={i}
      onClick={() => router.push(`/organizations/${o.organizationId}`)}
    >
      <TableCell
        sx={{
          ...bodyCellSx,
          fontWeight: theme.typography.fontWeight.semibold,
          color: theme.colors.primary.main,
          cursor: "pointer",
        }}
      >
        <TruncatedText text={o.name ?? "-"} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <TruncatedText text={o.city ?? "-"} />
      </TableCell>
      <TableCell sx={bodyCellSx}>
        {o.phone ?? "-"}
      </TableCell>
      <TableCell sx={bodyCellSx} align="right">
        {o.providerCount}
      </TableCell>
      <TableCell sx={bodyCellSx} align="right">
        {o.utilization}
      </TableCell>
    </StyledTableRow>
  );

  if (resourcesLoading || !resources) {
    return <div className={classes.loading}>Loading...</div>;
  }

  const cityOptions = [
    { value: "", label: "All Cities" },
    ...resources.cities.map((c) => ({ value: c.value, label: c.label })),
  ];

  return (
    <div className={classes.pageContainer}>
      <div className={classes.filterBar}>
        <StyledInput
          label="Search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name or city"
          startIcon={<SearchIcon sx={{ fontSize: "1.1rem", color: "#6b7280" }} />}
          clearIcon
          onClear={() => setSearch("")}
          height={36}
        />

        <StyledDropdown
          label="City"
          value={city}
          onChange={(v) => setCity(v as string)}
          options={cityOptions}
          width="100%"
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
          emptyMessage="No organizations found matching the selected filters."
        />
      </div>
    </div>
  );
}

export default function OrganizationsPage() {
  return (
    <Suspense>
      <OrganizationsPageContent />
    </Suspense>
  );
}
