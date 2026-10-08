import Highlight from "./Highlight.jsx";
import { claveDeNota, marcarClaves } from "../utils/texto.js";
import "./RequisitoList.css";

export default function RequisitoList({ evaluacion, referencia }) {
  const reales = referencia ? new Set(referencia.requisitos_cumplidos) : null;

  return (
    <ul className="req-list">
      {evaluacion.map((item) => {
        const clave = claveDeNota(item.nota);
        const coincide = reales ? reales.has(item.requisito) === item.cumple : null;
        return (
          <li key={item.requisito} className="req-item">
            <div className="req-item__header">
              <Highlight variant={item.cumple ? "success" : "danger"}>{item.requisito}</Highlight>
              <span className={`req-item__verdict req-item__verdict--${item.cumple ? "ok" : "no"}`}>
                {item.cumple ? "✓ Cumple" : "✕ No cumple"}
              </span>
            </div>

            {item.evidencia ? (
              <blockquote className="req-item__evidencia">
                {marcarClaves(item.evidencia, [clave]).map((parte, i) =>
                  parte.marcado ? (
                    <mark key={i}>{parte.texto}</mark>
                  ) : (
                    <span key={i}>{parte.texto}</span>
                  ),
                )}
              </blockquote>
            ) : (
              <p className="req-item__nota">{item.nota}</p>
            )}

            {coincide === false && (
              <p className="req-item__discrepancia">
                La etiqueta del dataset dice que {reales.has(item.requisito) ? "sí" : "no"} lo
                cumple: el evaluador por palabras clave no lo detectó correctamente.
              </p>
            )}
          </li>
        );
      })}
    </ul>
  );
}
