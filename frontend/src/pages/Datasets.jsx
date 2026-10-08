import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getResumenDatasets, listarDataset } from "../api/client.js";
import useApi from "../hooks/useApi.js";
import StatTile from "../components/StatTile.jsx";
import StatusPill from "../components/StatusPill.jsx";
import { Cargando, ErrorCarga } from "../components/EstadoCarga.jsx";
import { ETIQUETA_ROL } from "../utils/texto.js";
import "./Datasets.css";

const POR_PAGINA = 15;
const TABS = [
  { id: "seleccion", label: "Selección", titulo: "Dataset de selección" },
  { id: "ranking", label: "Ranking top 5", titulo: "Dataset de ranking" },
];

export default function Datasets() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get("d") === "ranking" ? "ranking" : "seleccion";
  const resumen = useApi(getResumenDatasets);
  const actual = resumen.data?.find((d) => d.nombre === tab);

  return (
    <div className="ds-page">
      <header className="page-header">
        <h1>Datasets</h1>
        <p className="page-header__subtitle">
          CVScope trabaja con dos datasets de hojas de vida: uno para <strong>seleccionar</strong>{" "}
          (rol y apto/no apto) y otro para el <strong>ranking</strong> de las 5 mejores por rol.
        </p>
      </header>

      <div className="role-tabs" role="tablist" aria-label="Dataset">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={`role-tabs__tab ${tab === t.id ? "role-tabs__tab--active" : ""}`}
            onClick={() => setSearchParams({ d: t.id })}
          >
            {t.label}
          </button>
        ))}
      </div>

      {resumen.status === "loading" && <Cargando texto="Cargando datasets…" />}
      {resumen.status === "error" && (
        <ErrorCarga mensaje={resumen.error} onRetry={resumen.reload} />
      )}
      {actual && <Resumen dataset={actual} titulo={TABS.find((t) => t.id === tab).titulo} />}
      {actual && <Tabla key={tab} nombre={tab} roles={Object.keys(actual.por_rol)} />}
    </div>
  );
}

