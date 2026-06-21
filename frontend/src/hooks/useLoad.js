import { useEffect, useState } from "react";
import { normalizeApiError } from "../utils/format";

export function useLoad(loader, deps = [], options = {}) {
  const { enabled = true, initialData = null } = options;
  const [state, setState] = useState({
    data: initialData,
    loading: Boolean(enabled),
    error: "",
  });

  useEffect(() => {
    if (!enabled) {
      setState((current) => ({ ...current, loading: false }));
      return undefined;
    }

    let active = true;
    setState((current) => ({ ...current, loading: true, error: "" }));

    loader()
      .then((data) => {
        if (active) setState({ data, loading: false, error: "" });
      })
      .catch((error) => {
        if (active) {
          setState({
            data: initialData,
            loading: false,
            error: normalizeApiError(error.message),
          });
        }
      });

    return () => {
      active = false;
    };
  }, deps);

  return state;
}
