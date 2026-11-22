import api from "./api";

export async function listInvoices(params = {}) {
  const response = await api.get("/invoices", { params });
  return response.data;
}

export async function getInvoice(id) {
  const response = await api.get(`/invoices/${id}`);
  return response.data;
}

export async function createInvoice(data) {
  const response = await api.post("/invoices", data);
  return response.data;
}

export async function updateInvoice(id, data) {
  const response = await api.put(`/invoices/${id}`, data);
  return response.data;
}

export async function sendInvoice(id) {
  const response = await api.post(`/invoices/${id}/send`);
  return response.data;
}

export async function deleteInvoice(id) {
  await api.delete(`/invoices/${id}`);
}
