# -*- coding: utf-8 -*-
"""Une todos los crudos en una tabla con los mismos campos.

Lee 01_busqueda/crudos/*.json y escribe:
  02_normalizacion/registros.csv   un registro por fila, con la corrida que lo trajo
  02_normalizacion/sin_titulo.csv  los registros sin título, que se cuentan aparte

Uso (<skill> es la carpeta de esta skill y <proyecto> la de la revisión):
  python3 <skill>/scripts/normalizar.py --carpeta <proyecto>

Antes de reescribir las tablas deja un respaldo con la fecha.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import (CAMPOS_REGISTRO, carpeta, escribir_csv, normalizar_doi,  # noqa: E402
                   respaldar)

CAMPOS = ["id_registro", "id_corrida", "base", "ecuacion"] + CAMPOS_REGISTRO


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carpeta", default=".", help="carpeta del proyecto")
    a = ap.parse_args()

    crudos = sorted(carpeta(a.carpeta, "crudos").glob("*.json"))
    if not crudos:
        sys.exit("No hay crudos en 01_busqueda/crudos/.")
    filas, sin_titulo, fuera = [], [], []
    for p in crudos:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        meta = d.get("meta", {})
        id_corrida = p.stem
        desde, hasta = (meta.get("ventana") or [None, None])
        for i, r in enumerate(d.get("registros", []), start=1):
            fila = {k: r.get(k, "") for k in CAMPOS_REGISTRO}
            fila["doi"] = normalizar_doi(fila.get("doi"))
            fila.update({"id_registro": "{}-{:04d}".format(id_corrida, i),
                         "id_corrida": id_corrida, "base": meta.get("base", ""),
                         "ecuacion": meta.get("ecuacion", "")})
            if not str(fila.get("titulo") or "").strip():
                sin_titulo.append(fila)
                continue
            anio = fila.get("anio")
            if desde and hasta and isinstance(anio, int) and not (desde <= anio <= hasta):
                fuera.append(fila)
                continue
            filas.append(fila)
        print("{}: {} registros".format(p.name, len(d.get("registros", []))))

    destino = carpeta(a.carpeta, "normalizacion")
    for nombre in ("registros.csv", "sin_titulo.csv", "fuera_de_ventana.csv"):
        respaldar(destino / nombre)
    escribir_csv(destino / "registros.csv", filas, CAMPOS)
    escribir_csv(destino / "sin_titulo.csv", sin_titulo, CAMPOS)
    escribir_csv(destino / "fuera_de_ventana.csv", fuera, CAMPOS)
    print("Normalizados: {}. Sin título, contados aparte: {}. Con año fuera de la "
          "ventana, contados aparte: {}.".format(len(filas), len(sin_titulo), len(fuera)))


if __name__ == "__main__":
    main()
