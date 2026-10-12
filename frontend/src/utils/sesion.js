// Sesión del usuario en el navegador. localStorage puede fallar (modo
// privado, almacenamiento bloqueado), así que todo va en try/catch.
const CLAVE = "cvscope.sesion";

export function leerSesion() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE)) ?? null;
  } catch {
    return null;
  }
}

export function guardarSesion(sesion) {
  try {
    localStorage.setItem(CLAVE, JSON.stringify(sesion));
  } catch {
    // sin almacenamiento la sesión dura lo que dure la pestaña en memoria
  }
  sesionEnMemoria = sesion;
}

export function cerrarSesion() {
  try {
    localStorage.removeItem(CLAVE);
  } catch {
    // nada que limpiar
  }
  sesionEnMemoria = null;
}

let sesionEnMemoria = leerSesion();

export function sesionActual() {
  return sesionEnMemoria;
}
