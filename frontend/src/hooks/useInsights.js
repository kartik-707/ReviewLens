/**
 * useInsights.js
 * Custom React hook that wraps the fetchInsights API call with
 * loading / error / data state management.
 */
import { useState, useCallback } from "react";
import { fetchInsights } from "../api";

export default function useInsights() {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);
  const [queried, setQueried] = useState(false);

  const search = useCallback(async (productId) => {
    const id = productId.trim();
    if (!id) return;

    setLoading(true);
    setError(null);
    setData(null);
    setQueried(true);

    try {
      const result = await fetchInsights(id);
      setData(result);
    } catch (err) {
      setError(err.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, queried, search };
}
