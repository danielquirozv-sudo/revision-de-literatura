# -*- coding: utf-8 -*-
"""Corre una búsqueda contra una base abierta y guarda el crudo.

No corre si el protocolo no tiene sus nueve puntos o si la persona no ha
aprobado las cadenas. Cada corrida deja un JSON nuevo en 01_busqueda/crudos/
(nunca sobrescribe) y una fila en 01_busqueda/registro_corridas.csv.

Uso (<skill> es la carpeta de esta skill y <proyecto> la de la revisión):
  python3 <skill>/scripts/buscar.py --carpeta <proyecto> --base openalex --ecuacion E1 --desde 2015 --hasta 2026
  python3 <skill>/scripts/buscar.py --carpeta <proyecto> --base eric --ecuacion E1 --desde 2015 --hasta 2026 --solo-mostrar
  python3 <skill>/scripts/buscar.py --carpeta <proyecto> --base openalex --ecuacion E1 --desde 2015 --hasta 2026 --solo-contar
  python3 <skill>/scripts/buscar.py --carpeta <proyecto> --base todas --desde 2015 --hasta 2026 --solo-contar

Crossref no admite operadores: no da un total para la ecuación, solo lo que
devuelve cada combinación de términos por relevancia. Por eso su corrida
siempre lleva un tope (--max) que decide la persona.

Los registros que la fuente entrega fuera de la ventana de años no se borran:
quedan en el crudo, en la lista «fuera_de_ventana», y no pasan a las etapas
siguientes.

Opciones de consumo: --max (tope de registros por corrida, 2000 por omisión).
OpenAlex: sin clave admite unas cien páginas de búsqueda al día; con la
variable OPENALEX_API_KEY el cupo es mayor.
"""

import argparse
import os
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cadenas  # noqa: E402
import protocolo  # noqa: E402
from comun import (agregar_fila_csv, ahora, carpeta, contacto, get_json,  # noqa: E402
                   guardar_json_nuevo, hoy, registro)

CAMPOS_REGISTRO_CORRIDAS = ["fecha_busqueda", "base", "ecuacion", "archivo",
                            "cadena_exacta", "filtros", "total_reportado",
                            "n_registros", "incompleta", "consumo",
                            "observaciones"]


class Consumo:
    def __init__(self):
        self.llamadas = 0
        self.creditos = 0
        self.restante = None

    def anotar(self, resp):
        self.llamadas += 1
        cab = resp.cabeceras if resp else {}
        try:
            self.creditos += int(cab.get("x-ratelimit-credits-used", 0))
        except ValueError:
            pass
        if "x-ratelimit-remaining" in cab:
            self.restante = cab["x-ratelimit-remaining"]

    def texto(self, base):
        t = "{} {}".format(self.llamadas, "llamada" if self.llamadas == 1 else "llamadas")
        if base == "openalex" and self.creditos:
            t += "; {} créditos de OpenAlex".format(self.creditos)
            if self.restante is not None:
                t += " (quedan {} hoy)".format(self.restante)
        return t


def _abstract_openalex(inv):
    if not inv:
        return ""
    pos = {}
    for palabra, idxs in inv.items():
        for i in idxs:
            pos[i] = palabra
    return " ".join(pos[i] for i in sorted(pos))


