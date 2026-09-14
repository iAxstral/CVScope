import { useEffect, useState } from "react";
import { getRoles } from "../api/client.js";
import RoleCard from "../components/RoleCard.jsx";
import "./Dashboard.css";

export default function Dashboard() {
  const [roles, setRoles] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | success | error
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    loadRoles();
  }, []);

  function loadRoles() {
    setStatus("loading");
    getRoles()
      .then((data) => {
        setRoles(data);
        setStatus("success");
      })
      .catch((err) => {
        setErrorMessage(err.message);
        setStatus("error");
      });
  }

  return (
    <div className="dashboard-page">
      <header className="page-header">
        <h1>Roles</h1>
        <p className="page-header__subtitle">
          Roles disponibles para preseleccionar candidatos, obtenidos desde el backend.
        </p>
      </header>

      {status === "loading" && <p className="dashboard-page__status">Cargando roles…</p>}

      {status === "error" && (
        <div className="error-banner">
          <p>
            No se pudo conectar con el backend en http://127.0.0.1:8000. Detalle: {errorMessage}
          </p>
          <button type="button" className="btn btn--ghost" onClick={loadRoles}>
            Reintentar
          </button>
        </div>
      )}

      {status === "success" && (
        <div className="dashboard-page__grid">
          {roles.map((rol) => (
            <RoleCard key={rol.id} rol={rol} />
          ))}
        </div>
      )}
    </div>
  );
}
