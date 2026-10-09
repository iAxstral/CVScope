import "./LvqPanel.css";

const ETIQUETA = { apto: "Apto", no_apto: "No apto" };

export default function LvqPanel({ lvq }) {
  const m = lvq.metricas;
  const prototipos = [...lvq.prototipos].sort(
    (a, b) => a.fraccion_requisitos - b.fraccion_requisitos,
  );

  return (
    <section className="card lvq-panel">
      <div className="lvq-panel__head">
        <h2 className="section-title">Capa competitiva que aprende (LVQ) · apto / no apto</h2>
        <p>
          Cada neurona es un prototipo de hoja de vida "apta" o "no apta". Ante una hoja de vida
          gana la neurona más cercana y su clase es el veredicto. Al entrenar, la ganadora se acerca
          a la hoja de vida si acertó y se aleja si falló (regla de Kohonen); así la red aprende el
          criterio de los datos en vez de usar un umbral fijo.
        </p>
      </div>

      <figure
        className="lvq-panel__eje"
        aria-label="Prototipos aprendidos según su fracción de requisitos"
      >
        <div className="lvq-panel__linea">
          {prototipos.map((p) => (
            <span
              key={p.neurona}
              className={`lvq-panel__punto lvq-panel__punto--${p.clase}`}
              style={{ left: `${p.fraccion_requisitos * 100}%` }}
              title={`Neurona ${p.neurona}: ${ETIQUETA[p.clase]}, ${Math.round(p.fraccion_requisitos * 100)} % de requisitos, ${p.anios_experiencia} años`}
            />
          ))}
        </div>
        <div className="lvq-panel__ticks" aria-hidden="true">
          <span>0 %</span>
          <span>50 %</span>
          <span>100 % de requisitos</span>
        </div>
        <figcaption>
          Posición de cada neurona prototipo según la fracción de requisitos que aprendió.
        </figcaption>
      </figure>

      <ul className="lvq-panel__prototipos">
        {prototipos.map((p) => (
          <li key={p.neurona}>
            <span className={`status-pill status-pill--${p.clase}`}>{ETIQUETA[p.clase]}</span>
            <span>
              Neurona {p.neurona} · {Math.round(p.fraccion_requisitos * 100)} % de requisitos ·{" "}
              {p.anios_experiencia} años
            </span>
          </li>
        ))}
      </ul>

      <dl className="lvq-panel__metricas">
        <div>
          <dt>Exactitud en prueba</dt>
          <dd>
            {m.exactitud_prueba?.toFixed(3)}
            <small>palabras clave: {m.exactitud_prueba_base?.toFixed(3)}</small>
          </dd>
        </div>
        <div>
          <dt>F1 en prueba</dt>
          <dd>
            {m.f1_prueba?.toFixed(3)}
            <small>palabras clave: {m.f1_prueba_base?.toFixed(3)}</small>
          </dd>
        </div>
      </dl>
    </section>
  );
}
