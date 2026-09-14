import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar.jsx";
import "./Layout.css";

export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);

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
