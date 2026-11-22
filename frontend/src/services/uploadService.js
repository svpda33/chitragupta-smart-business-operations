import api from "./api.js";

export async function uploadBusinessLogo(file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/uploads/business-logo", form);
  return data;
}

export async function deleteBusinessLogo() {
  await api.delete("/uploads/business-logo");
}

export async function uploadProductImage(productId, file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post(`/uploads/products/${productId}`, form);
  return data;
}

export async function deleteProductImage(productId) {
  await api.delete(`/uploads/products/${productId}`);
}
