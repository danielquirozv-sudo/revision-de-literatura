# -*- coding: utf-8 -*-
"""Única fuente de las cadenas de búsqueda.

Lee 00_protocolo/cadenas.json, que copia los bloques de términos del
protocolo, y arma la cadena exacta para cada base. Nadie escribe una cadena de
memoria: se imprime con este programa, se lee, se compara con el protocolo y
solo entonces se corre.

Uso (<skill> es la carpeta de esta skill y <proyecto> la de la revisión):
  python3 <skill>/scripts/cadenas.py revisar --carpeta <proyecto>
  python3 <skill>/scripts/cadenas.py mostrar --carpeta <proyecto> --base openalex --ecuacion E1 --desde 2015 --hasta 2026
  python3 <skill>/scripts/cadenas.py mostrar --carpeta <proyecto> --todas --desde 2015 --hasta 2026
  python3 <skill>/scripts/cadenas.py terminos --carpeta <proyecto>

terminos lista los términos de cada bloque por idioma, para que la persona los
compare con el punto 6 de su protocolo antes de aprobar.

Bases: openalex, eric, doaj, crossref.
"""

import argparse
import itertools
import json
import sys
from pathlib import Path

BASES = ["openalex", "eric", "doaj", "crossref"]

# Idiomas que tiene sentido buscar en cada base si cadenas.json no dice otra cosa.
IDIOMAS_POR_OMISION = {"openalex": ["en", "es", "pt"], "eric": ["en"],
                       "doaj": ["en", "es", "pt"], "crossref": ["en", "es"]}


def ruta_cadenas(proyecto):
    return Path(proyecto) / "00_protocolo" / "cadenas.json"


def cargar(proyecto):
    p = ruta_cadenas(proyecto)
    if not p.exists():
        sys.exit("No existe {}. Se escribe en la etapa de búsqueda, después "
                 "del protocolo, copiando sus bloques de términos.".format(p))
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def problemas(c):
    """Lista lo que impide usar cadenas.json. Vacía si está bien."""
    errores = []
    bloques = c.get("bloques") or {}
    if not bloques:
        errores.append("No hay bloques de términos.")
    for clave, b in bloques.items():
        terminos = [t for idioma, ts in b.items() if idioma != "nombre"
                    for t in (ts or [])]
        if not terminos:
            errores.append("El bloque {} no tiene términos.".format(clave))
        for t in terminos:
            if "," in t:
                errores.append("El término «{}» del bloque {} tiene una coma; "
                               "OpenAlex la lee como separador.".format(t, clave))
    ecuaciones = c.get("ecuaciones") or {}
    if not ecuaciones:
        errores.append("No hay ecuaciones.")
    for e, bs in ecuaciones.items():
        for b in bs:
            if b not in bloques:
                errores.append("La ecuación {} usa el bloque {}, que no existe."
                               .format(e, b))
    if not str(c.get("aprobado_por_la_persona", "")).strip():
        errores.append("Falta la fecha en «aprobado_por_la_persona»: la persona "
                       "no ha aprobado estas cadenas.")
    return errores


def _terminos(bloque, idiomas):
    out = []
    for idioma in idiomas:
        for t in bloque.get(idioma, []) or []:
            t = " ".join(str(t).split())
            if t and t not in out:
                out.append(t)
    return out


def _citar(t, admite_comodin):
    notas = []
    if "*" in t and not admite_comodin:
        notas.append("«{}» sin comodín, porque esta base no lo admite".format(t))
        t = t.replace("*", "")
    if " " in t or "-" in t or not t.replace("*", "").isalnum():
        if "*" in t:
            notas.append("«{}» lleva comodín dentro de una frase; la base puede "
                         "ignorarlo".format(t))
        return '"{}"'.format(t.replace('"', "")), notas
    return t, notas


def _grupo(terminos, admite_comodin):
    partes, notas = [], []
    for t in terminos:
        q, n = _citar(t, admite_comodin)
        partes.append(q)
        notas += n
    return "(" + " OR ".join(partes) + ")", notas


