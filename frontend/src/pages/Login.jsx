import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { iniciarSesion } from "../api/client.js";
import { sesionActual } from "../utils/sesion.js";
import "./Login.css";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [estado, setEstado] = useState({ status: "idle", error: "" });

  if (sesionActual()) return <Navigate to="/dashboard" replace />;

  async function handleSubmit(e) {
    e.preventDefault();
    setEstado({ status: "loading", error: "" });
    try {
      await iniciarSesion({ email, contrasena: password });
      navigate(location.state?.desde ?? "/dashboard", { replace: true });
    } catch (err) {
      setEstado({ status: "error", error: err.message });
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-card__brand">
          <span className="login-card__brand-mark">CV</span>
          <span>CVScope</span>
        </div>

        <h1 className="login-card__title">Iniciar sesión</h1>
        <p className="login-card__subtitle">Preselección de talento con IA explicable</p>

        <form className="login-form" onSubmit={handleSubmit}>
          <label className="login-form__field">
            <span>Email</span>
            <input
              type="email"
              required
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="tu@empresa.com"
            />
          </label>

          <label className="login-form__field">
            <span>Contraseña</span>
            <input
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </label>

          {estado.status === "error" && (
            <p className="login-form__error" role="alert">
              {estado.error}
            </p>
          )}

          <button
            type="submit"
            className="btn btn--primary login-form__submit"
            disabled={estado.status === "loading"}
          >
            {estado.status === "loading" ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </div>
    </div>
  );
}
