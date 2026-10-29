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

1. Ubicar la carpeta del proyecto. Cada revisión tiene la suya; si la persona no dice cuál, se le pregunta. La carpeta de esta skill puede estar dentro de la del proyecto (por ejemplo, en `.claude/skills/`), pero el proyecto no puede estar dentro de la carpeta de la skill. Lo primero en la carpeta del proyecto es buscar `ESTADO.md` y, si existe, leerlo completo antes de seguir: dice en qué etapa va la revisión y qué decidió la persona. Si no existe, se crea copiando `plantillas/ESTADO.md`.
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
| 5. Cribado | la persona firma; el agente propone | `cribado.py` | `04_cribado/propuestas/`, `04_cribado/reglas_aplicadas.md`, `04_cribado/matriz_cribado.csv` |
| 6. Extracción | la persona, a texto completo | `extraccion.py` | `05_extraccion/texto_completo.csv`, `05_extraccion/fichas/` |
| 7. Verificación de citas | la persona resuelve lo que no se verifica | `verificar_citas.py` | `06_verificacion/citas_verificadas.csv` |

En cualquier momento, `flujo.py` cuenta desde los archivos las cifras del diagrama de flujo y las deja en `flujo_prisma.md`.

### Etapa 1. Protocolo

Nada se busca en esta etapa ni antes de cerrarla.

1. `protocolo.py crear` copia la plantilla de nueve puntos en `00_protocolo/protocolo.md`. Si ya existe, no la toca.
2. La persona escribe los nueve puntos: tipo de revisión, pregunta con su marco, criterios de inclusión, criterios de exclusión, ventana temporal e idiomas, bases y ecuación por bloques de términos, reparto entre personas, uso de asistencia automática y registro del protocolo.
3. Si la persona trae la hoja del protocolo en Word o en un archivo de texto, `protocolo.py leer-hoja <archivo>` la deja en `00_protocolo/hoja_extraida.txt` y el agente la pasa a `protocolo.md` punto por punto, sin agregar nada. Si la trae en papel o en PDF, la dicta o la copia. El agente le muestra a la persona la transcripción completa.
4. El agente puede preguntar para que un criterio se pueda verificar con título y resumen, para saber si lo que un criterio pone entre paréntesis es la lista completa de casos o son ejemplos, o para que un bloque de términos tenga sus sinónimos, pero no escribe por la persona ningún criterio, término ni decisión.
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
2. Para cada lote, el agente lee los criterios del protocolo y escribe `04_cribado/propuestas/lote_NNN.csv` con cuatro columnas: `id_ref`; `propuesta` (incluir, excluir o dudoso); `motivo`; y `fragmento`, las palabras del título o del resumen que sostienen la propuesta, copiadas del archivo del lote tal como están. Si hacen falta dos trozos, se separan con « … ».
3. El motivo es un solo criterio, copiado de los puntos 3 y 4 del protocolo sin el número de la lista. Para excluir, es el primer criterio de exclusión, en el orden del protocolo, que el título o el resumen muestran tal como está escrito. Para incluir, es «cumple todos los criterios de inclusión», y se propone incluir solo cuando el título y el resumen sostienen cada uno de esos criterios. Para dudoso, es el primer criterio de inclusión, en el orden del protocolo, que el título y el resumen no permiten dar por cumplido.
4. Casos difíciles. Un registro sin resumen va como dudoso, salvo que el título baste para excluirlo sin duda: que nombre lo que excluye un criterio, como una población, un concepto o un tipo de documento. Un título que no dice de qué trata el registro, como «Introducción» o «Presentación», no basta. El idioma y el tipo de documento se juzgan por el título y el resumen; los campos `idioma` y `tipo` de la base no sostienen una propuesta, porque el idioma a veces es el de la revista y el tipo no siempre distingue un estudio de una editorial o una reseña.
5. Reglas supuestas. Cuando un caso solo se resuelve con una lectura que el protocolo no hace explícita (leer como ejemplos lo que un criterio pone entre paréntesis, o decidir qué pasa con un estudio que menciona el concepto solo como una actividad entre varias), la propuesta es dudoso y el agente escribe esa lectura en `04_cribado/reglas_aplicadas.md`: el caso que el protocolo no resuelve, cómo lo leyó y los registros a los que se aplica. Al cerrar cada lote le muestra a la persona las reglas nuevas, y las del primer lote antes de empezar el segundo, porque ese lote sirve para probar los criterios.
6. La persona decide cada regla, y su decisión queda en `reglas_aplicadas.md` con la fecha. Desde entonces, los lotes siguientes aplican la regla como parte del criterio; mientras no la decida, los casos que cubre siguen yendo como dudoso. Los registros de los lotes anteriores no se vuelven a proponer: la persona los decide al firmar. Solo si ella cambia la redacción de un criterio, los lotes ya propuestos se proponen de nuevo, porque `cribado.py consolidar` compara cada motivo con el texto del protocolo. En ese caso el cambio se escribe en `protocolo.md` con sus palabras, se anota en `ESTADO.md` para declararlo en el método como un cambio al protocolo, y las propuestas anteriores se guardan en `04_cribado/propuestas/respaldos/`.
7. Si la herramienta permite subagentes, desde el segundo lote cada lote puede ir a uno, con las instrucciones de los pasos 2 a 5, la ruta del lote, la del protocolo, la de `reglas_aplicadas.md` y la del archivo de salida. Cada subagente devuelve en su respuesta las reglas nuevas que tuvo que suponer y no escribe en `reglas_aplicadas.md`; el agente principal las agrega y junta en una sola las que describen el mismo caso. Si no hay subagentes, se hace un lote a la vez, y el archivo se escribe antes de pasar al siguiente.
8. Si al leer un lote aparece un duplicado que la deduplicación no detectó (por ejemplo, el mismo estudio con el título traducido, o un preprint y su versión publicada), se anota en `03_deduplicacion/duplicados_vistos_en_cribado.csv` con los dos identificadores, y la persona decide. El agente anota los que ve en el lote que lee; no recorre los demás lotes buscándolos.
9. Después de cada lote se corre `cribado.py consolidar`, que arma `04_cribado/matriz_cribado.csv`. El programa compara cada motivo con los criterios del protocolo y cada fragmento con el título y el resumen del registro, y cuenta los dudosos por criterio. Una propuesta que no coincide no entra a la matriz y el programa dice por qué; el agente la corrige en el archivo del lote y vuelve a correr `consolidar`. Para retomar el cribado en otra sesión, `cribado.py pendientes` dice qué lotes no tienen propuesta.
10. Las columnas de las personas en la matriz (quién revisa, decisiones, motivo final, fecha de la firma y observaciones) quedan vacías y el agente no las llena. Si la persona dice de manera explícita que adopta las propuestas de un lote como su decisión, se corre `cribado.py adoptar --lote N --persona "Nombre"`, que copia las propuestas a sus columnas con la fecha y la observación «adoptó la propuesta del agente». Esas decisiones se declaran aparte en el método, y `flujo.py` las cuenta.

