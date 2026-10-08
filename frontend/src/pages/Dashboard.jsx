import { Link } from "react-router-dom";
import { getRanking, getResumenDatasets, getRoles } from "../api/client.js";
import useApi from "../hooks/useApi.js";
import RoleCard from "../components/RoleCard.jsx";
import StatTile from "../components/StatTile.jsx";
import { Cargando, ErrorCarga } from "../components/EstadoCarga.jsx";
import "./Dashboard.css";

async function cargarDashboard() {
  const [roles, datasets] = await Promise.all([getRoles(), getResumenDatasets()]);
  const rankings = await Promise.all(roles.map((rol) => getRanking(rol.id, 1).catch(() => null)));
  return {
    roles: roles.map((rol, i) => ({ ...rol, ranking: rankings[i] })),
    datasets: Object.fromEntries(datasets.map((d) => [d.nombre, d])),
  };
}

export default function Dashboard() {
  const { status, data, error, reload } = useApi(cargarDashboard);

  const seleccion = data?.datasets.seleccion;
  const ranking = data?.datasets.ranking;
  const totalCvs = (seleccion?.total ?? 0) + (ranking?.total ?? 0);
  const totalAptos = (seleccion?.aptos ?? 0) + (ranking?.aptos ?? 0);

  return (
    <div className="dashboard-page">
      <header className="page-header">
        <h1>Panel de preselección</h1>
        <p className="page-header__subtitle">
          Categoriza hojas de vida por rol, evalúa los requisitos mínimos con evidencia y obtén el
          top 5 de candidatos de cada rol.
        </p>
      </header>

      {status === "loading" && <Cargando texto="Cargando roles y datasets…" />}
      {status === "error" && <ErrorCarga mensaje={error} onRetry={reload} />}

      {status === "success" && (
        <>
          <section className="dashboard-page__stats" aria-label="Resumen">
            <StatTile
              label="Roles activos"
              value={data.roles.length}
              hint="con requisitos mínimos"
            />
            <StatTile
              label="Hojas de vida"
              value={totalCvs}
              hint={`${seleccion?.total ?? 0} selección · ${ranking?.total ?? 0} ranking`}
            />
            <StatTile
              label="Aptos en datasets"
              value={totalCvs ? `${Math.round((totalAptos / totalCvs) * 100)}%` : "—"}
              hint={`${totalAptos} de ${totalCvs} cumplen el mínimo`}
            />
            <StatTile label="Top por rol" value="5" hint="mejores hojas de vida aptas" />
          </section>

          <section className="dashboard-page__flow">
            <Link to="/seleccionar" className="flow-step">
              <span className="flow-step__n">1</span>
              <span>
                <strong>Seleccionar</strong>
                <small>Pega un CV y descubre su rol y si es apto, con evidencia.</small>
              </span>
            </Link>
            <Link to="/ranking" className="flow-step">
              <span className="flow-step__n">2</span>
              <span>
                <strong>Rankear</strong>
                <small>Compara a los candidatos aptos y obtén el top 5 por rol.</small>
              </span>
            </Link>
            <Link to="/datasets" className="flow-step">
              <span className="flow-step__n">3</span>
              <span>
                <strong>Validar</strong>
                <small>Explora los datasets de selección y de ranking.</small>
              </span>
            </Link>
          </section>

          <section>
            <h2 className="section-title">Roles</h2>
            <div className="dashboard-page__grid">
              {data.roles.map((rol) => (
                <RoleCard key={rol.id} rol={rol} ranking={rol.ranking} />
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
