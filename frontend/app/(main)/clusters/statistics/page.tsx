"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState, AppDispatch } from "@/store";
import { getClusterStatistics } from "@/store/slices/clusters/thunks";
import ScatterPlotComponent from "@/components/generic_components/ScatterPlotComponent/ScatterPlotComponent";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function ClusterStatisticsPage() {
  const { data, loading, error } = useSelector((state: RootState) => state.pcaScatter);
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (!data) dispatch(getClusterStatistics());
  }, [dispatch]);

  return (
    <div style={{ padding: "24px 16px", display: "flex", flexDirection: "column", gap: "24px", fontFamily: "Inter, sans-serif" }}>
      {loading && (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "200px", color: "#6b7280" }}>
          Loading...
        </div>
      )}
      {error && (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "200px", color: "#EF4444" }}>
          {error}
        </div>
      )}
      {data && (
        <>
          <ScatterPlotComponent
            points={data.points}
            title="Patient Clusters: PCA Projection"
            clusterColors={data.cluster_colors}
          />

          <div style={{ backgroundColor: "#ffffff", borderRadius: 12, boxShadow: "0 1px 4px rgba(0,0,0,0.08)", padding: "16px" }}>
            <p style={{ fontFamily: "Inter, sans-serif", fontSize: "1rem", fontWeight: 600, color: "#191c1e", margin: "0 0 8px 0" }}>
              Cluster Heatmap
            </p>
            {data.heatmap && (
              <img
                src={`data:image/png;base64,${data.heatmap}`}
                alt="Cluster Heatmap"
                style={{ width: "100%", borderRadius: 8, display: "block" }}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
}
