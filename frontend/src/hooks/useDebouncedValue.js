import { useEffect, useState } from "react";

/**
 * Returns `value` after it has stayed unchanged for `delay` milliseconds.
 *
 * @param {any} value
 * @param {number} [delay=300]
 */
export function useDebouncedValue(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
