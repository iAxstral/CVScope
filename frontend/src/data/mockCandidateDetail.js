// MOCK: reemplazar con POST /preseleccion/evaluar cuando exista
// Estructura anticipada en base al docstring de app/routers/preseleccion.py (Paso 2).
const mockCandidateDetails = {
  1: {
    id: 1,
    nombre: "Valentina Rojas",
    email: "valentina.rojas@email.com",
    rolNombre: "Full Stack Developer",
    score: 92,
    estado: "apto",
    evaluacion: [
      { requisito: "JavaScript/TypeScript", cumple: true, nota: "5 años de experiencia mencionados, con proyectos en TypeScript documentados en el CV." },
      { requisito: "React o similar", cumple: true, nota: "Menciona React y Next.js en dos proyectos recientes." },
      { requisito: "Node.js o backend equivalente", cumple: true, nota: "Experiencia con Express y APIs REST." },
      { requisito: "Bases de datos SQL/NoSQL", cumple: true, nota: "Uso de PostgreSQL y MongoDB en roles anteriores." },
    ],
  },
  2: {
    id: 2,
    nombre: "Marco Antonio Díaz",
    email: "marco.diaz@email.com",
    rolNombre: "Full Stack Developer",
    score: 81,
    estado: "apto",
    evaluacion: [
      { requisito: "JavaScript/TypeScript", cumple: true, nota: "Experiencia sólida en JavaScript moderno (ES6+)." },
      { requisito: "React o similar", cumple: true, nota: "Dos años usando React en un rol previo." },
      { requisito: "Node.js o backend equivalente", cumple: false, nota: "El CV no menciona experiencia de backend, solo frontend." },
      { requisito: "Bases de datos SQL/NoSQL", cumple: true, nota: "Menciona uso básico de MySQL." },
    ],
  },
  3: {
    id: 3,
    nombre: "Camila Fuentes",
    email: "camila.fuentes@email.com",
    rolNombre: "Full Stack Developer",
    score: 74,
    estado: "apto",
    evaluacion: [
      { requisito: "JavaScript/TypeScript", cumple: true, nota: "Buen dominio de JavaScript según proyectos listados." },
      { requisito: "React o similar", cumple: false, nota: "No se encontró mención de React ni frameworks similares." },
      { requisito: "Node.js o backend equivalente", cumple: true, nota: "Experiencia con Node.js y NestJS." },
      { requisito: "Bases de datos SQL/NoSQL", cumple: true, nota: "Experiencia con PostgreSQL." },
    ],
  },
  4: {
    id: 4,
    nombre: "Ignacio Herrera",
    email: "ignacio.herrera@email.com",
    rolNombre: "Full Stack Developer",
    score: 58,
    estado: "no_apto",
    evaluacion: [
      { requisito: "JavaScript/TypeScript", cumple: true, nota: "Nivel básico mencionado en cursos, sin proyectos documentados." },
      { requisito: "React o similar", cumple: false, nota: "No se encontró evidencia de experiencia con frameworks frontend." },
      { requisito: "Node.js o backend equivalente", cumple: false, nota: "No se encontró experiencia de backend en el CV." },
      { requisito: "Bases de datos SQL/NoSQL", cumple: true, nota: "Menciona un curso introductorio de SQL." },
    ],
  },
  5: {
    id: 5,
    nombre: "Sofía Contreras",
    email: "sofia.contreras@email.com",
    rolNombre: "Full Stack Developer",
    score: 41,
    estado: "no_apto",
    evaluacion: [
      { requisito: "JavaScript/TypeScript", cumple: false, nota: "El CV no menciona lenguajes de programación." },
      { requisito: "React o similar", cumple: false, nota: "No se encontró experiencia con frameworks frontend." },
      { requisito: "Node.js o backend equivalente", cumple: false, nota: "No se encontró experiencia de backend." },
      { requisito: "Bases de datos SQL/NoSQL", cumple: false, nota: "No se menciona experiencia con bases de datos." },
    ],
  },
};

const fallbackId = 1;

export function getMockCandidateDetail(candidatoId) {
  return mockCandidateDetails[candidatoId] ?? mockCandidateDetails[fallbackId];
}