def buscar_openalex(spec, desde, hasta, maximo, consumo, solo_contar):
    filtro = "title_and_abstract.search:{},from_publication_date:{}-01-01," \
             "to_publication_date:{}-12-31".format(spec["cadena_exacta"], desde, hasta)
    clave = os.environ.get("OPENALEX_API_KEY", "").strip()
    params = {"filter": filtro, "per-page": 1 if solo_contar else 200}
    if contacto():
        params["mailto"] = contacto()
    if clave:
        params["api_key"] = clave
    regs, total, incompleta = [], None, False
    pagina, cursor = 1, "*"
    while True:
        p = dict(params)
        if clave:
            p["cursor"] = cursor
        else:
            p["page"] = pagina
        r = get_json("https://api.openalex.org/works", p)
        consumo.anotar(r)
        if r is None:
            incompleta = True
            break
        meta = r.datos.get("meta") or {}
        total = meta.get("count", total)
        if solo_contar:
            break
        for w in r.datos.get("results", []):
            fuente = ((w.get("primary_location") or {}).get("source") or {})
            regs.append(registro(
                titulo=w.get("display_name"),
                autores="; ".join((a.get("author") or {}).get("display_name", "")
                                  for a in w.get("authorships", [])),
                anio=w.get("publication_year"), fuente=fuente.get("display_name"),
                idioma=w.get("language"), tipo=w.get("type"), doi=w.get("doi"),
                url=w.get("doi") or (w.get("primary_location") or {}).get(
                    "landing_page_url"),
                resumen=_abstract_openalex(w.get("abstract_inverted_index"))))
        if not r.datos.get("results") or len(regs) >= (total or 0):
            break
        if len(regs) >= maximo:
            incompleta = True
            break
        if clave:
            cursor = meta.get("next_cursor")
            if not cursor:
                break
        else:
            pagina += 1
            if pagina * 200 > 10000:
                incompleta = True
                spec["notas"] += (" Sin clave, OpenAlex solo pagina hasta 10000 "
                                  "resultados.")
                break
    return regs[:maximo], total, incompleta


def buscar_eric(spec, desde, hasta, maximo, consumo, solo_contar):
    q = "{} AND {}".format(spec["cadena_exacta"], spec["filtros"])
    regs, total, start, incompleta = [], None, 0, False
    filas = 1 if solo_contar else 200
    while True:
        r = get_json("https://api.ies.ed.gov/eric/", {
            "search": q, "rows": filas, "start": start, "format": "json",
            "fields": "id,title,author,source,publicationdateyear,description,"
                      "publicationtype,language,url"})
        consumo.anotar(r)
        if r is None:
            incompleta = True
            break
        resp = r.datos.get("response") or {}
        total = resp.get("numFound", total)
        if solo_contar:
            break
        docs = resp.get("docs") or []
        for d in docs:
            enlace = d.get("url") or ""
            m = re.search(r"doi\.org/(10\.\S+)", enlace)
            regs.append(registro(
                doi=m.group(1) if m else "",
                titulo=d.get("title"), autores="; ".join(d.get("author") or []),
                anio=d.get("publicationdateyear"), fuente=d.get("source"),
                idioma="; ".join(d.get("language") or []) if isinstance(
                    d.get("language"), list) else d.get("language"),
                tipo="; ".join(d.get("publicationtype") or []),
                url="https://eric.ed.gov/?id={}".format(d.get("id", "")),
                resumen=d.get("description")))
        start += filas
        if not docs or start >= (total or 0):
            break
        if len(regs) >= maximo:
            incompleta = True
            break
    return regs[:maximo], total, incompleta


def buscar_doaj(spec, desde, hasta, maximo, consumo, solo_contar):
    q = "{} AND {}".format(spec["cadena_exacta"], spec["filtros"])
    url = "https://doaj.org/api/search/articles/" + urllib.parse.quote(q, safe="")
    regs, total, pagina, incompleta = [], None, 1, False
    tam = 1 if solo_contar else 100
    while True:
        r = get_json(url, {"page": pagina, "pageSize": tam})
        consumo.anotar(r)
        if r is None:
            incompleta = True
            break
        total = r.datos.get("total", total)
        if solo_contar:
            break
        resultados = r.datos.get("results") or []
        for x in resultados:
            bj = x.get("bibjson") or {}
            doi = next((i.get("id") for i in bj.get("identifier", [])
                        if (i.get("type") or "").lower() == "doi"), "")
            enlace = next((l.get("url") for l in bj.get("link", []) if l.get("url")), "")
            idiomas = (bj.get("journal") or {}).get("language") or []
            regs.append(registro(
                titulo=bj.get("title"),
                autores="; ".join(a.get("name", "") for a in bj.get("author", [])),
                anio=bj.get("year"), fuente=(bj.get("journal") or {}).get("title"),
                idioma=idiomas[0] if idiomas else "", tipo="artículo", doi=doi,
                url=enlace, resumen=bj.get("abstract")))
        if not resultados or pagina * tam >= (total or 0):
            break
        if len(regs) >= maximo:
            incompleta = True
            break
        if pagina * tam >= 1000:
            incompleta = True
            spec["notas"] += " DOAJ entrega como máximo 1000 resultados por consulta."
            break
        pagina += 1
    return regs[:maximo], total, incompleta


