# -*- coding: utf-8 -*-
"""Funciones compartidas por los programas de la skill revision-de-literatura.

Solo usa la biblioteca estándar de Python 3.9 o superior, sin bibliotecas
adicionales. Todas las rutas son relativas a la carpeta del proyecto de revisión, que
se indica con --carpeta (por omisión, la carpeta desde donde se corre).
"""

import csv
import html
import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

CAMPOS_REGISTRO = ["titulo", "autores", "anio", "fuente", "idioma", "tipo",
                   "doi", "url", "resumen"]

PAUSA = 1.0       # segundos entre llamadas a una API
REINTENTOS = 3

# Carpetas del proyecto, en el orden de las etapas.
CARPETAS = {
    "protocolo": "00_protocolo",
    "busqueda": "01_busqueda",
    "crudos": "01_busqueda/crudos",
    "normalizacion": "02_normalizacion",
    "deduplicacion": "03_deduplicacion",
    "cribado": "04_cribado",
    "extraccion": "05_extraccion",
    "verificacion": "06_verificacion",
}


SKILL = Path(__file__).resolve().parent.parent


def carpeta(proyecto, clave, crear=True):
    raiz = Path(proyecto).resolve()
    if raiz == SKILL or SKILL in raiz.parents:
        raise SystemExit("La carpeta del proyecto no puede estar dentro de la skill. "
                         "Se indica con --carpeta la carpeta de la revisión.")
    p = Path(proyecto) / CARPETAS[clave]
    if crear:
        p.mkdir(parents=True, exist_ok=True)
    return p


def ahora():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def hoy():
    return datetime.now().date().isoformat()


def contacto():
    """Correo de contacto opcional para las API (variable REVISION_CORREO)."""
    return os.environ.get("REVISION_CORREO", "").strip()


def agente_http():
    c = contacto()
    base = "revision-de-literatura/1.0 (skill de revision de literatura"
    return base + ("; mailto:{})".format(c) if c else ")")


class Respuesta:
    def __init__(self, datos, cabeceras):
        self.datos = datos
        self.cabeceras = cabeceras


def get_json(url, params=None, pausa=PAUSA, timeout=60):
    """GET con reintentos. Devuelve Respuesta o None si la fuente no responde."""
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    ultimo = None
    for intento in range(1, REINTENTOS + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": agente_http(), "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                datos = json.loads(r.read().decode("utf-8"))
                cab = {k.lower(): v for k, v in r.headers.items()}
            time.sleep(pausa)
            return Respuesta(datos, cab)
        except urllib.error.HTTPError as e:
            ultimo = "HTTP {}".format(e.code)
            if e.code == 429:
                espera = 15 * intento
                print("  La fuente pide esperar (429). Espera de {} s.".format(espera))
                time.sleep(espera)
                continue
            if e.code in (400, 401, 403, 404):
                break
            time.sleep(3 * intento)
        except Exception as e:  # red caída, tiempo agotado, JSON dañado
            ultimo = str(e)
            time.sleep(3 * intento)
    print("  ERROR tras {} intentos: {} ({})".format(REINTENTOS, url[:120], ultimo))
    return None


def limpiar(texto):
    """Decodifica entidades HTML, quita espacios repetidos y cambia las rayas
    largas y medias por guion."""
    if texto is None:
        return ""
    t = " ".join(html.unescape(str(texto)).split())
    return t.replace("\u2014", "-").replace("\u2013", "-")


def normalizar_doi(doi):
    d = (doi or "").strip().lower()
    for prefijo in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/",
                    "http://dx.doi.org/", "doi:"):
        if d.startswith(prefijo):
            d = d[len(prefijo):]
    return d.strip()


def normalizar_texto(texto):
    """Minúsculas, sin tildes ni puntuación: clave para comparar títulos."""
    t = unicodedata.normalize("NFKD", str(texto or ""))
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = "".join(c if c.isalnum() or c.isspace() else " " for c in t.lower())
    return " ".join(t.split())


# Comillas y guiones tipográficos que una copia puede cambiar sin cambiar las palabras.
TIPOGRAFIA = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"', "″": '"',
    "«": '"', "»": '"', "‐": "-", "‑": "-", "‒": "-",
    "–": "-", "—": "-", "―": "-", "−": "-", "­": None})


def para_comparar(texto):
    """Minúsculas y espacios simples, con las comillas y los guiones tipográficos
    cambiados por los del teclado. Conserva las tildes y las palabras: sirve para
    comprobar que una cita está tal cual en otro texto."""
    t = unicodedata.normalize("NFKC", str(texto or "")).translate(TIPOGRAFIA)
    return " ".join(t.split()).casefold()


def clave_motivo(texto):
    """Clave para comparar un motivo con un criterio del protocolo: sin el número
    de la lista ni el punto final, y con para_comparar."""
    t = re.sub(r"^\d+\s*[.)-]?\s*", "", para_comparar(texto))
    return t.rstrip(" .")


def anio_entero(valor):
    try:
        return int(str(valor).strip()[:4])
    except (TypeError, ValueError):
        return None


def registro(titulo="", autores="", anio=None, fuente="", idioma="", tipo="",
             doi="", url="", resumen=""):
    return {"titulo": limpiar(titulo), "autores": limpiar(autores),
            "anio": anio_entero(anio), "fuente": limpiar(fuente),
            "idioma": limpiar(idioma), "tipo": limpiar(tipo),
            "doi": normalizar_doi(doi), "url": (url or "").strip(),
            "resumen": limpiar(resumen)}


def guardar_json_nuevo(destino, contenido):
    """Escribe un JSON sin sobrescribir nunca: si existe, agrega _v2, _v3..."""
    destino = Path(destino)
    final = destino
    n = 2
    while final.exists():
        final = destino.with_name("{}_v{}{}".format(destino.stem, n, destino.suffix))
        n += 1
    with open(final, "w", encoding="utf-8") as f:
        json.dump(contenido, f, ensure_ascii=False, indent=1)
    return final


def respaldar(ruta):
    """Copia un archivo antes de reescribirlo. La copia va a la subcarpeta
    respaldos/ de la misma carpeta, con la fecha y la hora hasta el microsegundo,
    para que ningún programa la lea como si fuera el archivo vigente."""
    ruta = Path(ruta)
    if not ruta.exists():
        return None
    destino = ruta.parent / "respaldos"
    destino.mkdir(exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    copia = destino / "{}.{}{}".format(ruta.stem, marca, ruta.suffix)
    copia.write_bytes(ruta.read_bytes())
    return copia


def leer_csv(ruta):
    """Lee un CSV con coma o con punto y coma (Excel en español guarda con ;)."""
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        primera = f.readline()
        f.seek(0)
        sep = ";" if primera.count(";") > primera.count(",") else ","
        return list(csv.DictReader(f, delimiter=sep))


def escribir_csv(ruta, filas, campos):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        for fila in filas:
            w.writerow(fila)
    print("  {} ({} filas)".format(ruta, len(filas)))


def agregar_fila_csv(ruta, fila, campos):
    """Agrega una fila al final de un CSV; crea el encabezado si no existe."""
    ruta = Path(ruta)
    nuevo = not ruta.exists()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "a", encoding="utf-8-sig" if nuevo else "utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        if nuevo:
            w.writeheader()
        w.writerow(fila)
