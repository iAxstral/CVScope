import { useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { sesionActual } from "../utils/sesion.js";
import Sidebar from "./Sidebar.jsx";
import "./Layout.css";

export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);

  const location = useLocation();

  // Sin sesión no se entra a la aplicación; se vuelve al login y luego aquí.
  if (!sesionActual()) {
    return <Navigate to="/" replace state={{ desde: location.pathname + location.search }} />;
  }

  return (
    <div className="app-shell">
      <header className="mobile-topbar">
        <button
          type="button"
          className="mobile-topbar__toggle"
          onClick={() => setMenuOpen((open) => !open)}
          aria-label="Abrir menú de navegación"
          aria-expanded={menuOpen}
        >
          <span />
          <span />
          <span />
        </button>
        <span className="mobile-topbar__title">CVScope</span>
      </header>

      <Sidebar open={menuOpen} onNavigate={() => setMenuOpen(false)} />

      {menuOpen && <div className="app-shell__overlay" onClick={() => setMenuOpen(false)} />}

      <main className="app-shell__main">
        <Outlet />
      </main>
    </div>
  );
}
