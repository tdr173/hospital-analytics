"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState, AppDispatch } from "@/store";
import { getCategoricalFeaturesStatistics } from "@/store/slices/clusters/thunks";
import StackedBarChartComponent from "@/components/generic_components/StackedBarChartComponent/StackedBarChartComponent";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function CategoricalClusterFeaturesPage() {
  const { data, loading, error } = useSelector((state: RootState) => state.categoricalFeatures);
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (!data) dispatch(getCategoricalFeaturesStatistics());
  }, [dispatch]);

  return (
    <div style={{ padding: "24px 16px", fontFamily: "Inter, sans-serif" }}>
      {loading && (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "200px", color: "#6b7280" }}>
          Loading categorical features...
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
            <StackedBarChartComponent key={f.feature} featureData={f} />
          ))}
        </div>
      )}
    </div>
  );
}
