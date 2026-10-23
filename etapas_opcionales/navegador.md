# Bases que exigen navegador o acceso institucional

Pieza opcional. Scopus, Web of Science, SciELO, Redalyc y Google Scholar no se consultan con los programas de esta skill: unas piden acceso institucional y otras prohíben en sus condiciones de uso la extracción automática.

1. La persona entra a la base con su propio acceso. El agente no inicia sesión, no escribe contraseñas y no resuelve CAPTCHA.
2. El agente imprime la cadena con `cadenas.py mostrar`. Si la base tiene otra sintaxis (por ejemplo `TITLE-ABS-KEY` en Scopus o `TS=` en Web of Science), el agente propone la adaptación, la persona la aprueba y la adaptación se agrega a `cadenas.json` con una nota.
3. Si la base permite exportar los resultados, la persona los exporta en RIS o en CSV y guarda el archivo en `01_busqueda/exportados/`. El agente lo convierte a un crudo con la misma estructura de los demás (`meta` con la base, la ecuación, la cadena exacta, la ventana de años, la fecha, el total reportado y el número de registros, y `registros` con los nueve campos) y lo guarda en `01_busqueda/crudos/` con el nombre `base_ecuacion_fecha.json`. Si la base entregó registros con un año fuera de la ventana, pueden quedar en `registros`: `normalizar.py` los separa en `02_normalizacion/fuera_de_ventana.csv` y `flujo.py` los cuenta.
4. Si la base no permite exportar, se trabaja con la persona presente: el agente lee las páginas de resultados que ella abre y escribe el crudo; si aparece un CAPTCHA o una pantalla de acceso, se detiene y le avisa.
5. La corrida se anota en `01_busqueda/registro_corridas.csv` como cualquier otra.
