import api from "./api.js";

export async function listProducts(params = {}) {
  const { data } = await api.get("/products", { params });
  return data;
}

export async function getProduct(id) {
  const { data } = await api.get(`/products/${id}`);
  return data;
}

export async function createProduct(payload) {
  const { data } = await api.post("/products", payload);
  return data;
}

export async function updateProduct(id, payload) {
  const { data } = await api.put(`/products/${id}`, payload);
  return data;
}

export async function deleteProduct(id) {
  await api.delete(`/products/${id}`);
}

export async function adjustProductStock(id, payload) {
  const { data } = await api.post(`/products/${id}/stock`, payload);
  return data;
}

export async function getProductMovements(id, limit = 50) {
  const { data } = await api.get(`/products/${id}/movements`, { params: { limit } });
  return data;
}

export async function getInventorySummary() {
  const { data } = await api.get("/inventory/summary");
  return data;
}
