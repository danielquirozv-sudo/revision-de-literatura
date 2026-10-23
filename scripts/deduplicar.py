# -*- coding: utf-8 -*-
"""Quita los duplicados en tres pasadas y deja la lista única de candidatos.

  1. DOI idéntico. Es la única fusión que no admite duda.
  2. Título normalizado y mismo año, entre los que no comparten DOI.
  3. Títulos muy parecidos (año con diferencia de uno a lo sumo). Por encima del
     umbral automático se fusionan; entre el umbral de duda y el automático no se
     fusionan solos: van a pares_dudosos.csv y los decide una persona.

Guardia: dos registros con DOI distinto no se fusionan nunca, aunque coincidan
título y año (suelen ser el resumen de congreso y el artículo). Los registros
sin DOI solo se pueden unir por título y año (pasadas 2 y 3). El candidato que
queda toma los datos que falten (DOI, publicación, resumen) de los registros que
se fusionaron con él.

Los identificadores R-NNNN se fijan aquí. Una vez empieza el cribado no se
recalculan: el programa se niega a correr si ya hay lotes de cribado.

Salidas en 03_deduplicacion/: candidatos.csv, duplicados_eliminados.csv (con la
pasada que fusionó cada registro), pares_dudosos.csv y conteo.json. Antes de
reescribirlas deja respaldos en 03_deduplicacion/respaldos/.

Uso (<skill> es la carpeta de esta skill y <proyecto> la de la revisión):
  python3 <skill>/scripts/deduplicar.py --carpeta <proyecto>
  python3 <skill>/scripts/deduplicar.py --carpeta <proyecto> --aplicar-dudosos <proyecto>/03_deduplicacion/pares_dudosos.csv
"""

import argparse
import json
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import (carpeta, escribir_csv, leer_csv, normalizar_texto,  # noqa: E402
                   respaldar)

CAMPOS_CAND = ["id_ref", "autores", "anio", "titulo", "fuente", "idioma", "tipo",
               "doi", "url", "resumen", "bases", "ecuaciones", "ids_registro",
               "n_apariciones"]
COMPLETABLES = ["doi", "fuente", "resumen", "autores", "anio", "url", "idioma", "tipo"]
CAMPOS_DUDOSOS = ["similitud", "fusionar", "id_a", "titulo_a", "autores_a", "anio_a",
                  "fuente_a", "doi_a", "id_b", "titulo_b", "autores_b", "anio_b",
                  "fuente_b", "doi_b"]


def _riqueza(r):
    return (1 if r.get("doi") else 0, len(r.get("resumen") or ""),
            len(r.get("autores") or ""))


class Grupo:
    def __init__(self, r):
        self.principal = r
        self.miembros = [r]

    def absorber(self, r, pasada):
        r["_pasada"] = pasada
        self.miembros.append(r)
        if _riqueza(r) > _riqueza(self.principal):
            # el que era principal pasa a ser duplicado, por la misma razón
            self.principal.setdefault("_pasada", pasada)
            self.principal = r

    def dois(self):
        return {m.get("doi") for m in self.miembros if m.get("doi")}

    def fila(self, id_ref):
        p = {k: self.principal.get(k, "") for k in CAMPOS_CAND}
        for campo in COMPLETABLES:               # completa lo que le falte al principal
            if not str(p.get(campo) or "").strip():
                for m in self.miembros:
                    if str(m.get(campo) or "").strip():
                        p[campo] = m[campo]
                        break
        p["id_ref"] = id_ref
        p["bases"] = "; ".join(sorted({m.get("base", "") for m in self.miembros} - {""}))
        p["ecuaciones"] = "; ".join(sorted({m.get("ecuacion", "") for m in self.miembros} - {""}))
        p["ids_registro"] = "; ".join(m["id_registro"] for m in self.miembros)
        p["n_apariciones"] = len(self.miembros)
        return p


def incompatibles(g1, g2):
    d1, d2 = g1.dois(), g2.dois()
    return bool(d1) and bool(d2) and d1.isdisjoint(d2)


def deduplicar(registros, umbral_auto, umbral_duda):
    for r in registros:
        r["_t"] = normalizar_texto(r.get("titulo"))
        r["_a"] = int(r["anio"]) if str(r.get("anio", "")).strip().isdigit() else None

    grupos, por_doi = [], {}
    for r in registros:                                   # pasada 1
        doi = r.get("doi")
        if doi and doi in por_doi:
            por_doi[doi].absorber(r, "DOI idéntico")
        else:
            g = Grupo(r)
            grupos.append(g)
            if doi:
                por_doi[doi] = g

    por_clave, siguientes = {}, []
    for g in grupos:                                      # pasada 2
        clave = (g.principal["_t"], g.principal["_a"])
        destino = por_clave.get(clave)
        if clave[0] and destino is not None and not incompatibles(g, destino):
            for m in g.miembros:
                destino.absorber(m, "título y año")
        else:
            siguientes.append(g)
            if clave[0] and clave not in por_clave:
                por_clave[clave] = g

    finales, dudosos = [], []
    for g in siguientes:                                  # pasada 3
        t, a = g.principal["_t"], g.principal["_a"]
        destino, duda = None, None
        for f in finales:
            t2, a2 = f.principal["_t"], f.principal["_a"]
            if not t or not t2 or abs(len(t) - len(t2)) > 30:
                continue
            if a is not None and a2 is not None and abs(a - a2) > 1:
                continue
            if incompatibles(g, f):
                continue
            ratio = SequenceMatcher(None, t, t2).ratio()
            if ratio >= umbral_auto:
                destino = f
                break
            if ratio >= umbral_duda and duda is None:
                duda = (f, ratio)
        if destino is not None:
            for m in g.miembros:
                destino.absorber(m, "títulos casi iguales")
            continue
        finales.append(g)
        if duda:
            f, ratio = duda
            pa, pb = g.principal, f.principal
            dudosos.append({"similitud": round(ratio, 3), "fusionar": "",
                            "id_a": pa["id_registro"], "titulo_a": pa["titulo"],
                            "autores_a": pa.get("autores", ""), "anio_a": pa.get("anio", ""),
                            "fuente_a": pa.get("fuente", ""), "doi_a": pa.get("doi", ""),
                            "id_b": pb["id_registro"], "titulo_b": pb["titulo"],
                            "autores_b": pb.get("autores", ""), "anio_b": pb.get("anio", ""),
                            "fuente_b": pb.get("fuente", ""), "doi_b": pb.get("doi", "")})
    return finales, dudosos


