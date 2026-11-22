import { useEffect, useState } from "react";
import { getHealth } from "../services/healthService.js";

export default function useHealth() {
  const [state, setState] = useState({ status: "loading", detail: "" });

  useEffect(() => {
    let cancelled = false;

    getHealth()
      .then((data) => {
        if (cancelled) return;
        const healthy = data?.status === "ok" && data?.database === "ok";
        setState({
          status: healthy ? "ok" : "error",
          detail: healthy ? "" : "The backend reported a problem.",
        });
      })
      .catch((error) => {
        if (cancelled) return;
        setState({ status: "error", detail: error.message });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
