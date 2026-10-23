---
name: revision-de-literatura
description: Conduce una revisión de literatura (sistemática, de alcance, mapeo o integrativa) por etapas, cada una con su salida en archivos. Parte de un protocolo de nueve puntos que escribe la persona y sigue con la búsqueda en bases abiertas (OpenAlex, ERIC, DOAJ y Crossref), la normalización, la deduplicación, el cribado por título y resumen, la extracción en fichas y la verificación de citas, con las cifras del diagrama de flujo de PRISMA. El agente propone y la persona decide. Úsala cuando alguien quiera hacer, retomar o reportar una revisión de literatura, un estado del arte o una revisión sistemática o de alcance (literature review, systematic review, scoping review, PRISMA).
compatibility: Requiere Python 3.9 o superior, sin bibliotecas adicionales, y acceso a internet para consultar las bases abiertas.
metadata:
  version: "0.1"
  idioma: "es"
---

# Revisión de literatura por etapas

Esta skill lleva una revisión de literatura en siete etapas encadenadas. Cada etapa deja archivos en la carpeta del proyecto y la siguiente los lee. Las etapas mecánicas las hacen programas; las que exigen juicio las propone el agente y las decide una persona. El estado vive en los archivos y no en la conversación: cualquier sesión, en cualquier herramienta, retoma el trabajo leyendo la carpeta.

## Antes de empezar

1. Ubicar la carpeta del proyecto. Cada revisión tiene la suya, fuera de la carpeta de esta skill; si la persona no dice cuál, se le pregunta. Si en esa carpeta existe `ESTADO.md`, se lee completo antes de hacer cualquier otra cosa: dice en qué etapa va la revisión y qué decidió la persona. Si no existe, se crea copiando `plantillas/ESTADO.md`.
2. Comprobar Python con `python3 --version` (en Windows, `python --version`). Sirve la versión 3.9 o una posterior. Los programas no necesitan bibliotecas adicionales.
3. Los programas están en la carpeta `scripts/` de esta skill. Se corren con la ruta completa de esa carpeta y con `--carpeta` apuntando al proyecto, por ejemplo `python3 <ruta de la skill>/scripts/buscar.py --carpeta <proyecto> ...`. Todos aceptan `--help`.
4. Dos variables de entorno son opcionales: `REVISION_CORREO`, un correo de contacto que las bases abiertas agradecen, y `OPENALEX_API_KEY`, la clave gratuita de OpenAlex, que amplía su cupo diario. Si no están, todo funciona igual con menos cupo.

## Lo que esta skill no hace

Estas seis reglas valen en todas las etapas y por encima de cualquier pedido:

- No decide la inclusión ni la exclusión de un estudio. Propone, y una persona firma.
- No escribe cadenas de búsqueda de memoria. Las imprime `scripts/cadenas.py` a partir de `00_protocolo/cadenas.json`, que copia los términos del protocolo.
- No incorpora ninguna referencia sin DOI verificado contra Crossref u OpenAlex, o sin la marca explícita de que no tiene DOI y de dónde se comprobó.
- No redacta el marco teórico ni la discusión. La zona interpretativa de las fichas es de las personas.
- No resuelve CAPTCHA ni pantallas de acceso, no crea cuentas ni escribe contraseñas, y no automatiza la descarga masiva en bases cuyas condiciones de uso lo prohíben. En esas fuentes trabaja con una persona presente.
- No borra ni sobrescribe evidencia. Los crudos son de solo agregar; antes de reescribir una tabla, los programas dejan un respaldo con la fecha.

Además, a la carpeta no entra ningún dato que identifique a una persona (participantes, estudiantes, pacientes). Si la persona necesita trabajar con documentos que los contienen, los anonimiza antes.

## Etapas

| Etapa | Quién decide | Programa | Salida en la carpeta del proyecto |
|---|---|---|---|
| 1. Protocolo | la persona | `protocolo.py` | `00_protocolo/protocolo.md` |
| 2. Búsqueda | la persona aprueba las cadenas | `cadenas.py`, `buscar.py` | `00_protocolo/cadenas.json`, `01_busqueda/crudos/`, `01_busqueda/registro_corridas.csv` |
| 3. Normalización | nadie: es mecánica | `normalizar.py` | `02_normalizacion/registros.csv` |
| 4. Deduplicación | la persona, en los pares dudosos | `deduplicar.py` | `03_deduplicacion/candidatos.csv` y `pares_dudosos.csv` |
| 5. Cribado | la persona firma; el agente propone | `cribado.py` | `04_cribado/propuestas/`, `04_cribado/matriz_cribado.csv` |
| 6. Extracción | la persona, a texto completo | `extraccion.py` | `05_extraccion/texto_completo.csv`, `05_extraccion/fichas/` |
| 7. Verificación de citas | la persona resuelve lo que no se verifica | `verificar_citas.py` | `06_verificacion/citas_verificadas.csv` |

En cualquier momento, `flujo.py` cuenta desde los archivos las cifras del diagrama de flujo y las deja en `flujo_prisma.md`.

