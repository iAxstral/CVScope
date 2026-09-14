import { Link, useLocation, useParams } from "react-router-dom";
import { mockRanking } from "../data/mockRanking.js";
import MockBadge from "../components/MockBadge.jsx";
import StatusPill from "../components/StatusPill.jsx";
import Highlight from "../components/Highlight.jsx";
import "./Ranking.css";

export default function Ranking() {
  const { rolId } = useParams();
  const location = useLocation();
  const rolNombre = location.state?.rolNombre ?? `Rol #${rolId}`;

  const candidatos = [...mockRanking].sort((a, b) => b.score - a.score);

  return (
    <div className="ranking-page">
      <header className="page-header">
        <div className="page-header__row">
          <h1>Ranking — {rolNombre}</h1>
          <MockBadge />
        </div>
        <p className="page-header__subtitle">
          Candidatos aptos ordenados de mejor a peor ajuste con el perfil del rol.
        </p>
      </header>

      <ol className="ranking-list">
        {candidatos.map((candidato, index) => (
          <li key={candidato.id} className="ranking-row">
            <span className="ranking-row__position">{index + 1}</span>

            <div className="ranking-row__info">
              <Link to={`/candidatos/${candidato.id}`} className="ranking-row__nombre">
                {candidato.nombre}
              </Link>
              <span className="ranking-row__email">{candidato.email}</span>
              <div className="ranking-row__requisitos">
                {candidato.requisitosDestacados.map((req) => (
                  <Highlight key={req.texto} variant={req.cumple ? "success" : "danger"}>
                    {req.texto}
                  </Highlight>
                ))}
              </div>
            </div>

            <StatusPill estado={candidato.estado} />

            <span className="ranking-row__score">{candidato.score}</span>

            <Link to={`/candidatos/${candidato.id}`} className="btn btn--ghost">
              Ver detalle
            </Link>
          </li>
        ))}
      </ol>
    </div>
  );
}
