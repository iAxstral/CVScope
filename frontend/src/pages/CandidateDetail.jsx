import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { getDetalleHojaDeVida } from "../api/client.js";
import useApi from "../hooks/useApi.js";
import RequisitoList from "../components/RequisitoList.jsx";
import ScoreMeter from "../components/ScoreMeter.jsx";
import StatusPill from "../components/StatusPill.jsx";
import { Cargando, ErrorCarga } from "../components/EstadoCarga.jsx";
import { claveDeNota, marcarClaves } from "../utils/texto.js";
import "./CandidateDetail.css";

const FUENTES = {
  dataset_ranking: "Dataset de ranking",
  dataset_seleccion: "Dataset de selección",
  registrado: "Candidato registrado",
};

export default function CandidateDetail() {
  const { cvId } = useParams();
  const [searchParams] = useSearchParams();
  const rolId = searchParams.get("rolId");
  const navigate = useNavigate();
  const { status, data, error, reload } = useApi(
    () => getDetalleHojaDeVida(cvId, rolId),
    [cvId, rolId],
  );

  return (
    <div className="detail-page">
      <button type="button" className="detail-page__back" onClick={() => navigate(-1)}>
        ← Volver
      </button>

      {status === "loading" && <Cargando texto="Evaluando hoja de vida…" />}
      {status === "error" && <ErrorCarga mensaje={error} onRetry={reload} />}
      {status === "success" && <Detalle cv={data} />}
    </div>
  );
}

function Detalle({ cv }) {
  const claves = cv.evaluacion.map((e) => claveDeNota(e.nota)).filter(Boolean);
  const ref = cv.referencia;
  const coincide = ref ? ref.apto === (cv.estado === "apto") : null;

  return (
    <>
      <header className="page-header">
        <div className="page-header__row">
          <h1>{cv.nombre}</h1>
          <span className="chip">{FUENTES[cv.fuente] ?? cv.fuente}</span>
        </div>
        <p className="page-header__subtitle">
          {cv.email && `${cv.email} · `}Rol: {cv.rol_nombre} · {cv.anios_experiencia} años de
          experiencia · <code>{cv.id}</code>
        </p>
      </header>

      <div className="detail-page__grid">
        <div className="detail-page__main">
          <section className="card detail-summary">
            <ScoreMeter score={cv.score} size="lg" />
            <div className="detail-summary__body">
              <StatusPill estado={cv.estado} />
              <p>{cv.explicacion}</p>
            </div>
          </section>

          <section>
            <h2 className="section-title">Evaluación de requisitos</h2>
            <RequisitoList evaluacion={cv.evaluacion} referencia={ref} />
          </section>
        </div>

        <aside className="detail-page__side">
          {ref && (
            <section className="card detail-ref">
              <h2 className="section-title">Etiqueta del dataset</h2>
              <dl>
                <dt>Veredicto real</dt>
                <dd>{ref.apto ? "Apto" : "No apto"}</dd>
                {ref.puntaje_referencia !== null && (
                  <>
                    <dt>Puntaje de referencia</dt>
                    <dd>{ref.puntaje_referencia}</dd>
                  </>
                )}
                {ref.posicion_referencia !== null && (
                  <>
                    <dt>Posición de referencia</dt>
                    <dd>#{ref.posicion_referencia}</dd>
                  </>
                )}
              </dl>
              <p
                className={`detail-ref__veredicto detail-ref__veredicto--${coincide ? "ok" : "ko"}`}
              >
                {coincide
                  ? "✓ El sistema coincide con la etiqueta"
                  : "✕ El sistema no coincide con la etiqueta"}
              </p>
            </section>
          )}

          <section className="card detail-cv">
            <h2 className="section-title">Hoja de vida</h2>
            <p className="detail-cv__texto">
              {marcarClaves(cv.hoja_de_vida_texto, claves).map((parte, i) =>
                parte.marcado ? (
                  <mark key={i}>{parte.texto}</mark>
                ) : (
                  <span key={i}>{parte.texto}</span>
                ),
              )}
            </p>
          </section>

          <Link to={`/ranking/${cv.rol_id}`} className="btn btn--ghost">
            Ver top 5 de {cv.rol_nombre}
          </Link>
        </aside>
      </div>
    </>
  );
}
