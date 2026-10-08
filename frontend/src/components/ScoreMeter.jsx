import "./ScoreMeter.css";

export default function ScoreMeter({ score, size = "md" }) {
  const valor = Math.max(0, Math.min(100, Number(score) || 0));
  return (
    <div
      className={`score-meter score-meter--${size}`}
      role="meter"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={valor}
      aria-label={`Puntaje ${valor} de 100`}
    >
      <span className="score-meter__value">{valor.toFixed(valor % 1 ? 1 : 0)}</span>
      <span className="score-meter__track">
        <span className="score-meter__fill" style={{ width: `${valor}%` }} />
      </span>
    </div>
  );
}
