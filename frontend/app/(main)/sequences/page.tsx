"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
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
const SEARCH_DEBOUNCE_MS = 300;

type ActiveTab = "global" | "cluster";

export default function SequencesPage() {
  const classes = useClasses(SequencesPageStyles, { name: "SequencesPage" });
  const dispatch = useAppDispatch();

  const resources = useSelector((s: RootState) => s.sequenceResources.data);
  const resourcesLoading = useSelector(
    (s: RootState) => s.sequenceResources.loading,
  );
  const list = useSelector((s: RootState) => s.sequenceList.data);
  const listLoading = useSelector((s: RootState) => s.sequenceList.loading);
  const listError = useSelector((s: RootState) => s.sequenceList.error);
  const aiCache = useSelector((s: RootState) => s.sequenceAi.cache);
  const clustersData = useSelector((s: RootState) => s.clusters.data);

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [minLength, setMinLength] = useState(3);
  const [sortBy, setSortBy] = useState("support");
  const [sortType, setSortType] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [activeTab, setActiveTab] = useState<ActiveTab>("global");
  const [selectedClusterIds, setSelectedClusterIds] = useState<number[]>([]);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    dispatch(fetchSequenceResources());
  }, [dispatch]);

  useEffect(() => {
    contentRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  }, [page]);

  useEffect(() => {
    const handle = setTimeout(() => setDebouncedSearch(search), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [search]);

  const effectiveMinLength = useMemo(() => {
    if (!resources) return minLength;
    return Math.min(Math.max(minLength, resources.minLength), resources.maxLength);
  }, [minLength, resources]);

  useEffect(() => {
    dispatch(
      fetchSequences({
        search: debouncedSearch || undefined,
        minLength: effectiveMinLength,
        sortBy,
        sortType,
        page,
        rows: ROWS_PER_PAGE,
        clusterLabels: activeTab === "cluster" ? selectedClusterIds : undefined,
      }),
    );
  }, [dispatch, debouncedSearch, effectiveMinLength, sortBy, sortType, page, activeTab, selectedClusterIds]);

  const handleTabChange = (_: React.SyntheticEvent, value: ActiveTab) => {
    setActiveTab(value);
    setPage(1);
    if (value === "cluster" && !clustersData) {
      dispatch(getClustersOverview());
    }
  };

  const handleSearchChange = (value: string) => {
    setSearch(value);
    setPage(1);
  };
  const handleMinLengthChange = (value: number) => {
    setMinLength(value);
    setPage(1);
  };
  const handleSortByChange = (value: string) => {
    setSortBy(value);
    setPage(1);
  };
  const handleSortTypeChange = (value: "asc" | "desc") => {
    setSortType(value);
    setPage(1);
  };
  const handleClusterIdsChange = (ids: number[]) => {
    setSelectedClusterIds(ids);
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
      <div className={classes.content} ref={contentRef}>
        <Tabs
          value={activeTab}
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
          sortBy={sortBy}
          sortType={sortType}
          resources={resources}
          onSearchChange={handleSearchChange}
          onMinLengthChange={handleMinLengthChange}
          onSortByChange={handleSortByChange}
          onSortTypeChange={handleSortTypeChange}
          activeTab={activeTab}
          clusters={allClusters}
          selectedClusterIds={selectedClusterIds}
          onClusterIdsChange={handleClusterIdsChange}
        />

        {listError && <div className={classes.error}>{listError}</div>}

        {(listLoading || resourcesLoading) && !list && (
          <div className={classes.status}>Loading care sequences...</div>
        )}

        {!listLoading && !listError && !!list && items.length === 0 && (
          <div className={classes.empty}>
            {activeTab === "cluster" && selectedClusterIds.length === 0
              ? "Select one or more clusters to view their sequences."
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