function Resumen({ dataset, titulo }) {
  const roles = Object.entries(dataset.por_rol);
  return (
    <section className="ds-resumen">
      <div className="card ds-resumen__info">
        <h2 className="section-title">{titulo}</h2>
        <p>{dataset.descripcion}</p>
        <code className="ds-resumen__file">backend/{dataset.archivo}</code>
      </div>

      <div className="ds-resumen__stats">
        <StatTile label="Hojas de vida" value={dataset.total} />
        <StatTile
          label="Aptas"
          value={dataset.aptos}
          hint={`${Math.round((dataset.aptos / dataset.total) * 100)}% del total`}
        />
        <StatTile label="Roles" value={roles.length} />
      </div>

      <div className="card ds-dist">
        <h3 className="ds-dist__title">Aptos vs. no aptos por rol</h3>
        <div className="ds-dist__legend" aria-hidden="true">
          <span>
            <i className="ds-dist__swatch ds-dist__swatch--apto" /> Apto
          </span>
          <span>
            <i className="ds-dist__swatch ds-dist__swatch--no" /> No apto
          </span>
        </div>
        <ul className="ds-dist__rows">
          {roles.map(([rol, s]) => {
            const noAptos = s.total - s.aptos;
            return (
              <li key={rol} className="ds-dist__row">
                <span className="ds-dist__rol">{ETIQUETA_ROL[rol] ?? rol}</span>
                <span className="ds-dist__bar">
                  <span
                    className="ds-dist__seg ds-dist__seg--apto"
                    style={{ flexGrow: s.aptos }}
                    title={`${ETIQUETA_ROL[rol] ?? rol}: ${s.aptos} aptos`}
                  />
                  <span
                    className="ds-dist__seg ds-dist__seg--no"
                    style={{ flexGrow: noAptos }}
                    title={`${ETIQUETA_ROL[rol] ?? rol}: ${noAptos} no aptos`}
                  />
                </span>
                <span className="ds-dist__nums">
                  {s.aptos} / {s.total}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}

function Tabla({ nombre, roles }) {
  const [rol, setRol] = useState("");
  const [apto, setApto] = useState("");
  const [q, setQ] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [pagina, setPagina] = useState(0);

  // Espera a que el usuario deje de escribir antes de consultar.
  useEffect(() => {
    const t = setTimeout(() => {
      setBusqueda(q.trim());
      setPagina(0);
    }, 300);
    return () => clearTimeout(t);
  }, [q]);

  const { status, data, error, reload } = useApi(
    () =>
      listarDataset(nombre, {
        rol,
        apto,
        q: busqueda,
        limit: POR_PAGINA,
        offset: pagina * POR_PAGINA,
      }),
    [nombre, rol, apto, busqueda, pagina],
  );

  const esRanking = nombre === "ranking";
  const totalPaginas = data ? Math.max(1, Math.ceil(data.total / POR_PAGINA)) : 1;

  return (
    <section className="ds-tabla">
      <div className="ds-tabla__filtros">
        <select
          className="input"
          value={rol}
          onChange={(e) => {
            setRol(e.target.value);
            setPagina(0);
          }}
          aria-label="Filtrar por rol"
        >
          <option value="">Todos los roles</option>
          {roles.map((r) => (
            <option key={r} value={r}>
              {ETIQUETA_ROL[r] ?? r}
            </option>
          ))}
        </select>
        <select
          className="input"
          value={apto}
          onChange={(e) => {
            setApto(e.target.value);
            setPagina(0);
          }}
          aria-label="Filtrar por veredicto"
        >
          <option value="">Apto y no apto</option>
          <option value="true">Solo aptos</option>
          <option value="false">Solo no aptos</option>
        </select>
        <input
          className="input"
          type="search"
          placeholder="Buscar en el texto (ej. React, nómina, HubSpot)…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      {status === "error" && <ErrorCarga mensaje={error} onRetry={reload} />}

      <div className={`ds-tabla__wrap ${status === "loading" ? "ds-tabla__wrap--loading" : ""}`}>
        <table>
          <thead>
            <tr>
              {esRanking && <th>Pos. ref.</th>}
              <th>{esRanking ? "Candidato" : "Hoja de vida"}</th>
              <th>Rol</th>
              <th className="num">Años exp.</th>
              <th>Requisitos cumplidos</th>
              {esRanking && <th className="num">Puntaje ref.</th>}
              <th>Etiqueta</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((f) => (
              <tr key={f.id}>
                {esRanking && (
                  <td className="num">
                    {f.posicion_referencia ? `#${f.posicion_referencia}` : "—"}
                  </td>
                )}
                <td>
                  <div className="ds-tabla__cv">
                    <Link to={`/candidatos/${f.id}`} className="link">
                      {esRanking ? f.nombre : f.id}
                    </Link>
                    <span>{f.hoja_de_vida_texto.slice(0, 110)}…</span>
                  </div>
                </td>
                <td>{ETIQUETA_ROL[f.rol] ?? f.rol}</td>
                <td className="num">{f.anios_experiencia}</td>
                <td className="ds-tabla__reqs">
                  {f.requisitos_cumplidos.length ? f.requisitos_cumplidos.join(" · ") : "Ninguno"}
                </td>
                {esRanking && <td className="num">{f.puntaje_referencia}</td>}
                <td>
                  <StatusPill estado={f.apto ? "apto" : "no_apto"} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data?.items.length === 0 && (
          <p className="empty-state">No hay hojas de vida con esos filtros.</p>
        )}
      </div>

      {data && (
        <div className="ds-tabla__paginacion">
          <span>
            {data.total} resultado{data.total === 1 ? "" : "s"} · página {pagina + 1} de{" "}
            {totalPaginas}
          </span>
          <div>
            <button
              type="button"
              className="btn btn--ghost btn--sm"
              disabled={pagina === 0}
              onClick={() => setPagina((p) => p - 1)}
            >
              ← Anterior
            </button>
            <button
              type="button"
              className="btn btn--ghost btn--sm"
              disabled={pagina + 1 >= totalPaginas}
              onClick={() => setPagina((p) => p + 1)}
            >
              Siguiente →
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
