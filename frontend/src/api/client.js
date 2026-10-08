export const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

async function handleResponse(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // el backend no devolvió JSON (ej. no está corriendo)
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json();
}

async function get(path, params = {}) {
  const query = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ""),
  ).toString();
  const res = await fetch(`${API_BASE_URL}${path}${query ? `?${query}` : ""}`);
  return handleResponse(res);
}

async function post(path, body) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

export function getRoles() {
  return get("/roles/");
}

export function categorizarCv({ candidatoId, hojaDeVidaTexto }) {
  return post("/preseleccion/categorizar", {
    candidato_id: candidatoId ?? null,
    hoja_de_vida_texto: hojaDeVidaTexto ?? null,
  });
}

export function evaluarCv({ candidatoId, hojaDeVidaTexto, rolId }) {
  return post("/preseleccion/evaluar", {
    candidato_id: candidatoId ?? null,
    hoja_de_vida_texto: hojaDeVidaTexto ?? null,
    rol_id: rolId ? Number(rolId) : null,
  });
}

export function getRanking(rolId, top = 5) {
  return get(`/preseleccion/ranking/${rolId}`, { top });
}

export function getDetalleHojaDeVida(cvId, rolId) {
  return get(`/preseleccion/hojas-de-vida/${encodeURIComponent(cvId)}`, { rol_id: rolId });
}

export function crearCandidato({ nombre, email, hojaDeVidaTexto, rolId }) {
  return post("/candidatos/", {
    nombre,
    email,
    hoja_de_vida_texto: hojaDeVidaTexto,
    rol_id: rolId ? Number(rolId) : null,
  });
}

export function getResumenDatasets() {
  return get("/datasets/");
}

export function listarDataset(nombre, { rol, apto, q, limit, offset } = {}) {
  return get(`/datasets/${nombre}`, { rol, apto, q, limit, offset });
}

export function getCvAleatorio(rol) {
  return get("/datasets/seleccion/aleatorio", { rol });
}

export function compararCvs({ rolId, a, b }) {
  return post("/competencia/comparar", { rol_id: Number(rolId), a, b });
}

export function jugarTorneo({ rolId, cvIds, top = 5, semilla }) {
  return post("/competencia/torneo", {
    rol_id: Number(rolId),
    cv_ids: cvIds ?? null,
    top,
    semilla: semilla ?? null,
  });
}

export function getModeloCompetencia() {
  return get("/competencia/modelo");
}
