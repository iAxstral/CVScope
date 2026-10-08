import { useState } from "react";
import { crearRol } from "../api/client.js";
import "./NuevoRolForm.css";

const UMBRALES = [
  { valor: 0.5, etiqueta: "50 % · flexible" },
  { valor: 0.66, etiqueta: "66 % · recomendado" },
  { valor: 0.75, etiqueta: "75 % · exigente" },
  { valor: 1, etiqueta: "100 % · todos los requisitos" },
];

export default function NuevoRolForm({ onCreado, onCancelar }) {
  const [nombre, setNombre] = useState("");
  const [clave, setClave] = useState("");
  const [requisitosTexto, setRequisitosTexto] = useState("");
  const [umbral, setUmbral] = useState(0.66);
  const [estado, setEstado] = useState({ status: "idle", error: "" });

  const requisitos = requisitosTexto
    .split("\n")
    .map((r) => r.trim())
    .filter(Boolean);

  async function enviar(e) {
    e.preventDefault();
    setEstado({ status: "loading", error: "" });
    try {
      const rol = await crearRol({ nombre, clave, requisitos, umbralApto: umbral });
      onCreado(rol);
    } catch (err) {
      setEstado({ status: "error", error: err.message });
    }
  }

  return (
    <form className="card nuevo-rol" onSubmit={enviar}>
      <div className="nuevo-rol__head">
        <h3 className="section-title">Nuevo rol</h3>
        <button type="button" className="btn btn--ghost btn--sm" onClick={onCancelar}>
          Cancelar
        </button>
      </div>

      <div className="nuevo-rol__grid">
        <label className="field">
          <span>Nombre del rol</span>
          <input
            className="input"
            required
            minLength={2}
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Ej. Científico de datos"
          />
        </label>
        <label className="field">
          <span>
            Clave <span className="field__hint">(opcional, sin espacios)</span>
          </span>
          <input
            className="input"
            value={clave}
            pattern="[a-z0-9_-]*"
            maxLength={30}
            onChange={(e) => setClave(e.target.value.toLowerCase())}
            placeholder="Ej. datos"
          />
        </label>
      </div>

      <label className="field">
        <span>
          Requisitos mínimos <span className="field__hint">(uno por línea)</span>
        </span>
        <textarea
          className="input"
          rows={4}
          required
          value={requisitosTexto}
          onChange={(e) => setRequisitosTexto(e.target.value)}
          placeholder={"Python\nMachine learning\nSQL"}
        />
      </label>

      <label className="field">
        <span>Es apto si cumple al menos</span>
        <select
          className="input"
          value={umbral}
          onChange={(e) => setUmbral(Number(e.target.value))}
        >
          {UMBRALES.map((u) => (
            <option key={u.valor} value={u.valor}>
              {u.etiqueta}
            </option>
          ))}
        </select>
      </label>

      {estado.status === "error" && <p className="nuevo-rol__error">{estado.error}</p>}

      <div className="nuevo-rol__acciones">
        <span className="field__hint">
          {requisitos.length} requisito{requisitos.length === 1 ? "" : "s"}
        </span>
        <button
          type="submit"
          className="btn btn--primary"
          disabled={estado.status === "loading" || requisitos.length === 0}
        >
          {estado.status === "loading" ? "Creando…" : "Crear rol"}
        </button>
      </div>
    </form>
  );
}
