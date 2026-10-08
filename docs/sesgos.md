# Sesgos y equidad en CVScope

CVScope ayuda a preseleccionar personas para un empleo, así que un error del
sistema afecta oportunidades reales. Este documento resume los riesgos de
sesgo que identificamos, qué hace el sistema para mitigarlos, cómo se verifica
y qué limitaciones siguen abiertas.

## Riesgos identificados

| Riesgo | Por qué importa en CVScope |
|---|---|
| **Nombre** | El nombre sugiere género y origen étnico o regional. La red competitiva aprende de las palabras del texto; si viera nombres, podría asociarlos con "mejores" hojas de vida. |
| **Ciudad** | Puede funcionar como indicador indirecto de origen o de nivel socioeconómico (por ejemplo, Bogotá frente a Quibdó). |
| **Género** | En español, las profesiones llevan marca de género (*ingeniera/ingeniero*). |
| **Edad y estado civil** | Muchas hojas de vida incluyen edad, fecha de nacimiento o estado civil; no son criterios del cargo. |
| **Datos de contacto e identidad** | Correo, teléfono y documento no aportan al cargo y no deben salir hacia servicios externos (Gemini). |

## Qué hace el sistema

1. **Anonimización antes de la red competitiva y de Gemini** (`backend/app/services/anonimizador.py`).
   Se quitan nombre, correo, teléfono, URLs, documento, edad, fecha de
   nacimiento, estado civil, sexo/género y ciudades (32 capitales de
   departamento y los municipios grandes, con o sin tilde). Las profesiones se
   neutralizan (*ingeniera/ingeniero → ingenierx*). Los años de experiencia se
   conservan porque sí son un criterio del cargo. El evaluador por palabras
   clave y el clasificador de rol reciben el texto original; el primero solo
   busca evidencia de los requisitos y la auditoría confirma que no depende de
   datos personales.
2. **La red competitiva no ve ni siquiera los marcadores** (`[CANDIDATO]`,
   `[DATO PERSONAL]`…). Si quedaran como palabras, "este CV menciona la edad"
   sería una señal más.
3. **Gemini recibe el texto anonimizado.** Además debe citar literalmente la
   evidencia de cada requisito: si la cita no está en el CV, el requisito se
   marca como no cumplido. Así se evitan veredictos inventados.
4. **Explicabilidad**: cada veredicto muestra el fragmento del CV que lo
   sustenta y cada duelo explica por qué ganó una hoja de vida.

## Cómo se verifica

**Auditoría con contrafactuales** (`backend/scripts/auditar_sesgos.py`). A cada
una de las 60 hojas de vida del dataset de ranking se le cambia **solo** un
dato y se mide cuánto cambia su evaluación:

| Dato cambiado | Variación máx. de la fuerza (red) | Variación máx. del puntaje (palabras clave) |
|---|---|---|
| Nombre | 0.0000 | 0.0000 |
| Ciudad | 0.0000 | 0.0000 |
| Género de la profesión | 0.0000 | 0.0000 |
| Edad y estado civil | 0.0000 | 0.0000 |

Esta auditoría **encontró dos fugas reales** que se corrigieron:
- Una ciudad fuera de la lista inicial (Quibdó) cambiaba la fuerza de la red
  hasta **4.8 puntos**.
- El marcador `[DATO PERSONAL]` hacía que mencionar la edad cambiara la fuerza
  hasta **5.7 puntos**.

Además, las pruebas automáticas (`backend/tests/test_anonimizador.py`,
`test_red_competitiva.py`) verifican que dos hojas de vida que solo difieren en
nombre, ciudad y género producen exactamente el mismo vector de entrada.

## Limitaciones que siguen abiertas

- **La experiencia pesa un 20 %** del puntaje (con tope de 12 años). Es un
  criterio legítimo del cargo, pero también se correlaciona con la edad. El tope
  limita la ventaja de quienes tienen más años, aunque no la elimina.
- **Variables indirectas que no se quitan**: universidad, empresas anteriores o
  cursos pueden reflejar nivel socioeconómico o región. Quitarlas también
  quitaría información relevante del cargo.
- **Lista cerrada de ciudades**: un municipio pequeño o una ciudad extranjera
  que no esté en la lista no se anonimiza. La auditoría sirve para detectarlo.
- **Datos sintéticos**: los datasets se generaron con nombres y ciudades al
  azar, por lo que no reflejan los sesgos de datos históricos reales. Con hojas
  de vida reales habría que repetir la auditoría y medir resultados por grupo
  (por ejemplo, tasa de aptos por género), con su debido consentimiento.
- **Gemini** puede tener sesgos propios. La anonimización y la exigencia de
  citas reducen el riesgo, pero no lo eliminan.

## Uso responsable

- CVScope **apoya** la preselección; no reemplaza la decisión humana. Ninguna
  hoja de vida debería descartarse solo porque el sistema la marcó como no apta.
- Las explicaciones (evidencia por requisito, duelos) existen para que quien
  revise pueda contradecir al sistema.
- En Colombia, el tratamiento de hojas de vida está sujeto a la Ley 1581 de 2012
  (protección de datos personales): se necesita autorización de la persona y una
  finalidad clara. Anonimizar antes de enviar datos a un servicio externo como
  Gemini va en esa línea.
