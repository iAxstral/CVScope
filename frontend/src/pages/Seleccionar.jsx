import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  crearCandidato,
  evaluarCv,
  extraerTexto,
  getCvAleatorio,
  getMotores,
  getRoles,
} from "../api/client.js";
import useApi from "../hooks/useApi.js";
import Dropzone from "../components/Dropzone.jsx";
import RequisitoList from "../components/RequisitoList.jsx";
import ScoreMeter from "../components/ScoreMeter.jsx";
import StatusPill from "../components/StatusPill.jsx";
import { ETIQUETA_ROL } from "../utils/texto.js";
import "./Seleccionar.css";

const MIN_TEXTO = 20;
const AUTO = "auto";
const MOTORES = {
  palabras_clave: "Palabras clave",
  llm: "Gemini (LLM)",
};

export default function Seleccionar() {
  const [searchParams] = useSearchParams();
  const roles = useApi(getRoles);
  const motores = useApi(getMotores);
  const [motor, setMotor] = useState("palabras_clave");
  const [rolId, setRolId] = useState(searchParams.get("rolId") ?? AUTO);
  const [file, setFile] = useState(null);
  const [fileAviso, setFileAviso] = useState("");
  const [cvTexto, setCvTexto] = useState("");
  const [ejemplo, setEjemplo] = useState(null);
  const [evaluacion, setEvaluacion] = useState({ status: "idle", data: null, error: "" });
  const [intento, setIntento] = useState(0);

  const textoValido = cvTexto.trim().length >= MIN_TEXTO;

  async function handleFile(picked) {
    setFile(picked);
    setEjemplo(null);
    setFileAviso("Extrayendo texto…");
    try {
      const datos = await extraerTexto(picked);
      setCvTexto(datos.hoja_de_vida_texto);
      setFileAviso(`Texto extraído (${datos.caracteres} caracteres). Revísalo antes de evaluar.`);
    } catch (err) {
      setFileAviso(`No se pudo extraer el texto: ${err.message}`);
    }
  }

  async function usarEjemplo() {
    const rol = roles.data?.find((r) => String(r.id) === String(rolId));
    try {
      const cv = await getCvAleatorio(rol?.clave);
      setCvTexto(cv.hoja_de_vida_texto);
      setEjemplo(cv);
      setFile(null);
      setFileAviso("");
      setEvaluacion({ status: "idle", data: null, error: "" });
    } catch (err) {
      setEvaluacion({ status: "error", data: null, error: err.message });
    }
  }

  async function handleEvaluar() {
    setIntento((n) => n + 1);
    setEvaluacion({ status: "loading", data: null, error: "" });
    try {
      const data = await evaluarCv({
        hojaDeVidaTexto: cvTexto,
        rolId: rolId === AUTO ? null : rolId,
        motor,
      });
      setEvaluacion({ status: "success", data, error: "" });
    } catch (err) {
      setEvaluacion({ status: "error", data: null, error: err.message });
    }
  }

  const resultado = evaluacion.data;
  const referencia =
    ejemplo &&
    resultado &&
    roles.data?.find((r) => r.id === resultado.rol_id)?.clave === ejemplo.rol
      ? ejemplo
      : null;

  return (
    <div className="sel-page">
      <header className="page-header">
        <h1>Seleccionar hoja de vida</h1>
        <p className="page-header__subtitle">
          Evalúa un CV contra los requisitos mínimos de un rol. Si no eliges el rol, el clasificador
          de IA lo detecta a partir del texto.
        </p>
      </header>

      <div className="sel-page__grid">
        <section className="card sel-form" aria-label="Hoja de vida">
          <label className="field">
            <span>Rol destino</span>
            {roles.status === "error" ? (
              <span className="field__hint sel-form__error">
                No se pudieron cargar los roles: {roles.error}
              </span>
            ) : (
              <select
                className="input"
                value={rolId}
                onChange={(e) => setRolId(e.target.value)}
                disabled={roles.status !== "success"}
              >
                <option value={AUTO}>Detectar automáticamente (clasificador IA)</option>
                {roles.data?.map((rol) => (
                  <option key={rol.id} value={rol.id}>
                    {rol.nombre}
                  </option>
                ))}
              </select>
            )}
          </label>

          <fieldset className="field sel-motor">
            <legend>Motor de evaluación</legend>
            <div className="sel-motor__opciones">
              <label
                className={`sel-motor__opcion ${motor === "palabras_clave" ? "is-active" : ""}`}
              >
                <input
                  type="radio"
                  name="motor"
                  value="palabras_clave"
                  checked={motor === "palabras_clave"}
                  onChange={() => setMotor("palabras_clave")}
                />
                <span>
                  <strong>Palabras clave</strong>
                  <small>Rápido y determinístico</small>
                </span>
              </label>
              <label
                className={`sel-motor__opcion ${motor === "llm" ? "is-active" : ""} ${
                  motores.data?.llm ? "" : "is-disabled"
                }`}
              >
                <input
                  type="radio"
                  name="motor"
                  value="llm"
                  checked={motor === "llm"}
                  disabled={!motores.data?.llm}
                  onChange={() => setMotor("llm")}
                />
                <span>
                  <strong>Gemini (LLM)</strong>
                  <small>
                    {motores.data?.llm
                      ? `Entiende redacciones indirectas · ${motores.data.modelo_llm}`
                      : "No disponible: configura OPENAI_API_KEY en backend/.env"}
                  </small>
                </span>
              </label>
            </div>
          </fieldset>

          <div className="field">
            <span>Archivo del CV</span>
            <Dropzone file={file} onFileSelected={handleFile} hint={fileAviso} />
          </div>

          <label className="field">
            <span className="sel-form__label-row">
              Texto del CV
              <span className="field__hint">{cvTexto.trim().length} caracteres</span>
            </span>
            <textarea
              className="input"
              rows={10}
              value={cvTexto}
              onChange={(e) => {
                setCvTexto(e.target.value);
                setEjemplo(null);
              }}
              placeholder="Pega aquí el texto plano de la hoja de vida (mínimo 20 caracteres)…"
            />
          </label>

          {ejemplo && (
            <p className="field__hint">
              Ejemplo <code>{ejemplo.id}</code> del dataset de selección · rol real:{" "}
              <strong>{ETIQUETA_ROL[ejemplo.rol] ?? ejemplo.rol}</strong> · etiqueta:{" "}
              <strong>{ejemplo.apto ? "apto" : "no apto"}</strong>
            </p>
          )}

          <div className="sel-form__actions">
            <button type="button" className="btn btn--ghost" onClick={usarEjemplo}>
              Usar CV de ejemplo
            </button>
            <button
              type="button"
              className="btn btn--accent"
              disabled={!textoValido || evaluacion.status === "loading"}
              onClick={handleEvaluar}
            >
              {evaluacion.status === "loading" ? "Evaluando…" : "Evaluar hoja de vida"}
            </button>
          </div>
        </section>

        <section className="sel-result" aria-live="polite">
          {evaluacion.status === "idle" && (
            <div className="empty-state sel-result__empty">
              <strong>El resultado aparecerá aquí</strong>
              <p>Verás el rol, el puntaje, si es apto y la evidencia de cada requisito.</p>
            </div>
          )}

          {evaluacion.status === "error" && (
            <div className="error-banner" role="alert">
              <p>
                No se pudo evaluar la hoja de vida. Detalle: {evaluacion.error}
                {rolId === AUTO && " — Prueba eligiendo el rol manualmente."}
              </p>
            </div>
          )}

          {evaluacion.status === "loading" && <div className="card sel-result__skeleton" />}

          {evaluacion.status === "success" && resultado && (
            <Resultado
              key={intento}
              resultado={resultado}
              referencia={referencia}
              cvTexto={cvTexto}
              ejemplo={ejemplo}
            />
          )}
        </section>
      </div>
    </div>
  );
}