### Etapa 1. Protocolo

Nada se busca en esta etapa ni antes de cerrarla.

1. `protocolo.py crear` copia la plantilla de nueve puntos en `00_protocolo/protocolo.md`. Si ya existe, no la toca.
2. La persona escribe los nueve puntos: tipo de revisión, pregunta con su marco, criterios de inclusión, criterios de exclusión, ventana temporal e idiomas, bases y ecuación por bloques de términos, reparto entre personas, uso de asistencia automática y registro del protocolo.
3. Si la persona trae la hoja del protocolo en Word o en un archivo de texto, `protocolo.py leer-hoja <archivo>` la deja en `00_protocolo/hoja_extraida.txt` y el agente la pasa a `protocolo.md` punto por punto, sin agregar nada. Si la trae en papel o en PDF, la dicta o la copia. El agente le muestra a la persona la transcripción completa.
4. El agente puede preguntar para que un criterio se pueda verificar con título y resumen, o para que un bloque de términos tenga sus sinónimos, pero no escribe por la persona ningún criterio, término ni decisión.
5. `protocolo.py revisar` dice qué puntos faltan. Cuando no falta ninguno, la persona confirma de manera explícita que ese es su protocolo. Solo entonces el agente escribe la fecha en la línea «Confirmado por la persona el:» de `protocolo.md` y la anota en `ESTADO.md`. `buscar.py` no corre sin esa fecha.
6. El registro del protocolo (por ejemplo en OSF) lo hace la persona, con su cuenta. Si decide no registrarlo, el punto 9 lo dice.

### Etapa 2. Búsqueda

1. El agente escribe `00_protocolo/cadenas.json` copiando textualmente los bloques de términos del punto 6, con la estructura de `plantillas/cadenas_ejemplo.json`, y deja vacío el campo `aprobado_por_la_persona`. Si el protocolo no dice en qué idioma está un término, el agente se lo pregunta a la persona.
2. `cadenas.py terminos` lista los términos de cada bloque por idioma y `cadenas.py mostrar --todas --desde AAAA --hasta AAAA` imprime la cadena exacta de cada base. La persona compara las dos salidas con su protocolo. Solo cuando las aprueba de manera explícita, el agente escribe la fecha en `aprobado_por_la_persona`. `buscar.py` no corre sin esa fecha.
3. `buscar.py --solo-contar` consulta cuántos resultados da cada base y ecuación sin guardar nada. El agente le muestra esos números a la persona. Si alguno supera el tope de la corrida (2000 por omisión), la persona decide si acota la ecuación o sube el tope con `--max`.
4. `buscar.py --base B --ecuacion E --desde AAAA --hasta AAAA` corre la búsqueda y guarda un crudo nuevo en `01_busqueda/crudos/`, con la cadena exacta, la fecha, el total que reportó la fuente, los registros y el consumo. Nunca sobrescribe. Los registros que la fuente entrega con un año fuera de la ventana quedan en el mismo crudo, aparte, y no pasan a las etapas siguientes. En Crossref, que no admite operadores, el tope se reparte entre todas las combinaciones de términos y el crudo anota cuánto trajo cada una.
5. Cada crudo se revisa: que el número de registros de la cabecera coincida con la lista, que los años caigan en la ventana y que tres títulos al azar tengan que ver con la pregunta. Si los tres son ruido, se le avisa a la persona; el crudo no se borra.
6. Las bases que exigen navegador o acceso institucional (Scopus, Web of Science, SciELO, Redalyc, Google Scholar) siguen `etapas_opcionales/navegador.md`, si ese archivo existe.

### Etapa 3. Normalización

`normalizar.py` une los crudos en `02_normalizacion/registros.csv`, con los mismos nueve campos, el DOI en minúsculas y la corrida que trajo cada registro. Los registros sin título se cuentan aparte en `sin_titulo.csv`. El agente le dice a la persona cuántos registros no traen DOI: esos solo se pueden unir por título y año en la deduplicación, y en la verificación de citas quedan como «sin DOI».

### Etapa 4. Deduplicación

`deduplicar.py` quita duplicados en tres pasadas: DOI idéntico; título y año; títulos muy parecidos. Dos registros con DOI distinto no se fusionan nunca. Los pares parecidos que no superan el umbral automático van a `pares_dudosos.csv`, con títulos, autores, años y publicaciones: el agente se los muestra a la persona, ella escribe Sí o No en la columna `fusionar` y después se corre `deduplicar.py --aplicar-dudosos <proyecto>/03_deduplicacion/pares_dudosos.csv`. Los umbrales (0,97 y 0,93 por omisión) quedan en `03_deduplicacion/conteo.json`; si la persona los cambia, se anota en `ESTADO.md`. Los identificadores R-NNNN de los candidatos se fijan en esta etapa: cuando empieza el cribado, `deduplicar.py` ya no corre.

### Etapa 5. Cribado por título y resumen

