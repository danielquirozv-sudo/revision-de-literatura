# -*- coding: utf-8 -*-
"""Lleva el paso a texto completo y abre las fichas de extracción.

Uso (<skill> es la carpeta de esta skill y <proyecto> la de la revisión):
  python3 <skill>/scripts/extraccion.py preparar --carpeta <proyecto>
  python3 <skill>/scripts/extraccion.py ficha R-0012 --carpeta <proyecto>

preparar lee la matriz del cribado y copia a 05_extraccion/texto_completo.csv
los candidatos cuya decisión final es «incluir» o «dudoso» y lleva el nombre de
quien firmó: los dos pasan a leerse a texto completo. Las columnas de ese
archivo las llena la persona (si consiguió el texto, si el estudio se queda y
por qué no). ficha crea 05_extraccion/fichas/R-0012.md desde la plantilla, con
los datos de identificación, solo para un estudio que la persona dejó a texto
completo; nunca sobrescribe.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import carpeta, escribir_csv, leer_csv, respaldar  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
CAMPOS = ["id_ref", "autores", "anio", "titulo", "doi", "decision_cribado", "firmado_por",
          "texto_conseguido",
          "archivo_texto", "decision_texto_completo", "motivo_texto_completo",
          "ficha"]
DE_LA_PERSONA = ["texto_conseguido", "archivo_texto", "decision_texto_completo",
                 "motivo_texto_completo"]


def preparar(proyecto):
    matriz = carpeta(proyecto, "cribado") / "matriz_cribado.csv"
    if not matriz.exists():
        sys.exit("Primero se arma la matriz con cribado.py consolidar.")
    firmados = [f for f in leer_csv(matriz)
                if (f.get("decision_final") or "").strip().lower() in ("incluir", "dudoso")
                and ((f.get("revisor_1") or "").strip() or (f.get("revisor_2") or "").strip())]
    ruta = carpeta(proyecto, "extraccion") / "texto_completo.csv"
    previas = {}
    if ruta.exists():
        respaldar(ruta)
        previas = {f["id_ref"]: f for f in leer_csv(ruta)}
    filas = []
    for f in firmados:
        fila = {k: f.get(k, "") for k in ["id_ref", "autores", "anio", "titulo", "doi"]}
        fila["decision_cribado"] = f.get("decision_final", "")
        fila["firmado_por"] = "; ".join(x for x in ((f.get("revisor_1") or "").strip(),
                                                    (f.get("revisor_2") or "").strip()) if x)
        for col in DE_LA_PERSONA:
            fila[col] = (previas.get(f["id_ref"]) or {}).get(col, "")
        ficha = carpeta(proyecto, "extraccion") / "fichas" / "{}.md".format(f["id_ref"])
        fila["ficha"] = ficha.name if ficha.exists() else ""
        filas.append(fila)
    escribir_csv(ruta, filas, CAMPOS)
    print("Pasan a texto completo, con firma de una persona: {} ({} incluidos y {} "
          "dudosos).".format(len(filas),
                             sum(1 for f in filas if f["decision_cribado"] == "incluir"),
                             sum(1 for f in filas if f["decision_cribado"] == "dudoso")))


def ficha(proyecto, id_ref):
    matriz = carpeta(proyecto, "cribado") / "matriz_cribado.csv"
    datos = next((f for f in leer_csv(matriz) if f["id_ref"] == id_ref), None)
    if datos is None:
        sys.exit("{} no está en la matriz.".format(id_ref))
    tc = carpeta(proyecto, "extraccion") / "texto_completo.csv"
    fila_tc = next((f for f in leer_csv(tc) if f["id_ref"] == id_ref), None) \
        if tc.exists() else None
    if fila_tc is None:
        sys.exit("{} no está en texto_completo.csv: primero extraccion.py preparar.".format(id_ref))
    if (fila_tc.get("decision_texto_completo") or "").strip().lower() != "incluir":
        sys.exit("{} no tiene la decisión «incluir» a texto completo, que escribe la "
                 "persona en texto_completo.csv.".format(id_ref))
    destino = carpeta(proyecto, "extraccion") / "fichas" / "{}.md".format(id_ref)
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        sys.exit("La ficha {} ya existe; no se sobrescribe.".format(destino))
    plantilla = (SKILL / "plantillas" / "ficha.md").read_text(encoding="utf-8")
    for clave in ["id_ref", "autores", "anio", "titulo", "fuente", "doi"]:
        plantilla = plantilla.replace("{{" + clave + "}}", datos.get(clave, "") or "")
    destino.write_text(plantilla, encoding="utf-8")
    print("Ficha abierta en {}.".format(destino))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["preparar", "ficha"])
    ap.add_argument("id_ref", nargs="?")
    ap.add_argument("--carpeta", default=".", help="carpeta del proyecto")
    a = ap.parse_args()
    if a.accion == "preparar":
        preparar(a.carpeta)
    else:
        if not a.id_ref:
            ap.error("ficha necesita el identificador, por ejemplo R-0012")
        ficha(a.carpeta, a.id_ref)


if __name__ == "__main__":
    main()
