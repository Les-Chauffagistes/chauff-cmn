import type { TextMapGetter } from "@opentelemetry/api";

// `propagation.extract` a besoin d'un getter explicite pour l'objet Web
// `Headers` (le getter par défaut suppose un objet brut avec `[key]`).
export const headersGetter: TextMapGetter<Headers> = {
  get(carrier, key) {
    return carrier.get(key) ?? undefined;
  },
  keys(carrier) {
    return Array.from(carrier.keys());
  },
};
