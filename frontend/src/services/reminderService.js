import api from "./api";

export async function listReminders() {
  const response = await api.get("/reminders");
  return response.data;
}

export async function logReminder(invoiceId, data) {
  const response = await api.post(`/reminders/${invoiceId}/log`, data);
  return response.data;
}
