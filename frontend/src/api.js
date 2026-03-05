/**
 * api.js – centralised API client
 * Connects to the Python backend at API_BASE.
 */
const API_BASE = import.meta?.env?.VITE_API_URL ?? "http://localhost:8000";

export async function fetchInsights(productId) {
  const res = await fetch(`${API_BASE}/api/insights/${encodeURIComponent(productId)}`);
  const json = await res.json();
  if (!res.ok) throw new Error(json.detail ?? `HTTP ${res.status}`);
  if (json.status === "insufficient_data") throw new Error(json.message);
  return json;
}

export async function fetchProducts() {
  const res = await fetch(`${API_BASE}/api/products`);
  if (!res.ok) throw new Error("Failed to load product list");
  return res.json();
}
