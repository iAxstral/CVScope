import "./StatusPill.css";

const LABELS = {
  apto: "Apto",
  no_apto: "No apto",
  pendiente: "Pendiente",
};

export default function StatusPill({ estado }) {
  return <span className={`status-pill status-pill--${estado}`}>{LABELS[estado] ?? estado}</span>;
}
