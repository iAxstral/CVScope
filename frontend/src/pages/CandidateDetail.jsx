import { Link, useParams } from "react-router-dom";
import { getMockCandidateDetail } from "../data/mockCandidateDetail.js";
import MockBadge from "../components/MockBadge.jsx";
import StatusPill from "../components/StatusPill.jsx";
import Highlight from "../components/Highlight.jsx";
import "./CandidateDetail.css";

export default function CandidateDetail() {
  const { candidatoId } = useParams();
  const candidato = getMockCandidateDetail(candidatoId);

  return (
    <div className="detail-page">
      <Link to="/dashboard" className="detail-page__back">
        ← Volver
      </Link>

      <header className="page-header">
        <div className="page-header__row">
          <h1>{candidato.nombre}</h1>
          <MockBadge />
        </div>
        <p className="page-header__subtitle">
          {candidato.email} · Rol: {candidato.rolNombre}
        </p>
      </header>

      <div className="detail-summary">
        <div className="detail-summary__score">
          <span className="detail-summary__label">Score</span>
          <span className="detail-summary__valor">{candidato.score}</span>
        </div>
        <StatusPill estado={candidato.estado} />
      </div>

      <section className="detail-requisitos">
        <h2>Evaluación de requisitos</h2>
        <ul className="detail-requisitos__list">
          {candidato.evaluacion.map((item) => (
            <li key={item.requisito} className="detail-requisito">
              <div className="detail-requisito__header">
                <Highlight variant={item.cumple ? "success" : "danger"}>{item.requisito}</Highlight>
                <span
                  className={`detail-requisito__veredicto detail-requisito__veredicto--${item.cumple ? "ok" : "no"}`}
                >
                  {item.cumple ? "Cumple" : "No cumple"}
                </span>
              </div>
              <p className="detail-requisito__nota">{item.nota}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
