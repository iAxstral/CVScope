const API_BASE_URL = "http://127.0.0.1:8000";

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

export async function getRoles() {
  const res = await fetch(`${API_BASE_URL}/roles/`);
  return handleResponse(res);
}

export async function categorizarCv({ candidatoId, hojaDeVidaTexto }) {
  const res = await fetch(`${API_BASE_URL}/preseleccion/categorizar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      candidato_id: candidatoId ?? null,
      hoja_de_vida_texto: hojaDeVidaTexto ?? null,
    }),
  });
  return handleResponse(res);
}
