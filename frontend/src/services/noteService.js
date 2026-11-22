import api from "./api.js";

export async function listNotes(params = {}) {
  const { data } = await api.get("/notes", { params });
  return data;
}

export async function getNote(id) {
  const { data } = await api.get(`/notes/${id}`);
  return data;
}

export async function createNote(payload) {
  const { data } = await api.post("/notes", payload);
  return data;
}

export async function updateNote(id, payload) {
  const { data } = await api.put(`/notes/${id}`, payload);
  return data;
}

export async function deleteNote(id) {
  await api.delete(`/notes/${id}`);
}
