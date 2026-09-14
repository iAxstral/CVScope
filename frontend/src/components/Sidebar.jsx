import { NavLink } from "react-router-dom";
import "./Sidebar.css";

const links = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/cargar-candidatos", label: "Cargar candidatos" },
];

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
            {link.label}
          </NavLink>
        ))}
      </nav>

      <p className="sidebar__footnote">Preselección de talento con IA explicable</p>
    </aside>
  );
}
