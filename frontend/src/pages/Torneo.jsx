import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getModeloCompetencia, getRoles, jugarTorneo } from "../api/client.js";
import useApi from "../hooks/useApi.js";
import Bracket from "../components/Bracket.jsx";
import DueloDirecto from "../components/DueloDirecto.jsx";
import RoleTabs from "../components/RoleTabs.jsx";
import StatTile from "../components/StatTile.jsx";
import { Cargando, ErrorCarga } from "../components/EstadoCarga.jsx";
import "./Torneo.css";

const TOP = 5;

export default function Torneo() {
  const { rolId } = useParams();
  const navigate = useNavigate();
  const roles = useApi(getRoles);
  const modelo = useApi(getModeloCompetencia);
  const [semilla, setSemilla] = useState(null);
  const rolActivo = rolId ?? roles.data?.[0]?.id;

  const torneo = useApi(
    () =>
      rolActivo ? jugarTorneo({ rolId: rolActivo, top: TOP, semilla }) : new Promise(() => {}),
    [rolActivo, semilla],
  );

  return (
    <div className="torneo-page">
      <header className="page-header">
        <h1>Red neuronal competitiva</h1>
        <p className="page-header__subtitle">
          Las hojas de vida se enfrentan de a dos: la red decide cuál es mejor para el rol y la
          ganadora avanza a la siguiente ronda hasta que queda una campeona.
        </p>
      </header>

      {modelo.status === "success" && <ModeloResumen modelo={modelo.data} />}

      {roles.status === "error" && <ErrorCarga mensaje={roles.error} onRetry={roles.reload} />}
      {roles.status === "success" && (
        <div className="torneo-page__toolbar">
          <RoleTabs
            roles={roles.data}
            value={rolActivo}
            onChange={(rol) => navigate(`/torneo/${rol.id}`)}
          />
          <div className="torneo-page__sorteo">
            <button
              type="button"
              className="btn btn--ghost btn--sm"
              onClick={() => setSemilla(Math.floor(Math.random() * 1_000_000))}
            >
              Sortear cuadro
            </button>
            {semilla !== null && (
              <button
                type="button"
                className="btn btn--ghost btn--sm"
                onClick={() => setSemilla(null)}
              >
                Orden original
              </button>
            )}
          </div>
        </div>
      )}

      {torneo.status === "loading" && roles.status !== "error" && (
        <Cargando texto="Jugando el torneo…" />
      )}
      {torneo.status === "error" && <ErrorCarga mensaje={torneo.error} onRetry={torneo.reload} />}
      {torneo.status === "success" && (
        <Resultado key={`${rolActivo}-${semilla}`} torneo={torneo.data} />
      )}
    </div>
  );
}

function ModeloResumen({ modelo }) {
  const m = modelo.metricas;
  return (
    <section className="card torneo-modelo">
      <div>
        <span className="torneo-modelo__label">Modelo</span>
        <p className="torneo-modelo__arq">{modelo.arquitectura}</p>
      </div>
      <dl className="torneo-modelo__metricas">
        <div>
          <dt>Precisión@5 en prueba</dt>
          <dd>
            {m.precision_top5_prueba?.toFixed(2)}
            <small>palabras clave: {m.precision_top5_prueba_base?.toFixed(2)}</small>
          </dd>
        </div>
        <div>
          <dt>Exactitud en duelos</dt>
          <dd>
            {m.exactitud_duelos_prueba?.toFixed(3)}
            <small>palabras clave: {m.exactitud_duelos_prueba_base?.toFixed(3)}</small>
          </dd>
        </div>
      </dl>
    </section>
  );
}

function Resultado({ torneo }) {
  const porId = Object.fromEntries(torneo.participantes.map((p) => [p.id, p]));
  const final = torneo.rondas.at(-1)?.duelos[0] ?? null;
  const [duelo, setDuelo] = useState(final);
  const detalle = (id) => `/candidatos/${id}?rolId=${torneo.rol_id}`;

  return (
    <>
      <section className="torneo-page__stats" aria-label="Resumen del torneo">
        <StatTile label="Participantes" value={torneo.participantes.length} />
        <StatTile
          label="Duelos jugados"
          value={torneo.total_duelos}
          hint={`${torneo.rondas.length} rondas`}
        />
        {torneo.coincidencias_referencia !== null && (
          <StatTile
            label="Podio vs. referencia"
            value={`${torneo.coincidencias_referencia}/${TOP}`}
            hint="coinciden con el top real del dataset"
          />
        )}
      </section>

      <div className="torneo-page__grid">
        <section className="card torneo-campeon">
          <span className="torneo-campeon__label">Campeón · {torneo.rol_nombre}</span>
          <Link to={detalle(torneo.campeon.id)} className="torneo-campeon__nombre">
            {torneo.campeon.nombre}
          </Link>
          <p className="torneo-campeon__meta">
            {torneo.campeon.anios_experiencia} años de experiencia ·{" "}
            {torneo.campeon.requisitos_cumplidos.length} requisitos con evidencia · fuerza{" "}
            {torneo.campeon.fuerza.toFixed(1)}
          </p>
        </section>

        <section className="card torneo-podio">
          <h2 className="section-title">Top {TOP} de la red</h2>
          <ol>
            {torneo.podio.map((p, i) => (
              <li key={p.id}>
                <span className={`torneo-podio__pos torneo-podio__pos--${i + 1}`}>{i + 1}</span>
                <Link to={detalle(p.id)} className="torneo-podio__nombre">
                  {p.nombre}
                </Link>
                {p.posicion_referencia && (
                  <span className="chip" title="Posición real en el dataset de ranking">
                    ref. #{p.posicion_referencia}
                  </span>
                )}
                <span className="torneo-podio__fuerza">{p.fuerza.toFixed(1)}</span>
              </li>
            ))}
          </ol>
        </section>
      </div>

      <section>
        <h2 className="section-title">Cuadro del torneo</h2>
        <Bracket
          rondas={torneo.rondas}
          participantes={torneo.participantes}
          campeonId={torneo.campeon.id}
          onSelectDuelo={setDuelo}
        />
        {duelo && (
          <div className="card torneo-duelo" aria-live="polite">
            <span className="torneo-duelo__label">
              {porId[duelo.a]?.nombre} vs. {porId[duelo.b]?.nombre}
            </span>
            <p>{duelo.explicacion}</p>
          </div>
        )}
      </section>

      <DueloDirecto
        rolId={torneo.rol_id}
        participantes={torneo.podio.concat(
          torneo.participantes.filter((p) => !torneo.podio.some((q) => q.id === p.id)),
        )}
      />
    </>
  );
}
