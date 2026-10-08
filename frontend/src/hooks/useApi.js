import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Ejecuta una llamada a la API y expone su estado (loading | success | error).
 * La llamada se repite cada vez que cambia algún valor de `deps` o se invoca `reload`.
 */
export default function useApi(fetcher, deps = []) {
  const [state, setState] = useState({ status: "loading", data: null, error: "" });
  const [intento, setIntento] = useState(0);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  useEffect(() => {
    let vigente = true;
    setState((prev) => ({ ...prev, status: "loading", error: "" }));
    fetcherRef
      .current()
      .then((data) => vigente && setState({ status: "success", data, error: "" }))
      .catch((err) => vigente && setState({ status: "error", data: null, error: err.message }));
    return () => {
      vigente = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, intento]);

  const reload = useCallback(() => setIntento((n) => n + 1), []);

  return { ...state, reload };
}
