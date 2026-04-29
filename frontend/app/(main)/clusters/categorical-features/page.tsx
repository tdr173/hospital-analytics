"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState, AppDispatch } from "@/store";
import { getCategoricalFeaturesStatistics } from "@/store/slices/clusters/thunks";
import StackedBarChartComponent from "@/components/generic_components/StackedBarChartComponent/StackedBarChartComponent";
import useClasses from "@/utils/useClasses";
import { CategoricalFeaturesPageStyles } from "./styles";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function CategoricalClusterFeaturesPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.categoricalFeatures,
  );
  const dispatch = useAppDispatch();
  const classes = useClasses(CategoricalFeaturesPageStyles, {
    name: "CategoricalFeaturesPage",
  });

  useEffect(() => {
    if (!data) dispatch(getCategoricalFeaturesStatistics());
  }, [dispatch]);

  return (
    <div className={classes.container}>
      {loading && (
        <div className={classes.loading}>Loading categorical features...</div>
      )}
      {error && <div className={classes.error}>{error}</div>}
      {data && (
        <div className={classes.grid}>
          {data.features.map((f) => (
            <StackedBarChartComponent key={f.feature} featureData={f} />
          ))}
        </div>
      )}
    </div>
  );
}
