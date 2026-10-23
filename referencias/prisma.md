# Etapas frente a PRISMA 2020 y PRISMA-ScR

PRISMA 2020 (Page, McKenzie, et al., 2021) es la guía para reportar revisiones sistemáticas, y su documento de explicación (Page, Moher, et al., 2021) desarrolla cada ítem. PRISMA-ScR (Tricco et al., 2018) es la extensión de PRISMA para revisiones de alcance, publicada en 2018 sobre la declaración original. Ninguna de las dos dice cómo hacer la revisión: dicen qué se reporta. La tabla muestra qué ítem toca cada etapa de esta skill y qué archivo de la carpeta sirve para reportarlo. Los ítems de PRISMA 2020 van con su número; los de PRISMA-ScR, por su nombre.

| Etapa | PRISMA 2020 | PRISMA-ScR | Archivo que lo sostiene |
|---|---|---|---|
| Protocolo | 5, criterios de elegibilidad; 24a a 24c, registro y protocolo, con los cambios que se le hicieron | Protocolo y registro; criterios de elegibilidad; objetivos | `00_protocolo/protocolo.md` y la fecha de confirmación en `ESTADO.md` |
| Búsqueda | 6, fuentes de información, con la fecha de la última consulta; 7, estrategia de búsqueda completa de cada base, con filtros y límites | Fuentes de información, con la fecha de la búsqueda más reciente; búsqueda, con la estrategia completa de al menos una base, de modo que se pueda repetir | `00_protocolo/cadenas.json`, los crudos con su cadena exacta y `01_busqueda/registro_corridas.csv` |
| Normalización y deduplicación | 16a, resultados de la búsqueda: registros identificados y excluidos antes del cribado, como los duplicados | Selección de las fuentes de evidencia, en los resultados, idealmente con diagrama de flujo | `03_deduplicacion/conteo.json` y `flujo_prisma.md` |
| Cribado por título y resumen | 8, proceso de selección: cuántas personas cribaron cada registro, si trabajaron por separado y, si aplica, cómo se usaron herramientas automáticas; 16a, cuántos excluyó una persona y cuántos una herramienta | Selección de las fuentes de evidencia, en los métodos: cribado y elegibilidad | `04_cribado/matriz_cribado.csv`, con la propuesta del agente separada de la firma de las personas, y la calibración si se hizo |
| Extracción | 9, proceso de recolección de datos, incluidas las herramientas automáticas; 10, datos que se buscaron | Proceso de extracción de datos (charting): formularios probados, si se hizo por separado o por duplicado; datos extraídos | `05_extraccion/fichas/` y `05_extraccion/texto_completo.csv` |
| Verificación de citas | 27, disponibilidad de datos, código y otros materiales, junto con el resto de la carpeta | Sin ítem propio | `06_verificacion/citas_verificadas.csv` |

Lo que esta skill no cubre queda en manos de las personas: la evaluación del riesgo de sesgo y la certeza de la evidencia de PRISMA 2020, la valoración crítica que PRISMA-ScR deja como opcional, y la síntesis.

## Asistencia automática en el reporte

PRISMA 2020 pide declarar, en el proceso de selección, si se usaron herramientas automáticas y cómo. Su documento de explicación agrega dos precisiones: los registros que una herramienta descarta antes del cribado se reportan en el diagrama de flujo en una casilla propia, «Records marked as ineligible by automation tools», y el diagrama debe indicar cuántos registros excluyó una persona y cuántos una herramienta (Page, Moher, et al., 2021). Con esta skill la casilla de la herramienta queda en cero, porque el agente propone y no descarta, y `flujo.py` separa las propuestas del agente de las decisiones firmadas. Cuando una persona adopta en bloque las propuestas de un lote, la decisión es suya, pero se declara: `flujo.py` cuenta cuántas decisiones se tomaron así. Los registros que una base entrega con un año fuera de la ventana se cuentan entre los identificados y como eliminados antes del cribado por otras razones; quedan guardados en el crudo de su corrida.

En el apartado de método se declara, como mínimo: qué etapas usaron un agente de IA, con qué herramienta y modelo y en qué fechas; qué decidió el agente y qué decidieron las personas; si se calibró el cribado y con qué acuerdo; cómo se verificaron las referencias; y dónde están los archivos que permiten repetir la búsqueda. Cada revista fija además su propia política sobre el uso de IA, y esa política se consulta antes de enviar.

## Referencias

Page, M. J., McKenzie, J. E., Bossuyt, P. M., Boutron, I., Hoffmann, T. C., Mulrow, C. D., Shamseer, L., Tetzlaff, J. M., Akl, E. A., Brennan, S. E., Chou, R., Glanville, J., Grimshaw, J. M., Hróbjartsson, A., Lalu, M. M., Li, T., Loder, E. W., Mayo-Wilson, E., McDonald, S., ... Moher, D. (2021). The PRISMA 2020 statement: An updated guideline for reporting systematic reviews. *BMJ*, *372*, Artículo n71. https://doi.org/10.1136/bmj.n71

Page, M. J., Moher, D., Bossuyt, P. M., Boutron, I., Hoffmann, T. C., Mulrow, C. D., Shamseer, L., Tetzlaff, J. M., Akl, E. A., Brennan, S. E., Chou, R., Glanville, J., Grimshaw, J. M., Hróbjartsson, A., Lalu, M. M., Li, T., Loder, E. W., Mayo-Wilson, E., McDonald, S., ... McKenzie, J. E. (2021). PRISMA 2020 explanation and elaboration: Updated guidance and exemplars for reporting systematic reviews. *BMJ*, *372*, Artículo n160. https://doi.org/10.1136/bmj.n160

Tricco, A. C., Lillie, E., Zarin, W., O'Brien, K. K., Colquhoun, H., Levac, D., Moher, D., Peters, M. D. J., Horsley, T., Weeks, L., Hempel, S., Akl, E. A., Chang, C., McGowan, J., Stewart, L., Hartling, L., Aldcroft, A., Wilson, M. G., Garritty, C., ... Straus, S. E. (2018). PRISMA Extension for Scoping Reviews (PRISMA-ScR): Checklist and explanation. *Annals of Internal Medicine*, *169*(7), 467-473. https://doi.org/10.7326/M18-0850