def aplicar_dudosos(finales, ruta):
    decididos = [d for d in leer_csv(ruta)
                 if (d.get("fusionar") or "").strip().lower() in ("si", "sí", "s")]
    indice = {m["id_registro"]: g for g in finales for m in g.miembros}
    n = 0
    for d in decididos:
        ga, gb = indice.get(d["id_a"]), indice.get(d["id_b"])
        if ga is None or gb is None or ga is gb:
            continue
        for m in ga.miembros:
            gb.absorber(m, "decisión de la persona")
            indice[m["id_registro"]] = gb
        finales.remove(ga)
        n += 1
    print("Fusiones decididas por la persona y aplicadas: {}".format(n))
    return finales


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carpeta", default=".", help="carpeta del proyecto")
    ap.add_argument("--umbral-auto", type=float, default=0.97)
    ap.add_argument("--umbral-duda", type=float, default=0.93)
    ap.add_argument("--aplicar-dudosos", default=None,
                    help="pares_dudosos.csv con la columna fusionar llena (Sí o No)")
    a = ap.parse_args()

    lotes = carpeta(a.carpeta, "cribado", crear=False) / "lotes"
    if lotes.exists() and any(lotes.glob("lote_*.csv")):
        sys.exit("El cribado ya empezó: los identificadores R-NNNN no se recalculan. "
                 "Si hay registros nuevos, la persona decide cómo se incorporan.")
    ruta = carpeta(a.carpeta, "normalizacion") / "registros.csv"
    if not ruta.exists():
        sys.exit("Primero se corre normalizar.py.")
    salida = carpeta(a.carpeta, "deduplicacion")
    dudosos_previos = salida / "pares_dudosos.csv"
    if (not a.aplicar_dudosos and dudosos_previos.exists()
            and any((d.get("fusionar") or "").strip() for d in leer_csv(dudosos_previos))):
        sys.exit("pares_dudosos.csv ya tiene respuestas de la persona. Se aplican con "
                 "--aplicar-dudosos; correr sin esa opción las borraría.")

    registros = leer_csv(ruta)
    finales, dudosos = deduplicar(registros, a.umbral_auto, a.umbral_duda)
    if a.aplicar_dudosos:
        finales = aplicar_dudosos(finales, a.aplicar_dudosos)
        dudosos = []
    finales.sort(key=lambda g: (g.principal["_a"] or 9999, g.principal["_t"]))
    filas = [g.fila("R-{:04d}".format(i + 1)) for i, g in enumerate(finales)]
    eliminados = [{"id_eliminado": m["id_registro"], "titulo": m["titulo"],
                   "base": m.get("base", ""), "pasada": m.get("_pasada", ""),
                   "quedo_en": g.principal["id_registro"]}
                  for g in finales for m in g.miembros if m is not g.principal]

    for nombre in ("candidatos.csv", "duplicados_eliminados.csv", "conteo.json"):
        respaldar(salida / nombre)
    escribir_csv(salida / "candidatos.csv", filas, CAMPOS_CAND)
    escribir_csv(salida / "duplicados_eliminados.csv", eliminados,
                 ["id_eliminado", "titulo", "base", "pasada", "quedo_en"])
    if not a.aplicar_dudosos:
        respaldar(dudosos_previos)
        escribir_csv(dudosos_previos, dudosos, CAMPOS_DUDOSOS)
    conteo = {"registros_normalizados": len(registros),
              "duplicados_eliminados": len(eliminados),
              "duplicados_por_pasada": dict(Counter(e["pasada"] for e in eliminados)),
              "candidatos": len(filas),
              "candidatos_sin_doi": sum(1 for f in filas if not f.get("doi")),
              "pares_dudosos_sin_decidir": len(dudosos),
              "umbral_auto": a.umbral_auto, "umbral_duda": a.umbral_duda,
              "dudosos_aplicados_desde": a.aplicar_dudosos or ""}
    with open(salida / "conteo.json", "w", encoding="utf-8") as f:
        json.dump(conteo, f, ensure_ascii=False, indent=2)
    print(json.dumps(conteo, ensure_ascii=False, indent=2))
    if dudosos:
        print("ATENCIÓN: {} pares dudosos esperan la decisión de una persona "
              "(columna fusionar de pares_dudosos.csv).".format(len(dudosos)))


if __name__ == "__main__":
    main()
