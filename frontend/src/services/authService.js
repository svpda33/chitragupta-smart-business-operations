import api from "./api.js";

export async function registerUser(payload) {
  const { data } = await api.post("/auth/register", payload);
  return data;
}

export async function loginUser(payload) {
  const { data } = await api.post("/auth/login", payload);
  return data;
}

export async function logoutUser() {
  await api.post("/auth/logout");
}

export async function fetchMe() {
  const { data } = await api.get("/auth/me");
  return data;
}

export async function forgotPassword(email) {
  const { data } = await api.post("/auth/forgot-password", { email });
  return data;
}

export async function completeOnboarding(payload) {
  const { data } = await api.post("/business/onboarding", payload);
  return data;
}

export async function getBusinessProfile() {
  const { data } = await api.get("/business/profile");
  return data;
}

export async function updateBusinessProfile(payload) {
  const { data } = await api.put("/business/profile", payload);
  return data;
}
