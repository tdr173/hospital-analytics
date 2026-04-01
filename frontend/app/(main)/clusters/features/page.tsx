"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState, AppDispatch } from "@/store";
import { getNumericalFeaturesStatistics } from "@/store/slices/clusters/thunks";
import StyledTabs from "@/components/generic_components/StyledTabs/StyledTabs";
import ClusterFeatureChart from "@/components/generic_components/ClusterFeatureChart/ClusterFeatureChart";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const clusterTabs = [
  { name: "CLUSTER SUMMARIES", forward: "/clusters/summaries" },
  { name: "CLUSTER STATISTICS", forward: "/clusters/statistics" },
  { name: "CLUSTER FEATURES", forward: "/clusters/features" },
];

export default function ClusterFeaturesPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.numericalFeatures,
  );
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(getNumericalFeaturesStatistics());
  }, [dispatch]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", fontFamily: "Inter, sans-serif", minWidth: 0 }}>
      <div style={{ padding: "0 16px", overflow: "hidden", minWidth: 0 }}>
        <StyledTabs items={clusterTabs} />
      </div>

      <div style={{ flex: 1, overflow: "auto", padding: "24px 16px" }}>
        {loading && (
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100%", color: "#6b7280" }}>
            Loading feature statistics...
          </div>
        )}
        {error && (
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100%", color: "#EF4444" }}>
            {error}
          </div>
        )}
        {data && (
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(2, 1fr)",
            gap: "24px",
          }}>
            {data.features.map((f) => (
              <ClusterFeatureChart key={f.feature} feature={f.feature} data={f.data} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
