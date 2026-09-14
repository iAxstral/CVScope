// MOCK: reemplazar con GET /preseleccion/ranking/{rol_id} cuando exista
// Estructura anticipada en base al docstring de app/routers/preseleccion.py (Paso 3).
export const mockRanking = [
  {
    id: 1,
    nombre: "Valentina Rojas",
    email: "valentina.rojas@email.com",
    score: 92,
    estado: "apto",
    requisitosDestacados: [
      { texto: "React", cumple: true },
      { texto: "Node.js", cumple: true },
      { texto: "Bases de datos SQL/NoSQL", cumple: true },
    ],
  },
  {
    id: 2,
    nombre: "Marco Antonio Díaz",
    email: "marco.diaz@email.com",
    score: 81,
    estado: "apto",
    requisitosDestacados: [
      { texto: "JavaScript/TypeScript", cumple: true },
      { texto: "React", cumple: true },
      { texto: "Node.js", cumple: false },
    ],
  },
  {
    id: 3,
    nombre: "Camila Fuentes",
    email: "camila.fuentes@email.com",
    score: 74,
    estado: "apto",
    requisitosDestacados: [
      { texto: "JavaScript/TypeScript", cumple: true },
      { texto: "Bases de datos SQL/NoSQL", cumple: true },
      { texto: "React", cumple: false },
    ],
  },
  {
    id: 4,
    nombre: "Ignacio Herrera",
    email: "ignacio.herrera@email.com",
    score: 58,
    estado: "no_apto",
    requisitosDestacados: [
      { texto: "JavaScript/TypeScript", cumple: true },
      { texto: "React", cumple: false },
      { texto: "Node.js", cumple: false },
    ],
  },
  {
    id: 5,
    nombre: "Sofía Contreras",
    email: "sofia.contreras@email.com",
    score: 41,
    estado: "no_apto",
    requisitosDestacados: [
      { texto: "JavaScript/TypeScript", cumple: false },
      { texto: "React", cumple: false },
      { texto: "Bases de datos SQL/NoSQL", cumple: false },
    ],
  },
];
