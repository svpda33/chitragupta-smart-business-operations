import api from "./api";

export async function getAiStatus() {
  const response = await api.get("/ai/status");
  return response.data;
}

export async function sendChatMessage(message, { conversationId = null, history = [] } = {}) {
  const payload = { message, history };
  if (conversationId != null) {
    payload.conversation_id = conversationId;
  }
  const response = await api.post("/ai/chat", payload, { timeout: 45000 });
  return response.data;
}

export async function listConversations(search = "") {
  const params = {};
  if (search && search.trim()) {
    params.search = search.trim();
  }
  const response = await api.get("/ai/conversations", { params });
  return response.data;
}

export async function createConversation(title = null) {
  const response = await api.post("/ai/conversations", title ? { title } : {});
  return response.data;
}

export async function getConversation(conversationId) {
  const response = await api.get(`/ai/conversations/${conversationId}`);
  return response.data;
}

export async function renameConversation(conversationId, title) {
  const response = await api.patch(`/ai/conversations/${conversationId}`, { title });
  return response.data;
}

export async function deleteConversation(conversationId) {
  await api.delete(`/ai/conversations/${conversationId}`);
}
