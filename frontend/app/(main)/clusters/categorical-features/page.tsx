"use client";

import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState, AppDispatch } from "@/store";
import { getCategoricalFeaturesStatistics } from "@/store/slices/clusters/thunks";
import StackedBarChartComponent from "@/components/generic_components/StackedBarChartComponent/StackedBarChartComponent";
import useClasses from "@/utils/useClasses";
import { CategoricalFeaturesPageStyles } from "./styles";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

function toTitleCase(str: string): string {
  return str.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}

export default function CategoricalClusterFeaturesPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.categoricalFeatures,
  );
  const dispatch = useAppDispatch();
  const classes = useClasses(CategoricalFeaturesPageStyles, { name: "CategoricalFeaturesPage" });
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!data) dispatch(getCategoricalFeaturesStatistics());
  }, [dispatch]);

  const features = data?.features ?? [];
  const total = features.length;
  const current = features[index];

  const prev = () => setIndex((i) => Math.max(0, i - 1));
  const next = () => setIndex((i) => Math.min(total - 1, i + 1));

  return (
    <div className={classes.container}>
      {loading && <div className={classes.loading}>Loading categorical features...</div>}
      {error && <div className={classes.error}>{error}</div>}
      {current && (
        <>
          <div className={classes.header}>
            <p className={classes.featureTitle}>{toTitleCase(current.feature)}</p>
            <p className={classes.counter}>{index + 1} / {total}</p>
          </div>
          <div className={classes.chartArea}>
            <button
              className={classes.arrow}
              onClick={prev}
              disabled={index === 0}
              aria-label="Previous"
            >
              ‹
            </button>
            <div className={classes.chartWrapper}>
              <StackedBarChartComponent featureData={current} />
            </div>
            <button
              className={classes.arrow}
              onClick={next}
              disabled={index === total - 1}
              aria-label="Next"
            >
              ›
            </button>
          </div>
        </>
      )}
    </div>
  );
}
