"use client";

import { Suspense, useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useSearchParams, useRouter } from "next/navigation";
import TableCell from "@mui/material/TableCell";

import { RootState, AppDispatch } from "@/store";
import { fetchProviders, fetchProviderResources } from "@/store/slices/providers/thunks";
import { ProviderListItem } from "@/models/generic/providers";

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
  { key: "lastName", label: "Name", sortable: true, width: 200 },
  { key: "speciality", label: "Speciality", sortable: true, width: 180 },
  { key: "gender", label: "Gender", width: 80 },
  { key: "city", label: "City", sortable: true, width: 140 },
  { key: "organizationName", label: "Organization", width: 200 },
  { key: "encounters", label: "Encounters", sortable: true, width: 100, align: "right" as const },
];

function GenderBadge({ gender, classes }: { gender: string | null; classes: any }) {
  if (!gender) return <span className={classes.genderBadgeEmpty}>-</span>;
  const isFemale = gender === "F";
  return (
    <span className={isFemale ? classes.genderBadgeFemale : classes.genderBadgeMale}>
      {isFemale ? "F" : "M"}
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

  const setParam = (updates: Record<string, string | null>, resetPage = true) => {
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

  const renderRow = (p: ProviderListItem, i: number) => (
    <StyledTableRow
      key={p.providerId}
      index={i}
      onClick={() => router.push(`/providers/${p.providerId}`)}
    >
      <TableCell
        sx={{
          ...bodyCellSx,
          fontWeight: theme.typography.fontWeight.semibold,
          color: theme.colors.primary.main,
          cursor: "pointer",
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
    </StyledTableRow>
  );

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
          placeholder="Search providers by name"
          startIcon={<SearchIcon sx={{ fontSize: "1.1rem", color: "#6b7280" }} />}
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
          label="Speciality"
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
          emptyMessage="No providers found matching the selected filters."
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
