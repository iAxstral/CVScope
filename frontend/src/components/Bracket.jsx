import "./Bracket.css";

function Lado({ competidor, gano, prob }) {
  return (
    <div className={`bracket-side ${gano ? "bracket-side--win" : "bracket-side--lose"}`}>
      <span className="bracket-side__name" title={competidor?.nombre}>
        {competidor?.nombre ?? "—"}
      </span>
      <span className="bracket-side__prob">{Math.round(prob * 100)}%</span>
    </div>
  );
}

export default function Bracket({ rondas, participantes, campeonId, onSelectDuelo }) {
  const porId = Object.fromEntries(participantes.map((p) => [p.id, p]));

  return (
    <div className="bracket" role="list" aria-label="Cuadro del torneo">
      {rondas.map((ronda) => (
        <section key={ronda.numero} className="bracket-round" role="listitem">
          <h3 className="bracket-round__title">
            {ronda.nombre}
            <span>
              {ronda.duelos.length} duelo{ronda.duelos.length === 1 ? "" : "s"}
            </span>
          </h3>
          <ol className="bracket-round__matches">
            {ronda.duelos.map((d) => (
              <li key={`${d.a}-${d.b}`}>
                <button
                  type="button"
                  className="bracket-match"
                  onClick={() => onSelectDuelo?.(d)}
                  title={d.explicacion}
                >
                  <Lado competidor={porId[d.a]} gano={d.ganador === d.a} prob={d.prob_a} />
                  <Lado competidor={porId[d.b]} gano={d.ganador === d.b} prob={1 - d.prob_a} />
                </button>
              </li>
            ))}
            {ronda.pases.map((id) => (
              <li key={`bye-${id}`} className="bracket-bye">
                <span className="bracket-bye__name">{porId[id]?.nombre}</span>
                <span className="bracket-bye__tag">pasa directo</span>
              </li>
            ))}
          </ol>
        </section>
      ))}
      {campeonId && (
        <section className="bracket-round bracket-round--champion" role="listitem">
          <h3 className="bracket-round__title">Campeón</h3>
          <div className="bracket-champion">
            <span className="bracket-champion__trophy" aria-hidden="true">
              ★
            </span>
            {porId[campeonId]?.nombre}
          </div>
        </section>
      )}
    </div>
  );
}
