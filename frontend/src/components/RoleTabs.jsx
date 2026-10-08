import "./RoleTabs.css";

export default function RoleTabs({ roles, value, onChange }) {
  return (
    <div className="role-tabs" role="tablist" aria-label="Rol">
      {roles.map((rol) => {
        const activo = String(rol.id) === String(value);
        return (
          <button
            key={rol.id}
            type="button"
            role="tab"
            aria-selected={activo}
            className={`role-tabs__tab ${activo ? "role-tabs__tab--active" : ""}`}
            onClick={() => onChange(rol)}
          >
            {rol.nombre}
          </button>
        );
      })}
    </div>
  );
}
