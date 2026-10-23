# Revisión de literatura por etapas con un agente de IA

Esta carpeta es una skill: un conjunto de instrucciones y de programas que un agente de IA de los que trabajan sobre las carpetas del computador (Claude Code, Codex y otros) lee cuando se le pide una revisión de literatura. No es un programa que se abre y funciona solo. Le da al agente un procedimiento: llevar la revisión en siete etapas, dejar en archivos lo que sale de cada una y detenerse cada vez que hay una decisión que le corresponde a la persona que investiga.

La hoja del protocolo, en la que se escriben los nueve puntos antes de buscar, está en [Word](plantillas/hoja_protocolo.docx) y en [PDF](plantillas/hoja_protocolo.pdf).

## Lo que queda en la carpeta de la revisión

Cada revisión vive en su propia carpeta. Al terminar, esa carpeta tiene el protocolo de nueve puntos; las cadenas de búsqueda aprobadas; un archivo por cada búsqueda, con la cadena exacta, la fecha y el número de resultados; la lista única de candidatos con el registro de los duplicados; la matriz del cribado, donde la propuesta del agente está separada de la decisión de las personas; una ficha por estudio incluido; la verificación de cada cita contra Crossref y OpenAlex; y las cifras del diagrama de flujo de PRISMA, calculadas desde esos archivos. Cualquier número del informe se puede rastrear hasta el archivo que lo produjo.

## Qué decide la persona y qué hace el agente

| Decide la persona | Hace el agente |
|---|---|
| Los nueve puntos del protocolo, antes de cualquier búsqueda | Pasa el protocolo a la carpeta y pregunta lo que no se puede verificar |
| Si las cadenas de búsqueda corresponden al protocolo | Arma las cadenas desde el protocolo y las muestra antes de buscar |
| Si una búsqueda muy grande se acota o se amplía el tope | Cuenta los resultados de cada base y corre las búsquedas |
| Si dos registros parecidos son el mismo | Une los resultados y quita los duplicados seguros |
| La inclusión o exclusión de cada estudio | Propone incluir, excluir o dejar en duda, con el motivo y las palabras del resumen que lo sostienen |
| Qué estudios se quedan a texto completo | Abre las fichas y llena la parte descriptiva con la página de cada dato |
| La posición propia frente a cada estudio y la síntesis | Verifica las citas y cuenta las cifras del diagrama de flujo |

La skill tiene seis reglas que el agente no rompe aunque se le pida; están al principio de `SKILL.md`. La primera es que el agente propone y una persona firma.

## Qué se necesita

**Una herramienta que lea skills.** Comprobado el 18 de octubre de 2026 en la documentación oficial de cada una:

- Claude Code, de Anthropic. Requiere una cuenta Pro, Max, Team, Enterprise o de la consola de API; el plan gratuito no lo incluye. El plan Pro cuesta 20 dólares al mes, o 17 con pago anual, y el Max desde 100 dólares al mes.
- Codex, de OpenAI. Está incluido en los planes de ChatGPT Free, Go, Plus, Pro, Business, Edu y Enterprise, con más o menos uso según el plan (Plus cuesta 20 dólares al mes), y también se puede usar con una clave de API.
- Otras herramientas siguen el mismo formato abierto de skills (Agent Skills), entre ellas GitHub Copilot en VS Code, Cursor, OpenCode y Gemini CLI; esta última fue reemplazada por Antigravity CLI para las cuentas gratuitas y de Google One el 18 de junio de 2026, según su documentación. La lista completa está en agentskills.io.

**Python 3.9 o superior.** En macOS llega con las herramientas de línea de comandos de Apple, que el sistema ofrece instalar la primera vez que se escribe `python3` en la terminal; en Windows se instala desde python.org y el comando es `python` en lugar de `python3`; en Linux suele venir instalado. Los programas no necesitan bibliotecas adicionales.

**Saber abrir una terminal en una carpeta y pegar un comando.** En macOS se abre la aplicación Terminal, se escribe `cd` y un espacio, se arrastra la carpeta a la ventana y se oprime Enter. En Windows se abre la carpeta en el Explorador, se escribe `cmd` en la barra de la dirección y se oprime Enter. No hace falta saber programar: el agente escribe y corre los comandos, y la herramienta pide permiso antes de correrlos, según cómo esté configurada.

