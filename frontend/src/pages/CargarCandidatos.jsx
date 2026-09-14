import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getRoles, categorizarCv } from "../api/client.js";
import Dropzone from "../components/Dropzone.jsx";
import "./CargarCandidatos.css";

const MIN_TEXTO = 20;

export default function CargarCandidatos() {
  const [searchParams] = useSearchParams();
  const [roles, setRoles] = useState([]);
  const [rolesStatus, setRolesStatus] = useState("loading"); // loading | success | error
  const [selectedRolId, setSelectedRolId] = useState(searchParams.get("rolId") ?? "");
  const [file, setFile] = useState(null);
  const [cvTexto, setCvTexto] = useState("");
  const [evalStatus, setEvalStatus] = useState("idle"); // idle | loading | success | error
  const [resultado, setResultado] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    getRoles()
      .then((data) => {
        setRoles(data);
        setRolesStatus("success");
      })
      .catch(() => setRolesStatus("error"));
  }, []);

  async function handleEvaluar() {
    setEvalStatus("loading");
    setErrorMessage("");
    try {
      const data = await categorizarCv({ hojaDeVidaTexto: cvTexto });
      setResultado(data);
      setEvalStatus("success");
    } catch (err) {
      setErrorMessage(err.message);
      setEvalStatus("error");
    }
  }

  const textoValido = cvTexto.trim().length >= MIN_TEXTO;

  return (
    <div className="cargar-page">
      <header className="page-header">
        <h1>Cargar candidatos</h1>
        <p className="page-header__subtitle">
          Selecciona el rol destino, adjunta el CV y evalúa con IA para conocer el rol que el
          modelo predice a partir del texto.
        </p>
      </header>

      <section className="cargar-section">
        <label className="cargar-field">
          <span>Rol destino</span>
          {rolesStatus === "loading" && <p className="cargar-field__hint">Cargando roles…</p>}
          {rolesStatus === "error" && (
            <p className="cargar-field__hint cargar-field__hint--error">
              No se pudo cargar la lista de roles desde el backend (http://127.0.0.1:8000).
            </p>
          )}
          {rolesStatus === "success" && (
            <select value={selectedRolId} onChange={(e) => setSelectedRolId(e.target.value)}>
              <option value="">Selecciona un rol…</option>
              {roles.map((rol) => (
                <option key={rol.id} value={rol.id}>
                  {rol.nombre}
                </option>
              ))}
            </select>
          )}
        </label>
      </section>

      <section className="cargar-section">
        <span className="cargar-field__label">Archivo del CV</span>
        <Dropzone file={file} onFileSelected={setFile} />
        {/* TODO: extracción de texto desde PDF/DOCX */}
      </section>

      <section className="cargar-section">
        <label className="cargar-field">
          <span>Texto del CV</span>
          <textarea
            rows={8}
            value={cvTexto}
            onChange={(e) => setCvTexto(e.target.value)}
            placeholder="Pega aquí el texto plano de la hoja de vida (mínimo 20 caracteres)…"
          />
        </label>

        <button
          type="button"
          className="btn btn--accent"
          disabled={!textoValido || evalStatus === "loading"}
          onClick={handleEvaluar}
        >
          {evalStatus === "loading" ? "Evaluando…" : "Evaluar con IA"}
        </button>
      </section>

      {evalStatus === "error" && (
        <div className="error-banner">
          <p>No se pudo categorizar el CV. Detalle: {errorMessage}</p>
        </div>
      )}

      {evalStatus === "success" && resultado && (
        <section className="resultado-card">
          <span className="resultado-card__label">Rol predicho por la IA</span>
          <span className="resultado-card__valor">{resultado.rol_predicho}</span>
        </section>
      )}
    </div>
  );
}
