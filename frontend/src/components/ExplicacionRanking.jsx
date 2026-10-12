import { getExplicacionRanking } from "../api/client.js";
import useApi from "../hooks/useApi.js";
import StatTile from "./StatTile.jsx";
import { Cargando, ErrorCarga } from "./EstadoCarga.jsx";
import "./ExplicacionRanking.css";

const signo = (n) => `${n >= 0 ? "+" : "−"}${Math.abs(n).toFixed(2)}`;

function claseVentaja(valor) {
  if (valor > 0) return "explicacion__ventaja explicacion__ventaja--pos";
  if (valor < 0) return "explicacion__ventaja explicacion__ventaja--neg";
  return "explicacion__ventaja";
}

export default function ExplicacionRanking({ rolId }) {
  const explicacion = useApi(() => getExplicacionRanking(rolId), [rolId]);

  if (explicacion.status === "loading") return <Cargando texto="Calculando la explicación…" />;
  if (explicacion.status === "error") {
    return <ErrorCarga mensaje={explicacion.error} onRetry={explicacion.reload} />;
  }
  return <Contenido e={explicacion.data} />;
}

function Contenido({ e }) {
  const { ganador, segundo, margen } = e;
  const escala = Math.max(
    0.01,
    ...e.requisitos.flatMap((r) => [r.ganador.contribucion, r.segundo.contribucion]),
    ganador.experiencia,
    segundo.experiencia,
  );

  return (
    <div className="explicacion">
      <p className="explicacion__resumen">{e.resumen}</p>

      <section className="explicacion__stats" aria-label="Margen de la victoria">
        <StatTile
          label="Margen de fuerza"
          value={margen.fuerza.toFixed(2)}
          hint={`${ganador.fuerza.toFixed(2)} frente a ${segundo.fuerza.toFixed(2)}`}
        />
        <StatTile
          label="Probabilidad de ganar"
          value={`${(margen.probabilidad_ganador * 100).toFixed(1)}%`}
          hint="frente a la segunda: sigmoide de la diferencia de fuerzas"
        />
        <StatTile
          label="Iteraciones MAXNET"
          value={margen.iteraciones}
          hint={`hasta apagar a la segunda (ε = ${margen.epsilon})`}
        />
      </section>

      <table className="explicacion__tabla">
        <caption className="explicacion__caption">
          Aporte de cada requisito a la fuerza de las dos primeras hojas de vida
        </caption>
        <thead>
          <tr>
            <th scope="col">Requisito</th>
            <th scope="col">
              <span className="explicacion__leyenda explicacion__leyenda--ganador" />
              {ganador.nombre} (1.ª)
            </th>
            <th scope="col">
              <span className="explicacion__leyenda explicacion__leyenda--segundo" />
              {segundo.nombre} (2.ª)
            </th>
            <th scope="col">Ventaja</th>
          </tr>
        </thead>
        <tbody>
          {e.requisitos.map((r) => (
            <tr key={r.requisito}>
              <th scope="row">{r.requisito}</th>
              <td>
                <Barra v={r.ganador} escala={escala} lado="ganador" />
              </td>
              <td>
                <Barra v={r.segundo} escala={escala} lado="segundo" />
              </td>
              <td className={claseVentaja(r.ventaja)}>{signo(r.ventaja)}</td>
            </tr>
          ))}
          <tr>
            <th scope="row">Experiencia declarada</th>
            <td>
              <Barra
                v={{ cumple: ganador.anios_experiencia > 0, contribucion: ganador.experiencia }}
                escala={escala}
                lado="ganador"
                texto={`${ganador.anios_experiencia} años`}
              />
            </td>
            <td>
              <Barra
                v={{ cumple: segundo.anios_experiencia > 0, contribucion: segundo.experiencia }}
                escala={escala}
                lado="segundo"
                texto={`${segundo.anios_experiencia} años`}
              />
            </td>
            <td className={claseVentaja(e.ventaja_experiencia)}>{signo(e.ventaja_experiencia)}</td>
          </tr>
          <tr className="explicacion__resto">
            <th scope="row">Resto (punto de partida e interacciones)</th>
            <td className="explicacion__numero">{signo(ganador.otras_senales)}</td>
            <td className="explicacion__numero">{signo(segundo.otras_senales)}</td>
            <td className={claseVentaja(e.ventaja_otras_senales)}>{signo(e.ventaja_otras_senales)}</td>
          </tr>
        </tbody>
      </table>

      <p className="explicacion__nota">
        El aporte de cada requisito se mide quitando del texto la evidencia de ese requisito y
        viendo cuánto baja la fuerza que le da la red. Como la red no es lineal, los aportes
        individuales no suman exactamente la fuerza: lo que falta queda en «Resto». La suma de
        todas las filas es la fuerza de cada hoja de vida y la suma de las ventajas es el margen.
        Compiten {e.total_competidores} hojas de vida; aquí se compara a la 1.ª con la 2.ª.
      </p>
    </div>
  );
}

function Barra({ v, escala, lado, texto }) {
  const ancho = Math.max(0, Math.min(100, (v.contribucion / escala) * 100));
  return (
    <div className="explicacion__barra">
      <div className="explicacion__pista" aria-hidden="true">
        <div
          className={`explicacion__relleno explicacion__relleno--${lado}`}
          style={{ width: `${ancho}%` }}
        />
      </div>
      <span className="explicacion__numero">
        {v.cumple ? signo(v.contribucion) : "sin evidencia"}
        {texto && <small> · {texto}</small>}
      </span>
      {v.evidencia && <span className="explicacion__evidencia">{v.evidencia}</span>}
    </div>
  );
}
