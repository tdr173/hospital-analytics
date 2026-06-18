"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useRouter } from "next/navigation";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import { RootState, AppDispatch } from "@/store";
import {
  fetchSequences,
  fetchSequenceResources,
  getSequenceAiAnalysis,
} from "@/store/slices/sequences/thunks";
import { getClustersOverview } from "@/store/slices/clusters/thunks";
import { openSequenceAnalysis } from "@/store/slices/sequences/sequence-ai-slice";
import useClasses from "@/utils/useClasses";
import { SequencesPageStyles } from "./styles";
import SequenceFilters from "./components/SequenceFilters/SequenceFilters";
import SequenceCard from "./components/SequenceCard/SequenceCard";
import SequencePagination from "./components/SequencePagination/SequencePagination";
import SequenceAiModal from "./components/SequenceAiModal/SequenceAiModal";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();
const ROWS_PER_PAGE = 8;

export type SequenceScope = "global" | "cluster";

interface AppliedFilters {
  search: string;
  minLength: number;
  sortBy: string;
  sortType: "asc" | "desc";
  clusterIds: number[];
}

interface Props {
  scope: SequenceScope;
}

export default function SequencesView({ scope }: Props) {
  const classes = useClasses(SequencesPageStyles, { name: "SequencesPage" });
  const dispatch = useAppDispatch();
  const router = useRouter();

  const resources = useSelector((s: RootState) => s.sequenceResources.data);
  const resourcesLoading = useSelector(
    (s: RootState) => s.sequenceResources.loading,
  );
  const list = useSelector((s: RootState) => s.sequenceList.data);
  const listLoading = useSelector((s: RootState) => s.sequenceList.loading);
  const listError = useSelector((s: RootState) => s.sequenceList.error);
  const aiCache = useSelector((s: RootState) => s.sequenceAi.cache);
  const clustersData = useSelector((s: RootState) => s.clusters.data);

  // Draft filter state - what the user is editing in the bar. Nothing is
  // queried from these until the Search button (or Enter) applies them.
  const [search, setSearch] = useState("");
  const [minLength, setMinLength] = useState(3);
  const [sortBy, setSortBy] = useState("support");
  const [sortType, setSortType] = useState<"asc" | "desc">("desc");
  const [selectedClusterIds, setSelectedClusterIds] = useState<number[]>([]);

  // Applied filters - the only thing that drives the fetch (besides paging).
  const [applied, setApplied] = useState<AppliedFilters>({
    search: "",
    minLength: 3,
    sortBy: "support",
    sortType: "desc",
    clusterIds: [],
  });
  const [page, setPage] = useState(1);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    dispatch(fetchSequenceResources());
  }, [dispatch]);

  useEffect(() => {
    if (scope === "cluster" && !clustersData) {
      dispatch(getClustersOverview());
    }
  }, [scope, clustersData, dispatch]);

  useEffect(() => {
    contentRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  }, [page]);

  // Min Steps interval for the active scope: the global range on the Global tab,
  // or the union of the selected clusters' ranges on the Per Cluster tab.
  const scopeRange = useMemo(() => {
    if (!resources) return { minLength: 1, maxLength: 1 };
    const globalRange = {
      minLength: resources.minLength,
      maxLength: resources.maxLength,
    };
    if (scope === "global" || selectedClusterIds.length === 0) {
      return globalRange;
    }
    let min = Infinity;
    let max = -Infinity;
    for (const id of selectedClusterIds) {
      const r = resources.clusterRanges?.[String(id)];
      if (!r) continue;
      if (r.minLength < min) min = r.minLength;
      if (r.maxLength > max) max = r.maxLength;
    }
    if (min === Infinity || max === -Infinity) return globalRange;
    return { minLength: min, maxLength: max };
  }, [resources, scope, selectedClusterIds]);

  const effectiveMinLength = useMemo(() => {
    return Math.min(
      Math.max(minLength, scopeRange.minLength),
      scopeRange.maxLength,
    );
  }, [minLength, scopeRange]);

  useEffect(() => {
    dispatch(
      fetchSequences({
        search: applied.search || undefined,
        minLength: applied.minLength,
        sortBy: applied.sortBy,
        sortType: applied.sortType,
        page,
        rows: ROWS_PER_PAGE,
        clusterLabels: scope === "cluster" ? applied.clusterIds : undefined,
      }),
    );
  }, [dispatch, applied, page, scope]);

  const handleTabChange = (_: React.SyntheticEvent, value: SequenceScope) => {
    if (value === scope) return;
    router.push(value === "global" ? "/sequences/global" : "/sequences/per-cluster");
  };

  // Draft updates only - no fetch until applyFilters runs.
  const handleSearchChange = (value: string) => setSearch(value);
  const handleSearchClear = () => setSearch("");
  const handleMinLengthChange = (value: number) => setMinLength(value);
  const handleSortByChange = (value: string) => setSortBy(value);
  const handleSortTypeChange = (value: "asc" | "desc") => setSortType(value);
  const handleClusterIdsChange = (ids: number[]) => setSelectedClusterIds(ids);

  const applyFilters = () => {
    setApplied({
      search,
      minLength: effectiveMinLength,
      sortBy,
      sortType,
      clusterIds: selectedClusterIds,
    });
    setPage(1);
  };

  const handleAnalyse = (sequence: NonNullable<typeof list>["items"][number]) => {
    dispatch(openSequenceAnalysis(sequence));
    if (!aiCache[sequence.id]) {
      dispatch(getSequenceAiAnalysis(sequence.id));
    }
  };

  const items = list?.items ?? [];
  const total = list?.total ?? 0;
  const colors = resources?.colors ?? {};
  const allClusters = clustersData?.clusters ?? [];

  return (
    <div className={classes.container}>
      <div className={classes.content}>
        <Tabs
          value={scope}
          onChange={handleTabChange}
          sx={{
            minHeight: "36px",
            "& .MuiTabs-indicator": { height: "2px" },
            "& .MuiTab-root": {
              minHeight: "36px",
              textTransform: "none",
              fontWeight: 600,
              fontSize: "0.85rem",
              padding: "6px 20px",
            },
          }}
        >
          <Tab value="global" label="Global" disableRipple />
          <Tab value="cluster" label="Per Cluster" disableRipple />
        </Tabs>

        <SequenceFilters
          search={search}
          minLength={effectiveMinLength}
          rangeMin={scopeRange.minLength}
          rangeMax={scopeRange.maxLength}
          sortBy={sortBy}
          sortType={sortType}
          resources={resources}
          onSearchChange={handleSearchChange}
          onSearchApply={applyFilters}
          onSearchClear={handleSearchClear}
          onMinLengthChange={handleMinLengthChange}
          onSortByChange={handleSortByChange}
          onSortTypeChange={handleSortTypeChange}
          activeTab={scope}
          clusters={allClusters}
          selectedClusterIds={selectedClusterIds}
          onClusterIdsChange={handleClusterIdsChange}
        />

        <div className={classes.scrollArea} ref={contentRef}>
          {listError && <div className={classes.error}>{listError}</div>}

          {(listLoading || resourcesLoading) && !list && (
            <div className={classes.status}>Loading care sequences...</div>
          )}

          {!listLoading && !listError && !!list && items.length === 0 && (
            <div className={classes.empty}>
              {scope === "cluster" && applied.clusterIds.length === 0
                ? "Select one or more clusters, then press Search to view their sequences."
                : "No care sequences match the current filters."}
            </div>
          )}

          {items.length > 0 && (
            <div className={classes.grid}>
              {items.map((seq) => (
                <SequenceCard
                  key={seq.id}
                  sequence={seq}
                  colors={colors}
                  onAnalyse={handleAnalyse}
                />
              ))}
            </div>
          )}
        </div>

        <SequencePagination
          page={page}
          rows={ROWS_PER_PAGE}
          total={total}
          onPageChange={setPage}
          loading={listLoading || !list}
          error={!!listError}
        />
      </div>

      <SequenceAiModal colors={colors} />
    </div>
  );
}
