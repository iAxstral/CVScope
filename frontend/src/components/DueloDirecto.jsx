import { useState } from "react";
import { compararCvs } from "../api/client.js";
import Highlight from "./Highlight.jsx";
import "./DueloDirecto.css";

function Esquina({ competidor, gano, prob }) {
  return (
    <div className={`duelo-esquina ${gano ? "duelo-esquina--win" : ""}`}>
      {gano && <span className="duelo-esquina__badge">Gana</span>}
      <strong className="duelo-esquina__nombre">{competidor.nombre}</strong>
      <span className="duelo-esquina__prob">{(prob * 100).toFixed(1)}%</span>
      <span className="duelo-esquina__meta">
        Fuerza {competidor.fuerza.toFixed(1)} · {competidor.anios_experiencia} años
      </span>
      <div className="duelo-esquina__reqs">
        {competidor.requisitos_cumplidos.map((r) => (
          <Highlight key={r} variant="success">
            {r}
          </Highlight>
        ))}
        {competidor.requisitos_faltantes.map((r) => (
          <Highlight key={r} variant="danger">
            {r}
          </Highlight>
        ))}
      </div>
    </div>
  );
}

export default function DueloDirecto({ rolId, participantes }) {
  const opciones = [...participantes].sort((x, y) => x.nombre.localeCompare(y.nombre));
  const [a, setA] = useState(participantes[0]?.id ?? "");
  const [b, setB] = useState(participantes[1]?.id ?? "");
  const [estado, setEstado] = useState({ status: "idle", data: null, error: "" });

  async function enfrentar() {
    setEstado({ status: "loading", data: null, error: "" });
    try {
      const data = await compararCvs({ rolId, a: { cv_id: a }, b: { cv_id: b } });
      setEstado({ status: "success", data, error: "" });
    } catch (err) {
      setEstado({ status: "error", data: null, error: err.message });
    }
  }

  const r = estado.data;

  return (
    <section className="card duelo">
      <h2 className="section-title">Duelo directo</h2>
      <p className="field__hint">
        Elige dos hojas de vida y la red decide cuál es mejor para el rol.
      </p>

      <div className="duelo__controles">
        <select
          className="input"
          value={a}
          onChange={(e) => setA(e.target.value)}
          aria-label="Hoja de vida A"
        >
          {opciones.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nombre}
            </option>
          ))}
        </select>
        <span className="duelo__vs">vs</span>
        <select
          className="input"
          value={b}
          onChange={(e) => setB(e.target.value)}
          aria-label="Hoja de vida B"
        >
          {opciones.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nombre}
            </option>
          ))}
        </select>
        <button
          type="button"
          className="btn btn--accent"
          onClick={enfrentar}
          disabled={!a || !b || a === b || estado.status === "loading"}
        >
          {estado.status === "loading" ? "Comparando…" : "Enfrentar"}
        </button>
      </div>
      {a && a === b && <p className="field__hint">Elige dos hojas de vida distintas.</p>}

      {estado.status === "error" && (
        <div className="error-banner" role="alert">
          <p>No se pudo comparar. Detalle: {estado.error}</p>
        </div>
      )}

      {estado.status === "success" && r && (
        <div className="duelo__resultado" aria-live="polite">
          <div className="duelo__barra" aria-hidden="true">
            <span style={{ flexGrow: r.prob_a }} />
            <span style={{ flexGrow: 1 - r.prob_a }} />
          </div>
          <div className="duelo__esquinas">
            <Esquina competidor={r.a} gano={r.ganador === "a"} prob={r.prob_a} />
            <Esquina competidor={r.b} gano={r.ganador === "b"} prob={1 - r.prob_a} />
          </div>
          <p className="duelo__explicacion">{r.explicacion}</p>
        </div>
      )}
    </section>
  );
}