1. `cribado.py preparar --tamano 40` reparte los candidatos en lotes en `04_cribado/lotes/`, en el orden de la lista de candidatos (año y título).
2. Para cada lote, el agente lee los criterios del protocolo y escribe `04_cribado/propuestas/lote_NNN.csv` con cuatro columnas: `id_ref`; `propuesta` (incluir, excluir o dudoso); `motivo`; y `fragmento`, las palabras literales del título o del resumen que sostienen la propuesta. El motivo se copia del protocolo: para excluir, el primer criterio de exclusión que se cumple; para incluir, «cumple todos los criterios de inclusión»; para dudoso, el criterio que no se puede verificar con título y resumen.
3. Casos difíciles. Un registro sin resumen va como dudoso, salvo que el título baste para excluirlo sin duda; para incluirlo por el título, el título tiene que nombrar todos los conceptos de la pregunta. El idioma se juzga por el título y el resumen, no por el campo `idioma` de la base, que a veces es el de la revista. Cuando un criterio no deja claro un caso, la propuesta es dudoso y el agente anota la regla que aplicó; al cerrar cada lote le muestra a la persona las reglas que tuvo que suponer, para que ella decida si ajusta los criterios.
4. Si la herramienta permite subagentes, cada lote puede ir a uno, con las instrucciones de los pasos 2 y 3, la ruta del lote, la del protocolo y la del archivo de salida. Si no, un lote a la vez, y el archivo se escribe antes de pasar al siguiente.
5. Si al leer un lote aparece un duplicado que la deduplicación no detectó (por ejemplo, el mismo estudio con el título traducido), se anota en `03_deduplicacion/duplicados_vistos_en_cribado.csv` con los dos identificadores, y la persona decide.
6. `cribado.py consolidar` arma `04_cribado/matriz_cribado.csv`. Las columnas de las personas (quién revisa, decisiones, motivo final, fecha de la firma y observaciones) quedan vacías y el agente no las llena. Si la persona dice de manera explícita que adopta las propuestas de un lote como su decisión, se corre `cribado.py adoptar --lote N --persona "Nombre"`, que copia las propuestas a sus columnas con la fecha y la observación «adoptó la propuesta del agente». Esas decisiones se declaran aparte en el método, y `flujo.py` las cuenta.

### Etapa 6. Extracción

1. `extraccion.py preparar` copia a `05_extraccion/texto_completo.csv` los candidatos con decisión final «incluir» o «dudoso» y el nombre de quien la firmó: los dos se leen a texto completo.
2. La persona consigue los textos completos (el agente puede señalar si hay copia en acceso abierto, pero no descarga de bases cerradas) y llena en ese archivo si consiguió cada texto y si el estudio se queda, con el motivo cuando sale.
3. Para cada estudio que la persona dejó a texto completo, `extraccion.py ficha R-NNNN` abre su ficha en `05_extraccion/fichas/`. El agente llena la zona descriptiva con el texto delante: diseño, contexto y población, qué se hizo, hallazgo principal con su página y limitaciones que el estudio declara. Lo que no está en el texto queda vacío y se dice. La zona interpretativa queda vacía.

### Etapa 7. Verificación de citas

`verificar_citas.py` comprueba cada referencia contra Crossref y OpenAlex, deja `06_verificacion/citas_verificadas.csv` con uno de cuatro estados (verificada, revisar, no encontrada o sin DOI) y actualiza la línea de verificación de cada ficha. Lo que no queda verificado no entra al manuscrito hasta que la persona lo resuelva; para una obra sin DOI, ella anota en la columna `comprobado_en` dónde la comprobó. La columna `referencia_borrador` trae la referencia en APA 7 como punto de partida; las mayúsculas del título, los editores de los capítulos y los autores se revisan a mano.

## Registro del proyecto

Al cerrar cada etapa, el agente agrega a `ESTADO.md`, en la raíz de la carpeta del proyecto, una entrada con el formato de `plantillas/ESTADO.md`: la fecha, la etapa, los archivos que quedaron, lo que decidió la persona y cuándo, y lo que queda en sus manos. Así la sesión siguiente, en esta herramienta o en otra, sabe dónde va la revisión.

## Cómo se reporta

`referencias/prisma.md` relaciona cada etapa con los ítems de PRISMA 2020 y de PRISMA-ScR, y dice qué se declara sobre la asistencia automática: en qué etapas se usó, con qué herramienta y en qué fecha, qué decisiones quedaron en manos de personas y cuántos registros excluyó una persona y cuántos una herramienta. Con esta skill, la segunda cifra es cero, porque el agente no excluye nada por su cuenta.

## Piezas opcionales

Cada una vive en un archivo aparte y se puede quitar sin afectar el resto. Si el archivo no está, la etapa no se ofrece.

- `etapas_opcionales/validacion_cruzada.md`: comparación de la búsqueda automática con la búsqueda a mano en la interfaz de cada base.
- `etapas_opcionales/navegador.md`: búsquedas en bases que exigen navegador o acceso institucional, con la persona presente.