def construir(c, base, ecuacion, desde, hasta, max_subconsultas=30):
    """Devuelve un dict con cadena_exacta, subconsultas, filtros y notas."""
    if base not in BASES:
        raise ValueError("Base desconocida: {}".format(base))
    ecuaciones = c.get("ecuaciones") or {}
    if ecuacion not in ecuaciones:
        raise ValueError("La ecuación {} no está en cadenas.json".format(ecuacion))
    idiomas = (c.get("idiomas_por_base") or {}).get(base) or IDIOMAS_POR_OMISION[base]
    bloques = [c["bloques"][b] for b in ecuaciones[ecuacion]]
    listas = [_terminos(b, idiomas) for b in bloques]
    notas = []
    subconsultas = []

    if base == "crossref":
        # Crossref no admite operadores: se consulta por combinaciones de un
        # término de cada bloque y se unen los resultados.
        # Las combinaciones se arman dentro de cada idioma, para no mezclar
        # un término en inglés con otro en español.
        for idioma in idiomas:
            por_idioma = [_terminos(b, [idioma]) for b in bloques]
            if not all(por_idioma):
                continue
            for combo in itertools.product(*por_idioma):
                if len(subconsultas) >= max_subconsultas:
                    break
                subconsultas.append(" ".join(t.replace("*", "") for t in combo))
        if len(subconsultas) >= max_subconsultas:
            notas.append("Se cortó en {} subconsultas.".format(max_subconsultas))
        cadena = " | ".join(subconsultas)
        filtros = "from-pub-date:{}-01-01, until-pub-date:{}-12-31".format(desde, hasta)
        notas.append("Crossref no es booleano: cada subconsulta devuelve los "
                     "primeros resultados por relevancia; el ruido se depura en "
                     "el cribado.")
    else:
        admite = base in ("eric", "doaj")
        grupos = []
        for lista in listas:
            g, n = _grupo(lista, admite)
            grupos.append(g)
            notas += n
        cadena = " AND ".join(grupos)
        if base == "openalex":
            filtros = ("title_and_abstract.search; from_publication_date:{}-01-01; "
                       "to_publication_date:{}-12-31".format(desde, hasta))
            notas.append("OpenAlex busca en título y resumen, sin comodines.")
        elif base == "eric":
            filtros = "publicationdateyear:[{} TO {}]".format(desde, hasta)
            notas.append("ERIC busca en los campos que indexa por omisión.")
        else:
            filtros = "bibjson.year:[{} TO {}]".format(desde, hasta)
            notas.append("DOAJ busca en todos los campos del artículo.")
    return {"base": base, "ecuacion": ecuacion,
            "bloques": list(ecuaciones[ecuacion]), "idiomas": idiomas,
            "cadena_exacta": cadena, "subconsultas": subconsultas,
            "filtros": filtros, "notas": " ".join(notas)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["revisar", "mostrar", "terminos"])
    ap.add_argument("--carpeta", default=".", help="carpeta del proyecto")
    ap.add_argument("--base", choices=BASES)
    ap.add_argument("--ecuacion")
    ap.add_argument("--todas", action="store_true",
                    help="mostrar todas las bases y ecuaciones")
    ap.add_argument("--desde", type=int)
    ap.add_argument("--hasta", type=int)
    a = ap.parse_args()
    c = cargar(a.carpeta)

    errores = problemas(c)
    if a.accion == "terminos":
        for clave, b in (c.get("bloques") or {}).items():
            print("Bloque {} ({})".format(clave, b.get("nombre", "")))
            for idioma, ts in b.items():
                if idioma != "nombre":
                    print("  {}: {}".format(idioma, "; ".join(ts or [])))
        for e, bs in (c.get("ecuaciones") or {}).items():
            print("Ecuación {}: {}".format(e, " AND ".join(bs)))
        for base in BASES:
            idiomas = (c.get("idiomas_por_base") or {}).get(base) or IDIOMAS_POR_OMISION[base]
            print("Idiomas que se buscan en {}: {}".format(base, ", ".join(idiomas)))
        return
    if a.accion == "revisar":
        if errores:
            print("cadenas.json todavía no se puede usar:")
            for e in errores:
                print("  - " + e)
            sys.exit(1)
        print("cadenas.json está completo y aprobado el {}."
              .format(c["aprobado_por_la_persona"]))
        return

    if a.desde is None or a.hasta is None:
        ap.error("mostrar necesita --desde y --hasta")
    pares = ([(b, e) for b in BASES for e in c.get("ecuaciones", {})]
             if a.todas else [(a.base, (a.ecuacion or "").upper())])
    for base, ecuacion in pares:
        if not base or not ecuacion:
            ap.error("indique --base y --ecuacion, o --todas")
        spec = construir(c, base, ecuacion, a.desde, a.hasta)
        print("== {} {} ({}-{})".format(base, ecuacion, a.desde, a.hasta))
        print(spec["cadena_exacta"])
        print("Filtros: " + spec["filtros"])
        print("Notas: " + spec["notas"])
        print()
    if errores:
        print("AVISO: " + " ".join(errores))


if __name__ == "__main__":
    main()
