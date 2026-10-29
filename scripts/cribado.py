# -*- coding: utf-8 -*-
"""Prepara el cribado por título y resumen y arma la matriz.

El agente propone; una persona firma. Este programa no decide nada: reparte los
candidatos en lotes, junta las propuestas del agente, las compara con el
protocolo y con los registros, y arma la matriz con las columnas de las personas
vacías. Si la matriz ya existe, conserva lo que las personas hayan escrito en ella.

Uso (<skill> es la carpeta de esta skill y <proyecto> la de la revisión):
  python3 <skill>/scripts/cribado.py preparar --carpeta <proyecto> --tamano 40
  python3 <skill>/scripts/cribado.py pendientes --carpeta <proyecto>
  python3 <skill>/scripts/cribado.py consolidar --carpeta <proyecto>
  python3 <skill>/scripts/cribado.py adoptar --carpeta <proyecto> --lote 1 --persona "Nombre Apellido"

Cada propuesta del agente es un archivo 04_cribado/propuestas/lote_NNN.csv con
las columnas id_ref; propuesta (incluir, excluir o dudoso); motivo, copiado de
los puntos 3 y 4 del protocolo sin el número de la lista (para excluir, el
primer criterio de exclusión que el título o el resumen muestran; para incluir,
«cumple todos los criterios de inclusión»; para dudoso, el primer criterio de
inclusión que no se puede dar por cumplido); y fragmento, las palabras del título
o del resumen que sostienen la propuesta, con « … » entre dos trozos.

consolidar compara cada motivo con los criterios del protocolo, sin contar el
número de la lista, el punto final, las mayúsculas ni los espacios, y lo deja en
la matriz con el texto exacto del protocolo, para que los motivos iguales se
cuenten juntos. Comprueba también que cada trozo del fragmento esté tal cual en
el título o en el resumen, sin contar las comillas ni los guiones tipográficos.
Una propuesta que no pasa alguna de las dos pruebas no entra a la matriz, y el
programa dice por qué.

adoptar copia las propuestas de un lote a las columnas de una persona solo
cuando ella lo pide de manera explícita, con su nombre y la fecha.
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import protocolo  # noqa: E402
from comun import (carpeta, clave_motivo, escribir_csv, hoy, leer_csv,  # noqa: E402
                   para_comparar, respaldar)

CAMPOS_LOTE = ["id_ref", "titulo", "resumen", "anio", "fuente", "tipo", "idioma"]
COLUMNAS_PERSONAS = ["revisor_1", "decision_1", "motivo_1", "revisor_2",
                     "decision_2", "motivo_2", "decision_final", "motivo_final",
                     "fecha_firma", "observaciones"]
CAMPOS_MATRIZ = (["id_ref", "autores", "anio", "titulo", "fuente", "doi", "url",
                  "propuesta_agente", "motivo_agente", "fragmento"] + COLUMNAS_PERSONAS)
VALIDAS = {"incluir", "excluir", "dudoso"}
PATRON_LOTE = re.compile(r"^lote_\d{3}\.csv$")
MOTIVO_INCLUIR = "cumple todos los criterios de inclusión"
ESPERADO = {"incluir": "«{}»".format(MOTIVO_INCLUIR),
            "excluir": "un criterio de exclusión del protocolo",
            "dudoso": "un criterio de inclusión del protocolo"}
ENTRE_TROZOS = re.compile(r"\s*(?:\[\s*(?:…|\.\.\.)\s*\]|…|\.\.\.)\s*")


def candidatos(proyecto):
    ruta = carpeta(proyecto, "deduplicacion") / "candidatos.csv"
    if not ruta.exists():
        sys.exit("Primero se corre deduplicar.py.")
    return leer_csv(ruta)


def archivos_de_lote(carpeta_lotes):
    """Solo lote_NNN.csv; nunca respaldos ni copias con otro nombre."""
    return sorted(p for p in Path(carpeta_lotes).glob("lote_*.csv")
                  if PATRON_LOTE.match(p.name))


def preparar(proyecto, tamano):
    filas = candidatos(proyecto)
    lotes = carpeta(proyecto, "cribado") / "lotes"
    lotes.mkdir(parents=True, exist_ok=True)
    (carpeta(proyecto, "cribado") / "propuestas").mkdir(exist_ok=True)
    if archivos_de_lote(lotes):
        sys.exit("Ya hay lotes en {}. No se rehacen: si los candidatos cambiaron, "
                 "la persona decide qué hacer con el cribado anterior.".format(lotes))
    n = 0
    for i in range(0, len(filas), tamano):
        n += 1
        escribir_csv(lotes / "lote_{:03d}.csv".format(n), filas[i:i + tamano], CAMPOS_LOTE)
    print("{} candidatos repartidos en {} lotes de hasta {}, en el orden de "
          "candidatos.csv (año y título).".format(len(filas), n, tamano))


def pendientes(proyecto):
    base = carpeta(proyecto, "cribado")
    lotes = archivos_de_lote(base / "lotes")
    hechos = {p.name for p in archivos_de_lote(base / "propuestas")}
    faltan = [p.name for p in lotes if p.name not in hechos]
    print("Lotes: {}. Con propuesta: {}. Sin propuesta: {}.".format(
        len(lotes), len(lotes) - len(faltan), len(faltan)))
    for f in faltan:
        print("  " + f)
    return faltan


def leer_propuestas(base):
    propuestas, errores = {}, []
    for p in archivos_de_lote(base / "propuestas"):
        for fila in leer_csv(p):
            id_ref = (fila.get("id_ref") or "").strip()
            valor = (fila.get("propuesta") or "").strip().lower()
            if valor not in VALIDAS:
                errores.append("{}: {} tiene la propuesta «{}»".format(p.name, id_ref, valor))
                continue
            if id_ref in propuestas:            # se conserva la primera aparición
                errores.append("{}: {} aparece otra vez; se conserva la primera".format(
                    p.name, id_ref))
                continue
            propuestas[id_ref] = {"propuesta_agente": valor,
                                  "motivo_agente": (fila.get("motivo") or "").strip(),
                                  "fragmento": (fila.get("fragmento") or "").strip(),
                                  "_lote": p.name}
    return propuestas, errores


def motivos_validos(proyecto):
    """{propuesta: {clave del motivo: texto del protocolo}}; vacío si el protocolo
    no tiene criterios numerados."""
    inclusion, exclusion = protocolo.criterios(proyecto)
    if not inclusion or not exclusion:
        return {}
    return {"incluir": {clave_motivo(MOTIVO_INCLUIR): MOTIVO_INCLUIR},
            "excluir": {clave_motivo(c): c for c in exclusion},
            "dudoso": {clave_motivo(c): c for c in inclusion}}


def fragmento_literal(fragmento, registro):
    """Cada trozo del fragmento está tal cual en el título o en el resumen."""
    textos = [para_comparar(registro.get(k)) for k in ("titulo", "resumen")]
    trozos = [para_comparar(t).strip(" \"'.") for t in ENTRE_TROZOS.split(fragmento)]
    trozos = [t for t in trozos if t]
    return bool(trozos) and all(any(t in x for x in textos) for t in trozos)


def revisar_propuesta(prop, registro, validos):
    """Dice qué está mal en una propuesta, o devuelve una cadena vacía. Si el motivo
    coincide con un criterio, lo deja con el texto exacto del protocolo."""
    if registro is None:
        return "no es un candidato"
    if validos:
        texto = validos[prop["propuesta_agente"]].get(clave_motivo(prop["motivo_agente"]))
        if texto is None:
            return "tiene un motivo que no es {}: «{}»".format(
                ESPERADO[prop["propuesta_agente"]], prop["motivo_agente"])
        prop["motivo_agente"] = texto
    if not fragmento_literal(prop["fragmento"], registro):
        return ("tiene un fragmento que no está tal cual en el título ni en el resumen: "
                "«{}»".format(prop["fragmento"]))
    return ""


def consolidar(proyecto):
    filas = candidatos(proyecto)
    por_id = {f["id_ref"]: f for f in filas}
    base = carpeta(proyecto, "cribado")
    propuestas, errores = leer_propuestas(base)
    validos = motivos_validos(proyecto)
    for id_ref in list(propuestas):
        problema = revisar_propuesta(propuestas[id_ref], por_id.get(id_ref), validos)
        if problema:
            errores.append("{}: {} {}".format(propuestas[id_ref]["_lote"], id_ref, problema))
            del propuestas[id_ref]
    sin_propuesta = [i for i in por_id if i not in propuestas]

    ruta = base / "matriz_cribado.csv"
    previas = {}
    if ruta.exists():
        respaldar(ruta)
        previas = {f["id_ref"]: f for f in leer_csv(ruta)}
    matriz = []
    for f in filas:
        m = {k: f.get(k, "") for k in ["id_ref", "autores", "anio", "titulo",
                                        "fuente", "doi", "url"]}
        prop = propuestas.get(f["id_ref"], {})
        m.update({k: v for k, v in prop.items() if not k.startswith("_")})
        for col in COLUMNAS_PERSONAS:          # lo de las personas no se toca
            m[col] = (previas.get(f["id_ref"]) or {}).get(col, "")
        matriz.append(m)
    escribir_csv(ruta, matriz, CAMPOS_MATRIZ)

    cuenta = Counter(p["propuesta_agente"] for p in propuestas.values())
    firmadas = Counter((m["decision_final"] or "").strip().lower() for m in matriz
                       if (m["decision_final"] or "").strip())
    print("Propuestas del agente: {}".format(dict(cuenta)))
    for valor, rotulo in (("excluir", "Motivos de exclusión propuestos:"),
                          ("dudoso", "Dudosos, por el criterio que no se pudo dar por "
                                     "cumplido:")):
        print(rotulo)
        for motivo, n in Counter(p["motivo_agente"] for p in propuestas.values()
                                 if p["propuesta_agente"] == valor).most_common():
            print("  {:5d}  {}".format(n, motivo))
    print("Candidatos sin propuesta: {}. Decisiones finales firmadas: {}.".format(
        len(sin_propuesta), dict(firmadas)))
    if not validos:
        print("ATENCIÓN: los puntos 3 y 4 de 00_protocolo/protocolo.md no tienen criterios "
              "numerados, así que los motivos no se compararon con el protocolo.")
    if errores:
        print("ATENCIÓN, las propuestas tienen errores que se corrigen en el archivo del "
              "lote antes de seguir. Las que tienen un error no entraron a la matriz:")
        for e in errores[:50]:
            print("  - " + e)
        if len(errores) > 50:
            print("  y {} más.".format(len(errores) - 50))
        if validos:
            print("Motivos válidos, tal como van en la columna motivo:")
            for valor in ("incluir", "excluir", "dudoso"):
                for texto in validos[valor].values():
                    print("  {}: {}".format(valor, texto))
        sys.exit(1)


def adoptar(proyecto, lote, persona):
    if not persona.strip():
        sys.exit("adoptar necesita el nombre de la persona que firma (--persona).")
    base = carpeta(proyecto, "cribado")
    nombre = "lote_{:03d}.csv".format(lote)
    archivo = base / "propuestas" / nombre
    if not archivo.exists():
        sys.exit("No hay propuestas para {}.".format(nombre))
    ids = {(f.get("id_ref") or "").strip() for f in leer_csv(archivo)}
    ruta = base / "matriz_cribado.csv"
    if not ruta.exists():
        sys.exit("Primero se arma la matriz con cribado.py consolidar.")
    respaldar(ruta)
    matriz = leer_csv(ruta)
    n = ya = sin = 0
    for m in matriz:
        if m["id_ref"] not in ids:
            continue
        if (m.get("decision_final") or "").strip():
            ya += 1
            continue
        if not (m.get("propuesta_agente") or "").strip():
            sin += 1
            continue
        m["revisor_1"] = persona
        m["decision_1"] = m.get("propuesta_agente", "")
        m["motivo_1"] = m.get("motivo_agente", "")
        m["decision_final"] = m.get("propuesta_agente", "")
        m["motivo_final"] = m.get("motivo_agente", "")
        m["fecha_firma"] = hoy()
        m["observaciones"] = ("adoptó la propuesta del agente; " +
                              (m.get("observaciones") or "")).strip("; ")
        n += 1
    escribir_csv(ruta, matriz, CAMPOS_MATRIZ)
    print("{} decisiones del {} adoptadas por {} el {}. {} ya tenían decisión y no se "
          "tocaron.".format(n, nombre, persona, hoy(), ya))
    if sin:
        print("{} no tienen una propuesta válida en la matriz y quedan sin firmar: se "
              "corrigen en el archivo del lote y se vuelve a correr consolidar.".format(sin))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["preparar", "pendientes", "consolidar", "adoptar"])
    ap.add_argument("--carpeta", default=".", help="carpeta del proyecto")
    ap.add_argument("--tamano", type=int, default=40, help="candidatos por lote")
    ap.add_argument("--lote", type=int, help="número del lote, para adoptar")
    ap.add_argument("--persona", default="", help="quién firma, para adoptar")
    a = ap.parse_args()
    if a.accion == "preparar":
        preparar(a.carpeta, a.tamano)
    elif a.accion == "pendientes":
        pendientes(a.carpeta)
    elif a.accion == "consolidar":
        consolidar(a.carpeta)
    else:
        if a.lote is None:
            ap.error("adoptar necesita --lote")
        adoptar(a.carpeta, a.lote, a.persona)


if __name__ == "__main__":
    main()
