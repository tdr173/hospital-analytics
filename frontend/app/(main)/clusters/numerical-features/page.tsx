"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState, AppDispatch } from "@/store";
import { getNumericalFeaturesStatistics } from "@/store/slices/clusters/thunks";
import ClusterFeatureChart from "@/components/generic_components/ClusterFeatureChart/ClusterFeatureChart";
import useClasses from "@/utils/useClasses";
import { NumericalFeaturesPageStyles } from "./styles";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function NumericClusterFeaturesPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.numericalFeatures,
  );
  const dispatch = useAppDispatch();
  const classes = useClasses(NumericalFeaturesPageStyles, { name: "NumericalFeaturesPage" });

  useEffect(() => {
    if (!data) dispatch(getNumericalFeaturesStatistics());
  }, [dispatch]);

  return (
    <div className={classes.container}>
      {loading && (
        <div className={classes.loading}>
          Loading feature statistics...
        </div>
      )}
      {error && (
        <div className={classes.error}>
          {error}
        </div>
      )}
      {data && (
        <div className={classes.grid}>
          {data.features.map((f) => (
            <ClusterFeatureChart
              key={f.feature}
              feature={f.feature}
              data={f.data}
              clusterColors={data.cluster_colors}
            />
          ))}
        </div>
      )}
    </div>
  );
}
