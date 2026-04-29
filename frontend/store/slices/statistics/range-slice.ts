import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export type StatisticsRange = "all" | "week" | "month";

interface StatisticsRangeState {
  range: StatisticsRange;
}

const initialState: StatisticsRangeState = {
  range: "all",
};

const statisticsRangeSlice = createSlice({
  name: "statisticsRange",
  initialState,
  reducers: {
    setStatisticsRange(state, action: PayloadAction<StatisticsRange>) {
      state.range = action.payload;
    },
  },
});

export const { setStatisticsRange } = statisticsRangeSlice.actions;
export default statisticsRangeSlice.reducer;
