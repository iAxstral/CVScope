import { Link, useNavigate, useParams } from "react-router-dom";
import { getRanking, getRoles } from "../api/client.js";
import useApi from "../hooks/useApi.js";
import Highlight from "../components/Highlight.jsx";
import RoleTabs from "../components/RoleTabs.jsx";
import ScoreMeter from "../components/ScoreMeter.jsx";
import StatTile from "../components/StatTile.jsx";
import { Cargando, ErrorCarga } from "../components/EstadoCarga.jsx";
import "./Ranking.css";

const TOP = 5;

export default function Ranking() {
  const { rolId } = useParams();
  const navigate = useNavigate();
  const roles = useApi(getRoles);
  const rolActivo = rolId ?? roles.data?.[0]?.id;

  const ranking = useApi(
    () => (rolActivo ? getRanking(rolActivo, TOP) : new Promise(() => {})),
    [rolActivo],
  );

  return (
    <div className="ranking-page">
      <header className="page-header">
        <h1>Ranking — top {TOP} hojas de vida</h1>
        <p className="page-header__subtitle">
          Se evalúan todas las hojas de vida del rol (dataset de ranking + candidatos registrados) y
          se ordenan las aptas de mejor a peor ajuste con el perfil.
        </p>
      </header>

      {roles.status === "error" && <ErrorCarga mensaje={roles.error} onRetry={roles.reload} />}
      {roles.status === "success" && (
        <RoleTabs
          roles={roles.data}
          value={rolActivo}
          onChange={(rol) => navigate(`/ranking/${rol.id}`)}
        />
      )}

      {ranking.status === "loading" && roles.status !== "error" && (
        <Cargando texto="Calculando ranking…" />
      )}
      {ranking.status === "error" && (
        <ErrorCarga mensaje={ranking.error} onRetry={ranking.reload} />
      )}

      {ranking.status === "success" && <RankingContenido ranking={ranking.data} />}
    </div>
  );
}

function RankingContenido({ ranking }) {
  return (
    <>
      <section className="ranking-page__stats" aria-label="Resumen del ranking">
        <StatTile label="Hojas de vida evaluadas" value={ranking.total_evaluados} />
        <StatTile
          label="Aptas"
          value={ranking.total_aptos}
          hint={`${ranking.total_evaluados - ranking.total_aptos} no alcanzan el mínimo`}
        />
        {ranking.coincidencias_referencia !== null && (
          <StatTile
            label="Coincidencia con referencia"
            value={`${ranking.coincidencias_referencia}/${TOP}`}
            hint="del top real del dataset de ranking"
          />
        )}
      </section>

      <div className="ranking-page__reqs">
        <span className="ranking-page__reqs-label">Requisitos del rol:</span>
        {ranking.requisitos.map((req) => (
          <span key={req} className="chip">
            {req}
          </span>
        ))}
      </div>

      {ranking.top.length === 0 ? (
        <p className="empty-state">
          Ninguna hoja de vida de este rol es apta todavía.{" "}
          <Link to={`/seleccionar?rolId=${ranking.rol_id}`} className="link">
            Evalúa y registra un candidato
          </Link>
          .
        </p>
      ) : (
        <ol className="ranking-list">
          {ranking.top.map((c, index) => {
            const detalle = `/candidatos/${c.id}?rolId=${ranking.rol_id}`;
            return (
              <li key={c.id} className={`ranking-row ${index === 0 ? "ranking-row--first" : ""}`}>
                <span className={`ranking-row__position ranking-row__position--${index + 1}`}>
                  {index + 1}
                </span>

                <div className="ranking-row__info">
                  <div className="ranking-row__name-line">
                    <Link to={detalle} className="ranking-row__nombre">
                      {c.nombre}
                    </Link>
                    {c.fuente === "registrado" && (
                      <span className="chip chip--accent">Registrado</span>
                    )}
                  </div>
                  <span className="ranking-row__meta">
                    {c.email} · {c.anios_experiencia} años de experiencia
                  </span>
                  <div className="ranking-row__requisitos">
                    {c.requisitos_cumplidos.map((r) => (
                      <Highlight key={r} variant="success">
                        {r}
                      </Highlight>
                    ))}
                    {c.requisitos_faltantes.map((r) => (
                      <Highlight key={r} variant="danger">
                        {r}
                      </Highlight>
                    ))}
                  </div>
                </div>

                <ScoreMeter score={c.score} />

                <Link to={detalle} className="btn btn--ghost btn--sm">
                  Ver detalle
                </Link>
              </li>
            );
          })}
        </ol>
      )}

      <p className="ranking-page__legend">
        <Highlight variant="success">Cumple</Highlight>{" "}
        <Highlight variant="danger">No cumple</Highlight>· Puntaje = 80 × requisitos cumplidos + 20
        × experiencia (tope 12 años).
      </p>
    </>
  );
}
