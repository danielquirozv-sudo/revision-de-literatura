# -*- coding: utf-8 -*-
"""Comprueba cada referencia contra Crossref y OpenAlex.

Por omisión toma los estudios de 05_extraccion/texto_completo.csv. También
recibe cualquier CSV con columnas doi y titulo (y, si las tiene, id_ref y anio),
o un DOI suelto. Si un estudio tiene ficha, actualiza su línea «Verificación de
la cita»; cuando la línea cambia, antes deja un respaldo de la ficha en
05_extraccion/fichas/respaldos/.

Estados posibles:
  verificada        el DOI existe en Crossref u OpenAlex y título y año coinciden
  revisar           el DOI existe, pero el título o el año no coinciden, o algún
                    autor no tiene forma de nombre de persona
  no encontrada     ninguna de las dos fuentes reconoce el DOI
  sin DOI           el registro no trae DOI; se deja una sugerencia por confirmar

Lo que no queda «verificada» no entra al manuscrito hasta que una persona lo
resuelva. Para un registro sin DOI, la persona anota en la columna
comprobado_en dónde comprobó la referencia (por ejemplo, la página del
repositorio) o acepta la sugerencia después de abrirla.

Uso (<skill> es la carpeta de esta skill y <proyecto> la de la revisión):
  python3 <skill>/scripts/verificar_citas.py --carpeta <proyecto>
  python3 <skill>/scripts/verificar_citas.py --carpeta <proyecto> --archivo mis_referencias.csv
  python3 <skill>/scripts/verificar_citas.py --doi 10.1136/bmj.n71
"""

import argparse
import re
import sys
import urllib.parse
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import (ahora, anio_entero, carpeta, contacto, escribir_csv,  # noqa: E402
                   get_json, leer_csv, limpiar, normalizar_doi, normalizar_texto,
                   respaldar)

CAMPOS = ["id_ref", "doi", "titulo_registro", "anio_registro", "titulo_crossref",
          "anio_crossref", "revista_crossref", "titulo_openalex", "anio_openalex",
          "estado", "nota", "comprobado_en", "referencia_borrador", "verificado_el"]


class Consumo:
    llamadas = 0
    creditos_openalex = 0


def _get(url, params=None):
    r = get_json(url, params)
    Consumo.llamadas += 1
    if r and "openalex" in url:
        try:
            Consumo.creditos_openalex += int(r.cabeceras.get("x-ratelimit-credits-used", 0))
        except ValueError:
            pass
    return r


def _params():
    return {"mailto": contacto()} if contacto() else None


def crossref(doi):
    r = _get("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/"),
             _params())
    return (r.datos.get("message") if r else None) or None


def openalex(doi):
    r = _get("https://api.openalex.org/works/https://doi.org/" + doi, _params())
    return r.datos if r else None


def anio_crossref(m):
    for clave in ("issued", "published-online", "published-print"):
        partes = ((m.get(clave) or {}).get("date-parts") or [[None]])[0]
        if partes and partes[0]:
            return partes[0]
    return None


def autor_raro(a):
    """Un autor sin nombre de pila o con palabras de cargo o institución."""
    familia = a.get("family") or a.get("name") or ""
    return (not a.get("given") or len(familia.split()) > 4 or
            bool(re.search(r"\d|Dept|Department|University|Universidad|Professor|"
                           r"Profesor|Faculty|Facultad", familia)))


def autores_apa(lista):
    nombres = []
    for a in lista:
        familia = limpiar(a.get("family") or a.get("name") or "")
        iniciales = " ".join(p[0] + "." for p in limpiar(a.get("given") or "").replace(
            "-", " ").split() if p)
        nombres.append("{}, {}".format(familia, iniciales).strip(", "))
    if not nombres:
        return ""
    if len(nombres) == 1:
        return nombres[0]
    if len(nombres) <= 20:
        return ", ".join(nombres[:-1]) + " y " + nombres[-1]
    return ", ".join(nombres[:19]) + ", ... " + nombres[-1]


def _cerrar(texto):
    texto = texto.strip()
    return texto if texto.endswith((".", "?", "!")) else texto + "."


def referencia(m, doi):
    """Borrador en APA 7. Las mayúsculas del título y los editores se revisan a mano."""
    titulo = limpiar("; ".join(m.get("title") or []))
    contenedor = limpiar("; ".join(m.get("container-title") or []))
    partes = [autores_apa(m.get("author") or []),
              "({}).".format(anio_crossref(m) or "s. f."), _cerrar(titulo)]
    if m.get("type") in ("book-chapter", "book-part", "book-section"):
        detalle = "En " + contenedor if contenedor else "En [libro]"
        if m.get("page"):
            detalle += " (pp. {})".format(m["page"])
        partes.append(_cerrar(detalle))
        if m.get("publisher"):
            partes.append(_cerrar(limpiar(m["publisher"])))
    else:
        detalle = contenedor
        if m.get("volume"):
            detalle += ", {}".format(m["volume"]) + (
                "({})".format(m["issue"]) if m.get("issue") else "")
        pag = m.get("page") or m.get("article-number")
        if pag:
            detalle += ", {}".format(pag)
        if detalle:
            partes.append(_cerrar(detalle))
    partes.append("https://doi.org/" + doi)
    return " ".join(p for p in partes if p)


def sugerir_doi(titulo):
    p = {"query.bibliographic": titulo, "rows": 1}
    if contacto():
        p["mailto"] = contacto()
    r = _get("https://api.crossref.org/works", p)
    items = ((r.datos.get("message") or {}).get("items") if r else None) or []
    if not items:
        return ""
    it = items[0]
    t = limpiar("; ".join(it.get("title") or []))
    sim = SequenceMatcher(None, normalizar_texto(titulo), normalizar_texto(t)).ratio()
    return "{} (similitud del título {:.2f})".format(it.get("DOI"), sim)


