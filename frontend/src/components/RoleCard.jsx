import { Link } from "react-router-dom";
import "./RoleCard.css";

export default function RoleCard({ rol }) {
  return (
    <article className="role-card">
      <h3 className="role-card__title">{rol.nombre}</h3>

      <ul className="role-card__requisitos">
        {rol.requisitos.map((req) => (
          <li key={req}>{req}</li>
        ))}
      </ul>

      <div className="role-card__actions">
        <Link to={`/ranking/${rol.id}`} state={{ rolNombre: rol.nombre }} className="btn btn--ghost">
          Ver ranking
        </Link>
        <Link to={`/cargar-candidatos?rolId=${rol.id}`} className="btn btn--primary">
          Cargar candidatos
        </Link>
      </div>
    </article>
  );
}
