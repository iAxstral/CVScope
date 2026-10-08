import { useState } from "react";
import "./MaxnetChart.css";

const ANCHO = 640;
const ALTO = 220;
const M = { top: 12, right: 120, bottom: 28, left: 40 };

/**
 * Activación de cada neurona de la capa competitiva (MAXNET) en cada
 * iteración. `colores` asigna color por índice de neurona; las demás van en
 * gris de contexto. La ganadora se rotula al final de su línea.
 */
export default function MaxnetChart({ trayectoria, nombres, ganador, colores = {} }) {
  const [hover, setHover] = useState(null);
  const pasos = trayectoria.length;
  const n = trayectoria[0]?.length ?? 0;
  const maxY = Math.max(...trayectoria[0]);
  const w = ANCHO - M.left - M.right;
  const h = ALTO - M.top - M.bottom;
  const x = (t) => M.left + (pasos > 1 ? (t / (pasos - 1)) * w : w / 2);
  const y = (v) => M.top + h - (v / maxY) * h;

  const linea = (i) =>
    trayectoria.map((paso, t) => `${t ? "L" : "M"}${x(t)},${y(paso[i])}`).join("");
  const orden = [...Array(n).keys()].sort(
    (a, b) => (a in colores) - (b in colores) || (a === ganador) - (b === ganador),
  );
  const ticksX =
    pasos <= 8 ? [...Array(pasos).keys()] : [0, Math.round((pasos - 1) / 2), pasos - 1];

  function mover(e) {
    const caja = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - caja.left) / caja.width) * ANCHO;
    const t = Math.round(((px - M.left) / w) * (pasos - 1));
    setHover(Math.max(0, Math.min(pasos - 1, t)));
  }

  const activas =
    hover === null
      ? []
      : trayectoria[hover]
          .map((v, i) => ({ i, v }))
          .filter((d) => d.v > 0)
          .sort((a, b) => b.v - a.v)
          .slice(0, 5);

  return (
    <figure className="maxnet-chart">
      <div className="maxnet-chart__plot">
        <svg
          viewBox={`0 0 ${ANCHO} ${ALTO}`}
          role="img"
          aria-label={`Activaciones de ${n} neuronas durante ${pasos - 1} iteraciones; gana ${nombres[ganador]}`}
          onMouseMove={mover}
          onMouseLeave={() => setHover(null)}
        >
          {[0, 0.5, 1].map((f) => (
            <g key={f}>
              <line
                className="maxnet-chart__grid"
                x1={M.left}
                x2={M.left + w}
                y1={y(f * maxY)}
                y2={y(f * maxY)}
              />
              <text
                className="maxnet-chart__tick"
                x={M.left - 6}
                y={y(f * maxY)}
                textAnchor="end"
                dominantBaseline="middle"
              >
                {(f * maxY).toFixed(f ? 2 : 0)}
              </text>
            </g>
          ))}
          {ticksX.map((t) => (
            <text key={t} className="maxnet-chart__tick" x={x(t)} y={ALTO - 8} textAnchor="middle">
              {t}
            </text>
          ))}

          {orden.map((i) => (
            <path
              key={i}
              d={linea(i)}
              className={`maxnet-chart__line ${i in colores || i === ganador ? "" : "maxnet-chart__line--contexto"}`}
              style={colores[i] ? { stroke: colores[i] } : undefined}
            />
          ))}

          <text
            className="maxnet-chart__label"
            x={x(pasos - 1) + 8}
            y={y(trayectoria[pasos - 1][ganador])}
            dominantBaseline="middle"
          >
            {nombres[ganador]?.split(" ").slice(0, 2).join(" ")}
          </text>

          {hover !== null && (
            <line
              className="maxnet-chart__cursor"
              x1={x(hover)}
              x2={x(hover)}
              y1={M.top}
              y2={M.top + h}
            />
          )}
        </svg>
        {hover !== null && (
          <div
            className="maxnet-chart__tooltip"
            style={{ left: `${(x(hover) / ANCHO) * 100}%` }}
            role="status"
          >
            <strong>Iteración {hover}</strong>
            {activas.map((d) => (
              <span key={d.i}>
                {nombres[d.i]} <b>{d.v.toFixed(3)}</b>
              </span>
            ))}
            {activas.length === 0 && <span>Todas apagadas</span>}
          </div>
        )}
      </div>
      <figcaption className="maxnet-chart__caption">
        Eje X: iteración de la capa competitiva · Eje Y: activación de cada neurona (hoja de vida)
      </figcaption>
    </figure>
  );
}