### Etapa 6. Extracción

1. `extraccion.py preparar` copia a `05_extraccion/texto_completo.csv` los candidatos con decisión final «incluir» o «dudoso» y el nombre de quien la firmó: los dos se leen a texto completo.
2. La persona consigue los textos completos (el agente puede señalar si hay copia en acceso abierto, pero no descarga de bases cerradas) y llena en ese archivo si consiguió cada texto y si el estudio se queda, con el motivo cuando sale.
3. Para cada estudio que la persona dejó a texto completo, `extraccion.py ficha R-NNNN` abre su ficha en `05_extraccion/fichas/`. El agente llena la zona descriptiva con el texto delante: diseño, contexto y población, qué se hizo, hallazgo principal con su página y limitaciones que el estudio declara. Lo que no está en el texto queda vacío y se dice. La zona interpretativa queda vacía.

### Etapa 7. Verificación de citas

`verificar_citas.py` comprueba cada referencia contra Crossref y OpenAlex, deja `06_verificacion/citas_verificadas.csv` con uno de cuatro estados (verificada, revisar, no encontrada o sin DOI) y actualiza la línea de verificación de cada ficha. Lo que no queda verificado no entra al manuscrito hasta que la persona lo resuelva; para una obra sin DOI, ella anota en la columna `comprobado_en` dónde la comprobó. La columna `referencia_borrador` trae la referencia en APA 7 como punto de partida; las mayúsculas del título, los editores de los capítulos y los autores se revisan a mano.

## Registro del proyecto

Al cerrar cada etapa, el agente agrega a `ESTADO.md`, en la raíz de la carpeta del proyecto, una entrada con el formato de `plantillas/ESTADO.md`: la fecha, la etapa, los archivos que quedaron, lo que decidió la persona y cuándo, y lo que queda en sus manos. En una etapa que dura varias sesiones, como el cribado, también agrega una entrada cada vez que la persona decide algo: las reglas de un lote, la adopción de un lote o un cambio en un criterio. El avance por lotes no necesita entrada, porque lo dice `cribado.py pendientes`. Así la sesión siguiente, en esta herramienta o en otra, sabe dónde va la revisión.

## Cómo se reporta

`referencias/prisma.md` relaciona cada etapa con los ítems de PRISMA 2020 y de PRISMA-ScR, y dice qué se declara sobre la asistencia automática: en qué etapas se usó, con qué herramienta y en qué fecha, qué decisiones quedaron en manos de personas y cuántos registros excluyó una persona y cuántos una herramienta. Con esta skill, la segunda cifra es cero, porque el agente no excluye nada por su cuenta.

## Piezas opcionales

Cada una vive en un archivo aparte y se puede quitar sin afectar el resto. Si el archivo no está, la etapa no se ofrece.

- `etapas_opcionales/validacion_cruzada.md`: comparación de la búsqueda automática con la búsqueda a mano en la interfaz de cada base.
- `etapas_opcionales/navegador.md`: búsquedas en bases que exigen navegador o acceso institucional, con la persona presente.
