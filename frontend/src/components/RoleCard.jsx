import { Link } from "react-router-dom";
import "./RoleCard.css";

export default function RoleCard({ rol, ranking }) {
  const lider = ranking?.top?.[0];

  return (
    <article className="role-card">
      <div className="role-card__head">
        <h3 className="role-card__title">{rol.nombre}</h3>
        {rol.clave && <span className="chip">{rol.clave}</span>}
      </div>

      <p className="role-card__umbral">
        Apto con al menos {Math.round((rol.umbral_apto ?? 0.66) * 100)} % de los requisitos
      </p>

      <ul className="role-card__requisitos">
        {rol.requisitos.map((req) => (
          <li key={req}>{req}</li>
        ))}
      </ul>

      {ranking && (
        <div className="role-card__stats">
          <span>
            <strong>{ranking.total_aptos}</strong> aptos de {ranking.total_evaluados}
          </span>
          {lider && (
            <Link to={`/candidatos/${lider.id}?rolId=${rol.id}`} className="role-card__lider">
              #1 {lider.nombre} · <span className="role-card__score">{lider.score}</span>
            </Link>
          )}
        </div>
      )}

      <div className="role-card__actions">
        <Link to={`/ranking/${rol.id}`} className="btn btn--primary">
          Ver top 5
        </Link>
        <Link to={`/seleccionar?rolId=${rol.id}`} className="btn btn--ghost">
          Evaluar CV
        </Link>
      </div>
    </article>
  );
}
