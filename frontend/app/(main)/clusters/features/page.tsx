"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState, AppDispatch } from "@/store";
import { getNumericalFeaturesStatistics } from "@/store/slices/clusters/thunks";
import StyledTabs from "@/components/generic_components/StyledTabs/StyledTabs";
import ClusterFeatureChart from "@/components/generic_components/ClusterFeatureChart/ClusterFeatureChart";
import useClasses from "@/utils/useClasses";
import { ClusterFeaturesPageStyles } from "./styles";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const clusterTabs = [
  { name: "PATIENT GROUPS", forward: "/clusters/summaries" },
  { name: "GROUP STATISTICS", forward: "/clusters/statistics" },
  { name: "GROUP FEATURES", forward: "/clusters/features" },
];

export default function ClusterFeaturesPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.numericalFeatures,
  );
  const dispatch = useAppDispatch();
  const classes = useClasses(ClusterFeaturesPageStyles, { name: "ClusterFeaturesPage" });

  useEffect(() => {
    dispatch(getNumericalFeaturesStatistics());
  }, [dispatch]);

  return (
    <div className={classes.container}>
      <div className={classes.tabsWrapper}>
        <StyledTabs items={clusterTabs} />
      </div>

      <div className={classes.content}>
        {loading && (
          <div className={classes.loading}>
            Loading group features...
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
              <ClusterFeatureChart key={f.feature} feature={f.feature} data={f.data} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