**Consumo.** Los modelos de lenguaje miden lo que leen y escriben en tokens, que son fragmentos de palabra, y los planes de pago limitan cuántos se usan en un periodo. En la prueba descrita al final, con una pregunta pequeña y 195 candidatos, el agente trabajó 37 minutos con el modelo Sonnet en Claude Code y la herramienta registró 582.489 tokens de uso. Ese tiempo incluye una pasada adicional sobre los excluidos que esta versión no trae, y cuyo consumo se midió aparte. Las bases abiertas recibieron 51 consultas y OpenAlex descontó 20 créditos de los 1000 que da al día sin clave. Se estima que el consumo del cribado crece con el número de candidatos. No se midió qué parte del cupo de cada plan representa ese consumo.

**Dos datos opcionales.** Un correo de contacto en la variable de entorno `REVISION_CORREO`, que las bases piden por cortesía, y la clave gratuita de OpenAlex en `OPENALEX_API_KEY`: sin clave, OpenAlex da un cupo diario que alcanza para un centenar de páginas de resultados; con la clave gratuita, el cupo es diez veces mayor (página de OpenAlex sobre límites de uso, consultada el 18 de octubre de 2026). Una variable de entorno se define en la terminal antes de abrir la herramienta: en macOS y Linux con `export REVISION_CORREO="nombre@universidad.edu.co"`, y en la PowerShell de Windows con `$env:REVISION_CORREO="nombre@universidad.edu.co"`. Vale mientras esa ventana esté abierta.

## Cómo se instala

Se descarga la carpeta desde la página del repositorio, https://github.com/danielquirozv-sudo/revision-de-literatura, con el botón Code y la opción Download ZIP. Al descomprimir, la carpeta llega con el nombre `revision-de-literatura-main` y se le cambia a `revision-de-literatura`, porque el nombre de la carpeta tiene que coincidir con el de la skill. Después se copia en el lugar donde la herramienta busca las skills. Las rutas son las de la documentación oficial al 18 de octubre de 2026:

| Herramienta | Para todas las revisiones del computador | Solo para una carpeta |
|---|---|---|
| Claude Code | `~/.claude/skills/revision-de-literatura/` | `.claude/skills/revision-de-literatura/` dentro de la carpeta |
| Codex | `~/.agents/skills/revision-de-literatura/` | `.agents/skills/revision-de-literatura/` dentro de la carpeta |
| Gemini CLI | `~/.gemini/skills/` o `~/.agents/skills/` | `.gemini/skills/` o `.agents/skills/` |
| GitHub Copilot en VS Code | `~/.copilot/skills/`, `~/.claude/skills/` o `~/.agents/skills/` | `.github/skills/`, `.claude/skills/` o `.agents/skills/` |

El símbolo `~` es la carpeta personal del usuario: en macOS, la que el Finder muestra con el ícono de una casa; en Windows, `C:\Users\<usuario>`. Las carpetas que empiezan por punto están ocultas: en el Finder de macOS se muestran con Comando, Mayúsculas y punto; en el Explorador de Windows, con Vista, Mostrar y Elementos ocultos.

Para comprobar que quedó instalada: en Claude Code se escribe `/revision-de-literatura`; en Codex, `/skills` o `$revision-de-literatura`. Si no aparece, se cierra la herramienta y se vuelve a abrir.

Documentación consultada: code.claude.com/docs/en/skills, learn.chatgpt.com/docs/build-skills, geminicli.com/docs/cli/skills, code.visualstudio.com/docs/copilot/customization/agent-skills y agentskills.io/specification.

## Cómo se empieza

1. Se crea una carpeta vacía para la revisión, se abre una terminal en ella y se abre la herramienta (`claude` en Claude Code, `codex` en Codex).
2. Se le pide al agente: «Quiero hacer una revisión de literatura con la skill revision-de-literatura».
3. El agente crea la plantilla del protocolo y la persona la llena. Si la persona trae diligenciada la hoja del protocolo en Word (`plantillas/hoja_protocolo.docx`), el agente la lee y la pasa a la carpeta; si la trae en papel o en PDF, la dicta o la copia. La persona confirma que el protocolo dice lo que ella decidió; el agente anota la fecha de esa confirmación y sin ella no busca nada.
4. Desde ahí, el agente avanza etapa por etapa y se detiene en cada decisión. Al cerrar cada etapa anota en `ESTADO.md` lo que quedó hecho y lo que falta, de modo que la revisión se puede retomar otro día o en otra herramienta.
5. Las tablas quedan en archivos CSV, que se abren con cualquier hoja de cálculo. Si la persona edita una en Excel, la guarda con el formato «CSV UTF-8 (delimitado por comas)», para que las tildes lleguen bien a los programas.

Cada búsqueda tarda segundos o minutos. Escribir el protocolo, firmar el cribado y leer a texto completo toman días.

## Cómo se declara el uso de IA en el manuscrito

