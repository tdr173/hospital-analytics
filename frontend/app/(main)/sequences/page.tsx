"use client";

import { useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState, AppDispatch } from "@/store";
import {
  fetchSequences,
  fetchSequenceResources,
  getSequenceAiAnalysis,
} from "@/store/slices/sequences/thunks";
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

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [minLength, setMinLength] = useState(3);
  const [sortBy, setSortBy] = useState("support");
  const [sortType, setSortType] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  useEffect(() => {
    dispatch(fetchSequenceResources());
  }, [dispatch]);

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
      }),
    );
  }, [dispatch, debouncedSearch, effectiveMinLength, sortBy, sortType, page]);

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

  const sequencesById = useMemo(() => {
    const map: Record<number, NonNullable<typeof list>["items"][number]> = {};
    if (list) {
      for (const item of list.items) map[item.id] = item;
    }
    return map;
  }, [list]);

  const handleAnalyse = (patternId: number) => {
    dispatch(openSequenceAnalysis(patternId));
    if (!aiCache[patternId]) {
      dispatch(getSequenceAiAnalysis(patternId));
    }
  };

  const items = list?.items ?? [];
  const total = list?.total ?? 0;
  const colors = resources?.colors ?? {};

  return (
    <div className={classes.container}>
      <div className={classes.content}>
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
        />

        {listError && <div className={classes.error}>{listError}</div>}

        {(listLoading || resourcesLoading) && !list && (
          <div className={classes.status}>Loading sequences...</div>
        )}

        {!listLoading && !listError && items.length === 0 && (
          <div className={classes.empty}>
            No sequences match the current filters.
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
        />
      </div>

      <SequenceAiModal sequencesById={sequencesById} colors={colors} />
    </div>
  );
}