function Resultado({ resultado, referencia, cvTexto, ejemplo }) {
  return (
    <div className="sel-result__content">
      <div className="card sel-summary">
        <div className="sel-summary__top">
          <div>
            <span className="sel-summary__label">Rol evaluado</span>
            <h2 className="sel-summary__rol">{resultado.rol_nombre}</h2>
            <div className="sel-summary__chips">
              <span className="chip">Motor: {MOTORES[resultado.motor] ?? resultado.motor}</span>
              {resultado.rol_predicho && (
                <span className="chip chip--accent">Detectado por IA</span>
              )}
            </div>
          </div>
          <StatusPill estado={resultado.estado} />
        </div>
        <ScoreMeter score={resultado.score} size="lg" />
        <p className="sel-summary__explicacion">{resultado.explicacion}</p>
        {referencia && (
          <p
            className={`sel-summary__ref ${
              referencia.apto === (resultado.estado === "apto")
                ? "sel-summary__ref--ok"
                : "sel-summary__ref--ko"
            }`}
          >
            {referencia.apto === (resultado.estado === "apto")
              ? "✓ Coincide con la etiqueta del dataset."
              : `✕ El dataset lo etiqueta como ${referencia.apto ? "apto" : "no apto"}.`}
          </p>
        )}
      </div>

      <div>
        <h3 className="section-title">Requisitos</h3>
        <RequisitoList evaluacion={resultado.evaluacion} referencia={referencia} />
      </div>

      <RegistrarCandidato
        rolId={resultado.rol_id}
        cvTexto={cvTexto}
        nombreSugerido={ejemplo ? cvTexto.split(".")[0] : ""}
      />
    </div>
  );
}

function RegistrarCandidato({ rolId, cvTexto, nombreSugerido }) {
  const [nombre, setNombre] = useState(nombreSugerido);
  const [email, setEmail] = useState("");
  const [estado, setEstado] = useState({ status: "idle", error: "" });

  async function registrar(e) {
    e.preventDefault();
    setEstado({ status: "loading", error: "" });
    try {
      await crearCandidato({ nombre, email, hojaDeVidaTexto: cvTexto, rolId });
      setEstado({ status: "success", error: "" });
    } catch (err) {
      setEstado({ status: "error", error: err.message });
    }
  }

  if (estado.status === "success") {
    return (
      <div className="card sel-register sel-register--done">
        <p>
          <strong>{nombre}</strong> ya forma parte del pool y compite en el ranking del rol.
        </p>
        <Link to={`/ranking/${rolId}`} className="btn btn--primary btn--sm">
          Ver top 5
        </Link>
      </div>
    );
  }

  return (
    <form className="card sel-register" onSubmit={registrar}>
      <h3 className="section-title">Registrar candidato</h3>
      <p className="field__hint">Agrégalo al pool del rol para que participe en el ranking.</p>
      <div className="sel-register__fields">
        <label className="field">
          <span>Nombre</span>
          <input
            className="input"
            required
            minLength={2}
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
          />
        </label>
        <label className="field">
          <span>Email</span>
          <input
            className="input"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
      </div>
      {estado.status === "error" && <p className="sel-form__error">{estado.error}</p>}
      <button type="submit" className="btn btn--primary" disabled={estado.status === "loading"}>
        {estado.status === "loading" ? "Registrando…" : "Registrar en el ranking"}
      </button>
    </form>
  );
}