En el apartado de método se dice qué etapas usaron un agente de IA, con qué herramienta y modelo y en qué fechas; qué hizo el agente y qué decidieron las personas, incluidas las decisiones que una persona tomó adoptando en bloque las propuestas del agente; si se calibró el cribado y con qué acuerdo; cómo se verificaron las referencias; y dónde están los archivos que permiten repetir la búsqueda. PRISMA 2020 pide, además, que el diagrama de flujo diga cuántos registros excluyó una persona y cuántos una herramienta; con esta skill la segunda cifra es cero, porque el agente propone y no descarta. Un ejemplo de redacción:

> La identificación, la deduplicación, la extracción descriptiva de los estudios y la verificación de referencias se hicieron con un agente de IA ([herramienta y modelo], [fechas]) que siguió un procedimiento por etapas con registro en archivos. El agente propuso una decisión de cribado para cada registro, con el criterio y el fragmento del resumen que la sostenían; las decisiones de inclusión y exclusión las tomaron [las autoras y los autores], que en [número] casos adoptaron en bloque la propuesta del agente. El agente llenó la parte descriptiva de cada ficha con el texto completo delante, con la página de cada dato. Las referencias se verificaron contra Crossref y OpenAlex por su DOI; las que no tenían DOI se comprobaron en su fuente.

La relación de cada etapa con los ítems de PRISMA 2020 y de PRISMA-ScR está en `referencias/prisma.md`. Cada revista tiene además su propia política sobre el uso de IA, que se consulta antes de enviar.

## Piezas opcionales

Están en `etapas_opcionales/` y se pueden quitar sin que el resto deje de funcionar:

- La validación cruzada entre la búsqueda automática y la búsqueda a mano.
- Las búsquedas en bases que exigen navegador o acceso institucional, con la persona presente.

## Prueba

El 18 y el 19 de octubre de 2026 un agente de IA que la leía por primera vez la corrió de principio a fin en Claude Code, con el modelo Sonnet, sobre una pregunta de ensayo: qué se publicó en 2024 y 2025 sobre la retroalimentación entre pares en la formación inicial de profesores. Las decisiones de la persona venían escritas de antemano y solo se consultaron OpenAlex, ERIC, DOAJ y Crossref.

| Etapa | Tiempo | Lo que quedó |
|---|---|---|
| Lectura de la skill y protocolo | 3 min | protocolo transcrito y confirmado |
| Búsqueda | 5 min | 4 crudos, 233 registros |
| Normalización y deduplicación | 3 min | 38 duplicados, 195 candidatos |
| Cribado, con una pasada adicional que esta versión no trae | 22 min | 67 propuestas de incluir, 70 de excluir y 58 dudosas; un lote firmado |
| Extracción | 1 min | 10 estudios a texto completo, ninguno conseguido; 2 fichas abiertas solo con el resumen |
| Verificación de citas y cifras de PRISMA | 3 min | 8 citas verificadas y 2 sin DOI |

Las dos fichas se abrieron con el resumen porque la prueba no descargó textos completos; la versión actual ya no abre una ficha sin la decisión de la persona a texto completo. La skill cambió durante la prueba: la etapa del protocolo usó una plantilla anterior, sin los campos que hoy comparte con la hoja del protocolo.

La prueba encontró fallas que se corrigieron después: un respaldo que el cribado leía como si fuera una propuesta, candidatos que perdían el DOI al deduplicar, Crossref corrido con una sola combinación de términos, registros fuera de la ventana que se descartaban sin guardarse y tablas que se reescribían sin respaldo. Las correcciones se comprobaron con una corrida de regresión en una carpeta aparte, no con una segunda prueba completa.

No se probó en Codex ni en otra herramienta distinta de Claude Code, ni en Windows. Tampoco se ejercitaron la clave de OpenAlex, el correo de contacto, la respuesta a un límite de consultas de una base, las bases que exigen navegador, la validación cruzada, el cribado repartido entre subagentes (agentes que el agente principal lanza para una tarea aparte) o entre dos personas, la lectura a texto completo con páginas ni la reanudación de la revisión en otra sesión. La lectura de la hoja del protocolo en Word se comprobó aparte.

## Autoría y licencia

Daniel Andrés Quiroz-Vallejo y Jaime Andrés Carmona-Mesa, Facultad de Educación, Universidad de Antioquia.

Esta obra está bajo una licencia Creative Commons Atribución-NoComercial-CompartirIgual 4.0 Internacional (CC BY-NC-SA 4.0): https://creativecommons.org/licenses/by-nc-sa/4.0/deed.es
