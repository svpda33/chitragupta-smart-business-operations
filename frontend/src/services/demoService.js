import api from "./api";

export async function resetAndSeedDemo(force = true) {
  const response = await api.post("/demo/seed", null, { params: { force } });
  return response.data;
}