def verificar(fila):
    doi = normalizar_doi(fila.get("doi"))
    titulo = fila.get("titulo") or ""
    anio = anio_entero(fila.get("anio"))
    out = {"id_ref": fila.get("id_ref", ""), "doi": doi, "titulo_registro": titulo,
           "anio_registro": anio or "", "comprobado_en": "", "verificado_el": ahora()}
    if not doi:
        out["estado"] = "sin DOI"
        sugerencia = sugerir_doi(titulo) if titulo else ""
        out["nota"] = ("El registro no trae DOI. Sugerencia de Crossref, que solo se "
                       "acepta después de abrirla: {}. Si la obra no tiene DOI, la "
                       "persona anota en comprobado_en dónde la comprobó.".format(
                           sugerencia or "ninguna"))
        return out
    cr, oa = crossref(doi), openalex(doi)
    if cr:
        out.update({"titulo_crossref": limpiar("; ".join(cr.get("title") or [])),
                    "anio_crossref": anio_crossref(cr) or "",
                    "revista_crossref": limpiar("; ".join(cr.get("container-title") or [])),
                    "referencia_borrador": referencia(cr, doi)})
    if oa:
        out.update({"titulo_openalex": oa.get("display_name") or "",
                    "anio_openalex": oa.get("publication_year") or ""})
    if not cr and not oa:
        out["estado"] = "no encontrada"
        out["nota"] = "Ni Crossref ni OpenAlex reconocen el DOI."
        return out
    titulo_fuente = out.get("titulo_crossref") or out.get("titulo_openalex") or ""
    anios = {a for a in (out.get("anio_crossref"), out.get("anio_openalex")) if a}
    sim = SequenceMatcher(None, normalizar_texto(titulo),
                          normalizar_texto(titulo_fuente)).ratio() if titulo else 1.0
    anio_ok = anio is None or not anios or any(abs(int(a) - anio) <= 1 for a in anios)
    raros = [a for a in (cr or {}).get("author") or [] if autor_raro(a)]
    if sim >= 0.9 and anio_ok and not raros:
        out["estado"] = "verificada"
        fuentes = [n for n, x in (("Crossref", cr), ("OpenAlex", oa)) if x]
        out["nota"] = "Coincide en " + " y ".join(fuentes) + "."
    else:
        out["estado"] = "revisar"
        notas = []
        if sim < 0.9 or not anio_ok:
            notas.append("Similitud del título {:.2f}; años en las fuentes: {}.".format(
                sim, ", ".join(str(a) for a in sorted(anios)) or "sin dato"))
        if raros:
            notas.append("Crossref trae un autor que no parece nombre de persona: {}.".format(
                "; ".join(limpiar(a.get("family") or a.get("name") or "") for a in raros)))
        out["nota"] = " ".join(notas)
    return out


def actualizar_fichas(proyecto, filas):
    fichas = carpeta(proyecto, "extraccion", crear=False) / "fichas"
    n = 0
    for f in filas:
        ruta = fichas / "{}.md".format(f.get("id_ref"))
        if not f.get("id_ref") or not ruta.exists():
            continue
        texto = ruta.read_text(encoding="utf-8")
        nueva = "Verificación de la cita: {} el {} ({})".format(
            f["estado"], f["verificado_el"][:10], f.get("nota", ""))
        # Con una función, re.sub no interpreta las barras invertidas de la nota.
        texto2 = re.sub(r"^Verificación de la cita:.*$", lambda m: nueva, texto,
                        count=1, flags=re.M)
        if texto2 != texto:
            respaldar(ruta)
            ruta.write_text(texto2, encoding="utf-8")
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carpeta", default=".", help="carpeta del proyecto")
    ap.add_argument("--archivo", help="CSV con columnas doi y titulo")
    ap.add_argument("--doi", help="un DOI suelto")
    a = ap.parse_args()

    if a.doi:
        fila = verificar({"doi": a.doi})
        for k in CAMPOS:
            if fila.get(k):
                print("{}: {}".format(k, fila[k]))
        return
    origen = Path(a.archivo) if a.archivo else \
        carpeta(a.carpeta, "extraccion") / "texto_completo.csv"
    if not origen.exists():
        sys.exit("No existe {}. Se corre extraccion.py preparar o se da --archivo."
                 .format(origen))
    filas = [verificar(f) for f in leer_csv(origen)]
    destino = carpeta(a.carpeta, "verificacion") / "citas_verificadas.csv"
    if destino.exists():                     # lo que escribió la persona no se pierde
        respaldar(destino)
        previas = {(f.get("id_ref") or "", f.get("doi") or ""): f for f in leer_csv(destino)}
        for f in filas:
            anterior = previas.get((f.get("id_ref") or "", f.get("doi") or ""))
            if anterior and (anterior.get("comprobado_en") or "").strip():
                f["comprobado_en"] = anterior["comprobado_en"]
    escribir_csv(destino, filas, CAMPOS)
    resumen = {}
    for f in filas:
        resumen[f["estado"]] = resumen.get(f["estado"], 0) + 1
    n = actualizar_fichas(a.carpeta, filas)
    print("Resultado: {}. Fichas actualizadas: {}.".format(resumen, n))
    print("Consumo: {} {} a las fuentes; {} créditos de OpenAlex.".format(
        Consumo.llamadas, "consulta" if Consumo.llamadas == 1 else "consultas",
        Consumo.creditos_openalex))


if __name__ == "__main__":
    main()
