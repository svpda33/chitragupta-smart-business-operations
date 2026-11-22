import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Runs an async function when `deps` change and exposes its result.
 *
 * @param {() => Promise<any>} fn  Async loader. Its result becomes `data`.
 * @param {Array} deps             Dependencies that trigger a reload.
 * @returns {{ data: any, error: object|null, loading: boolean, refresh: () => void }}
 *
 * Stale responses (from a previous deps value or an unmounted component)
 * are ignored, so only the latest request can update state.
 */
export function useAsync(fn, deps = []) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.resolve()
      .then(() => fnRef.current())
      .then(
        (result) => {
          if (!cancelled) {
            setData(result);
            setLoading(false);
          }
        },
        (err) => {
          if (!cancelled) {
            setError(err);
            setLoading(false);
          }
        }
      );

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, reloadKey]);

  const refresh = useCallback(() => setReloadKey((key) => key + 1), []);

  return { data, error, loading, refresh };
}
