// Quita tildes sin cambiar la longitud del texto (para buscar sin distinguir acentos).
export function sinTildes(texto) {
  return texto.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
}

/**
 * Divide `texto` en partes marcando las apariciones de `claves`
 * (sin distinguir mayúsculas ni tildes). Devuelve [{ texto, marcado }].
 */
export function marcarClaves(texto, claves) {
  const limpias = claves.filter(Boolean);
  if (!texto || limpias.length === 0) return [{ texto, marcado: false }];

  const nfc = texto.normalize("NFC");
  const base = sinTildes(nfc);
  if (base.length !== nfc.length) return [{ texto, marcado: false }];

  const escapadas = limpias.map((c) => sinTildes(c).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const patron = new RegExp(`(?<![a-z0-9])(${escapadas.join("|")})(?![a-z0-9])`, "g");

  const partes = [];
  let ultimo = 0;
  for (const match of base.matchAll(patron)) {
    if (match.index > ultimo)
      partes.push({ texto: nfc.slice(ultimo, match.index), marcado: false });
    partes.push({ texto: nfc.slice(match.index, match.index + match[0].length), marcado: true });
    ultimo = match.index + match[0].length;
  }
  if (ultimo < nfc.length) partes.push({ texto: nfc.slice(ultimo), marcado: false });
  return partes;
}

// La nota del backend trae la palabra clave encontrada entre « ».
export function claveDeNota(nota) {
  return nota?.match(/«(.+?)»/)?.[1] ?? null;
}

export const ETIQUETA_ROL = {
  fullstack: "Full Stack",
  rrhh: "Recursos Humanos",
  ventas: "Ventas",
  marketing: "Marketing Digital",
};
