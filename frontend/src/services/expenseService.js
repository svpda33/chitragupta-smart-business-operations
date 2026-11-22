import api from "./api";

export async function listExpenses() {
  const response = await api.get("/expenses");
  return response.data;
}

export async function createExpense(data) {
  const response = await api.post("/expenses", data);
  return response.data;
}

export async function deleteExpense(id) {
  await api.delete(`/expenses/${id}`);
}
