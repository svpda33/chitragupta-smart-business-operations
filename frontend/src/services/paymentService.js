import api from "./api";

export async function listPayments(params = {}) {
  const response = await api.get("/payments", { params });
  return response.data;
}

export async function getPayment(id) {
  const response = await api.get(`/payments/${id}`);
  return response.data;
}

export async function createPayment(data) {
  const response = await api.post("/payments", data);
  return response.data;
}

export async function updatePayment(id, data) {
  const response = await api.put(`/payments/${id}`, data);
  return response.data;
}

export async function reversePayment(id, reason) {
  const response = await api.post(`/payments/${id}/reverse`, { reason });
  return response.data;
}
