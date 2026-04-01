"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState, AppDispatch } from "@/store";
import { getNumericalFeaturesStatistics } from "@/store/slices/clusters/thunks";
import ClusterFeatureChart from "@/components/generic_components/ClusterFeatureChart/ClusterFeatureChart";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function NumericClusterFeaturesPage() {
  const { data, loading, error } = useSelector((state: RootState) => state.numericalFeatures);
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (!data) dispatch(getNumericalFeaturesStatistics());
  }, [dispatch]);

  return (
    <div style={{ padding: "24px 16px", fontFamily: "Inter, sans-serif" }}>
      {loading && (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "200px", color: "#6b7280" }}>
          Loading feature statistics...
        </div>
      )}
      {error && (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "200px", color: "#EF4444" }}>
          {error}
        </div>
      )}
      {data && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "24px" }}>
          {data.features.map((f) => (
            <ClusterFeatureChart key={f.feature} feature={f.feature} data={f.data} clusterColors={data.cluster_colors} />
          ))}
        </div>
      )}
    </div>
  );
}
