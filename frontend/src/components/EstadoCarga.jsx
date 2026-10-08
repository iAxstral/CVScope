import { API_BASE_URL } from "../api/client.js";

export function Cargando({ texto = "Cargando…" }) {
  return (
    <p className="loading-text" role="status">
      <span className="loading-text__dot" />
      {texto}
    </p>
  );
}

export function ErrorCarga({ mensaje, onRetry }) {
  return (
    <div className="error-banner" role="alert">
      <p>
        No se pudo obtener la información del backend ({API_BASE_URL}). Detalle: {mensaje}
      </p>
      {onRetry && (
        <button type="button" className="btn btn--ghost" onClick={onRetry}>
          Reintentar
        </button>
      )}
    </div>
  );
}
