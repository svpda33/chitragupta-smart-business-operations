import api from "./api";

export async function getCashFlowForecast(params = {}) {
  const response = await api.get("/cashflow/forecast", { params });
  return response.data;
}

export async function simulateCashFlow(data) {
  const response = await api.post("/cashflow/simulate", data);
  return response.data;
}