def buscar_crossref(spec, desde, hasta, maximo, consumo, solo_contar,
                    por_subconsulta=100):
    """Corre todas las subconsultas y reparte el tope entre ellas, para que
    cada término e idioma aporte; anota cuánto trajo cada una."""
    filtro = "from-pub-date:{}-01-01,until-pub-date:{}-12-31".format(desde, hasta)
    vistos, regs, total, incompleta = set(), [], 0, False
    subs = spec["subconsultas"]
    filas = max(1, min(por_subconsulta, maximo // max(1, len(subs))))
    spec["subconsultas_corridas"] = []
    for sub in subs:
        p = {"query.bibliographic": sub, "filter": filtro,
             "rows": 0 if solo_contar else filas}
        if contacto():
            p["mailto"] = contacto()
        r = get_json("https://api.crossref.org/works", p)
        consumo.anotar(r)
        if r is None:
            incompleta = True
            spec["notas"] += " Falló la subconsulta «{}».".format(sub)
            continue
        msg = r.datos.get("message") or {}
        spec["subconsultas_corridas"].append(
            {"subconsulta": sub, "total_reportado": msg.get("total-results", 0),
             "recuperados": len(msg.get("items", []))})
        if solo_contar:
            continue
        if msg.get("total-results", 0) > filas:
            incompleta = True
        for it in msg.get("items", []):
            doi = (it.get("DOI") or "").lower()
            if not doi or doi in vistos:
                continue
            vistos.add(doi)
            fecha = (it.get("issued") or it.get("published-online")
                     or it.get("published-print") or {})
            partes = (fecha.get("date-parts") or [[None]])[0]
            regs.append(registro(
                titulo="; ".join(it.get("title") or []),
                autores="; ".join(" ".join(x for x in [a.get("given"), a.get("family")] if x)
                                  for a in it.get("author") or []),
                anio=partes[0] if partes else None,
                fuente="; ".join(it.get("container-title") or []),
                idioma=it.get("language"), tipo=it.get("type"), doi=doi,
                url=it.get("URL"), resumen=re.sub(r"<[^>]+>", " ", it.get("abstract") or "")))
    if not solo_contar:
        spec["notas"] += (" Crossref no da un total para la ecuación; los totales por "
                          "combinación están en subconsultas_corridas. Se pidieron {} "
                          "registros por combinación para repartir el tope de {}."
                          .format(filas, maximo))
    return regs[:maximo], None, incompleta


FUNCIONES = {"openalex": buscar_openalex, "eric": buscar_eric,
             "doaj": buscar_doaj, "crossref": buscar_crossref}


def contar(c, base, ecuacion, a):
    """Consulta cuántos resultados hay, sin guardar registros."""
    spec = cadenas.construir(c, base, ecuacion, a.desde, a.hasta)
    consumo = Consumo()
    _, total, _ = FUNCIONES[base](spec, a.desde, a.hasta, a.max, consumo, True)
    if base == "crossref":
        partes = ["«{}»: {}".format(x["subconsulta"], x["total_reportado"])
                  for x in spec.get("subconsultas_corridas", [])]
        print("== crossref {}: no da un total para la ecuación. Por combinación, en "
              "orden de relevancia: {}. ({})".format(ecuacion, "; ".join(partes),
                                                      consumo.texto(base)))
    else:
        print("== {} {}: la fuente reporta {} resultados ({}).".format(
            base, ecuacion, total, consumo.texto(base)))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carpeta", default=".", help="carpeta del proyecto")
    ap.add_argument("--base", required=True, choices=sorted(FUNCIONES) + ["todas"])
    ap.add_argument("--ecuacion", help="obligatoria salvo con --base todas")
    ap.add_argument("--desde", type=int, required=True)
    ap.add_argument("--hasta", type=int, required=True)
    ap.add_argument("--max", type=int, default=2000,
                    help="tope de registros que se guardan en esta corrida")
    ap.add_argument("--solo-mostrar", action="store_true",
                    help="imprime la cadena y no consulta nada")
    ap.add_argument("--solo-contar", action="store_true",
                    help="consulta solo cuántos resultados hay, sin guardar registros")
    a = ap.parse_args()

    if not protocolo.revisar(a.carpeta, callado=True):
        sys.exit("No se busca nada mientras el protocolo no tenga sus nueve puntos "
                 "y la confirmación de la persona.")
    c = cadenas.cargar(a.carpeta)
    errores = cadenas.problemas(c)
    if errores and not a.solo_mostrar:
        for e in errores:
            print("  - " + e)
        sys.exit("No se busca nada mientras la persona no apruebe las cadenas.")

    if a.base == "todas":
        if not a.solo_contar:
            sys.exit("--base todas solo se usa con --solo-contar.")
        for base in sorted(FUNCIONES):
            for ecuacion in c.get("ecuaciones", {}):
                contar(c, base, ecuacion, a)
        return
    if not a.ecuacion:
        ap.error("--ecuacion es obligatoria salvo con --base todas")
    ecuacion = a.ecuacion.upper()
    if a.solo_contar:
        contar(c, a.base, ecuacion, a)
        return
    spec = cadenas.construir(c, a.base, ecuacion, a.desde, a.hasta)
    print("== {} {} ({}-{})".format(a.base, ecuacion, a.desde, a.hasta))
    print("Cadena exacta: " + spec["cadena_exacta"])
    print("Filtros: " + spec["filtros"])
    if a.solo_mostrar:
        print("Notas: " + spec["notas"])
        return

    consumo = Consumo()
    inicio = ahora()
    regs, total, incompleta = FUNCIONES[a.base](
        spec, a.desde, a.hasta, a.max, consumo, False)

    fuera = [r for r in regs if r["anio"] is not None
             and not (a.desde <= r["anio"] <= a.hasta)]
    if fuera:
        regs = [r for r in regs if r not in fuera]
        spec["notas"] += (" {} registros traían un año fuera de la ventana: quedan en "
                          "«fuera_de_ventana» y no pasan a la normalización.".format(len(fuera)))
    if incompleta and total is not None:
        spec["notas"] += (" Corrida incompleta: la fuente reporta {} y se guardaron "
                          "{}.".format(total, len(regs)))
    meta = {"base": a.base, "ecuacion": ecuacion, "bloques": spec["bloques"],
            "idiomas": spec["idiomas"], "cadena_exacta": spec["cadena_exacta"],
            "subconsultas": spec["subconsultas"],
            "subconsultas_corridas": spec.get("subconsultas_corridas", []),
            "filtros": spec["filtros"],
            "ventana": [a.desde, a.hasta], "inicio": inicio,
            "fecha_busqueda": ahora(), "total_reportado": total,
            "n_registros": len(regs), "n_fuera_de_ventana": len(fuera),
            "incompleta": incompleta,
            "consumo": consumo.texto(a.base), "observaciones": spec["notas"].strip()}
    destino = carpeta(a.carpeta, "crudos") / "{}_{}_{}.json".format(a.base, ecuacion, hoy())
    final = guardar_json_nuevo(destino, {"meta": meta, "registros": regs,
                                         "fuera_de_ventana": fuera})
    fila = dict(meta)
    fila["archivo"] = final.name
    agregar_fila_csv(carpeta(a.carpeta, "busqueda") / "registro_corridas.csv",
                     fila, CAMPOS_REGISTRO_CORRIDAS)
    print("Crudo: {}".format(final))
    if total is None:
        print("Crossref no da un total para la ecuación; se guardaron {} con el tope "
              "de {}. {}".format(len(regs), a.max, consumo.texto(a.base)))
    else:
        print("La fuente reporta {}; se guardaron {}. {}".format(
            total, len(regs), consumo.texto(a.base)))
    if incompleta and total is not None:
        print("ATENCIÓN: corrida incompleta. La persona decide si se acota la "
              "ecuación o se sube el tope (--max).")


if __name__ == "__main__":
    main()
