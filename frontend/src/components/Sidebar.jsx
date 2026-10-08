import { NavLink } from "react-router-dom";
import "./Sidebar.css";

const iconos = {
  dashboard: "M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z",
  seleccionar: "M9 11l3 3 8-8M20 12v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9",
  ranking: "M8 21V11M16 21V7M12 21V3M4 21h16",
  torneo: "M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4zM7 6H4v2a3 3 0 0 0 3 3M17 6h3v2a3 3 0 0 1-3 3",
  datasets:
    "M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3zM4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3",
};

const links = [
  { to: "/dashboard", label: "Dashboard", icono: "dashboard" },
  { to: "/seleccionar", label: "Seleccionar CV", icono: "seleccionar" },
  { to: "/ranking", label: "Ranking top 5", icono: "ranking" },
  { to: "/torneo", label: "Red competitiva", icono: "torneo" },
  { to: "/datasets", label: "Datasets", icono: "datasets" },
];

function Icono({ nombre }) {
  return (
    <svg className="sidebar__icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d={iconos[nombre]} />
    </svg>
  );
}

export default function Sidebar({ open, onNavigate }) {
  return (
    <aside className={`sidebar ${open ? "sidebar--open" : ""}`}>
      <div className="sidebar__brand">
        <span className="sidebar__brand-mark">CV</span>
        <span className="sidebar__brand-name">CVScope</span>
      </div>

      <nav className="sidebar__nav">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            onClick={onNavigate}
            className={({ isActive }) => `sidebar__link ${isActive ? "sidebar__link--active" : ""}`}
          >
            <Icono nombre={link.icono} />
            {link.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar__footer">
        <p className="sidebar__footnote">Preselección de talento con IA explicable</p>
        <NavLink to="/" className="sidebar__logout">
          Cerrar sesión
        </NavLink>
      </div>
    </aside>
  );
}
