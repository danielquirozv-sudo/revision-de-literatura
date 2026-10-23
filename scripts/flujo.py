# -*- coding: utf-8 -*-
"""Cuenta, desde los archivos, las cifras del diagrama de flujo de PRISMA.

Ninguna cifra se escribe de memoria: todas salen de los crudos, de la tabla
normalizada, del conteo de la deduplicación, de la matriz y del registro de
texto completo. Separa lo que propuso el agente de lo que firmó una persona,
como pide PRISMA 2020 cuando se usan herramientas automáticas.

Uso (<skill> es la carpeta de esta skill y <proyecto> la de la revisión):
  python3 <skill>/scripts/flujo.py --carpeta <proyecto>

Escribe flujo_prisma.json y flujo_prisma.md en la carpeta del proyecto.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import ahora, carpeta, leer_csv  # noqa: E402


def contar(proyecto):
    f = {"calculado": ahora()}
    por_base, fuera = Counter(), 0
    for p in sorted(carpeta(proyecto, "crudos", crear=False).glob("*.json")):
        with open(p, encoding="utf-8") as fh:
            meta = json.load(fh).get("meta", {})
        n_fuera = int(meta.get("n_fuera_de_ventana") or 0)
        por_base[meta.get("base", p.stem)] += int(meta.get("n_registros") or 0) + n_fuera
        fuera += n_fuera
    f["identificados_por_base"] = dict(por_base)
    f["identificados_total"] = sum(por_base.values())
    f["eliminados_por_estar_fuera_de_la_ventana"] = fuera

    norm = carpeta(proyecto, "normalizacion", crear=False)
    if (norm / "sin_titulo.csv").exists():
        f["sin_titulo_eliminados"] = len(leer_csv(norm / "sin_titulo.csv"))
    if (norm / "fuera_de_ventana.csv").exists():   # crudos hechos a mano o con navegador
        f["eliminados_por_estar_fuera_de_la_ventana"] += len(
            leer_csv(norm / "fuera_de_ventana.csv"))
    ded = carpeta(proyecto, "deduplicacion", crear=False) / "conteo.json"
    if ded.exists():
        c = json.load(open(ded, encoding="utf-8"))
        f["duplicados_eliminados"] = c.get("duplicados_eliminados")
        f["pares_dudosos_sin_decidir"] = c.get("pares_dudosos_sin_decidir")
        f["candidatos_cribados"] = c.get("candidatos")
    f["marcados_no_elegibles_por_herramientas_automaticas"] = 0

    matriz = carpeta(proyecto, "cribado", crear=False) / "matriz_cribado.csv"
    if matriz.exists():
        m = leer_csv(matriz)
        f["propuestas_del_agente"] = dict(Counter(
            (x.get("propuesta_agente") or "sin propuesta") for x in m))
        finales = Counter((x.get("decision_final") or "").strip().lower() or "sin firmar"
                          for x in m)
        f["firmados_incluir"] = finales.get("incluir", 0)
        f["firmados_excluir"] = finales.get("excluir", 0)
        f["firmados_dudoso_pasan_a_texto_completo"] = finales.get("dudoso", 0)
        f["sin_firmar"] = finales.get("sin firmar", 0)
        f["firmados_adoptando_la_propuesta_del_agente"] = sum(
            1 for x in m if "adoptó la propuesta del agente" in (x.get("observaciones") or ""))
        f["excluidos_por_personas_con_motivo"] = dict(Counter(
            (x.get("motivo_final") or "sin motivo escrito").strip()
            for x in m if (x.get("decision_final") or "").strip().lower() == "excluir"))
        f["excluidos_solo_por_el_agente"] = 0

    tc = carpeta(proyecto, "extraccion", crear=False) / "texto_completo.csv"
    if tc.exists():
        t = leer_csv(tc)
        f["informes_buscados"] = len(t)
        f["informes_buscados_por_decision_del_cribado"] = dict(Counter(
            (x.get("decision_cribado") or "").strip() for x in t))
        f["informes_no_conseguidos"] = sum(
            1 for x in t if (x.get("texto_conseguido") or "").strip().lower() in ("no", "n"))
        evaluados = [x for x in t if (x.get("decision_texto_completo") or "").strip()]
        f["informes_evaluados"] = len(evaluados)
        f["informes_excluidos_con_motivo"] = dict(Counter(
            (x.get("motivo_texto_completo") or "sin motivo escrito").strip()
            for x in evaluados
            if x["decision_texto_completo"].strip().lower() == "excluir"))
        f["estudios_incluidos"] = sum(
            1 for x in evaluados if x["decision_texto_completo"].strip().lower() == "incluir")
    fichas = carpeta(proyecto, "extraccion", crear=False) / "fichas"
    if fichas.exists():
        f["fichas_escritas"] = len(list(fichas.glob("*.md")))
    return f


def como_texto(f):
    l = ["# Cifras del diagrama de flujo", "",
         "Calculadas el {} desde los archivos de la carpeta.".format(f["calculado"]), "",
         "## Identificación", ""]
    for base, n in f.get("identificados_por_base", {}).items():
        l.append("- {}: {}".format(base, n))
    l += ["- Total identificado: {}".format(f.get("identificados_total")),
          "- Eliminados antes del cribado por duplicados: {}".format(
              f.get("duplicados_eliminados", "sin calcular")),
          "- Eliminados antes del cribado por no tener título: {}".format(
              f.get("sin_titulo_eliminados", "sin calcular")),
          "- Eliminados antes del cribado por traer un año fuera de la ventana "
          "(quedan en los crudos): {}".format(
              f.get("eliminados_por_estar_fuera_de_la_ventana", 0)),
          "- Marcados como no elegibles por herramientas automáticas: 0. El agente "
          "solo propone; no elimina registros.", "", "## Cribado", "",
          "- Registros cribados: {}".format(f.get("candidatos_cribados", "sin calcular"))]
    if "propuestas_del_agente" in f:
        l.append("- Propuestas del agente (no son decisiones): {}".format(
            f["propuestas_del_agente"]))
        l.append("- Firmados por una persona para incluir: {}".format(f["firmados_incluir"]))
        l.append("- Firmados por una persona para excluir: {}".format(f["firmados_excluir"]))
        l.append("- Firmados como dudosos, que pasan a texto completo: {}".format(
            f["firmados_dudoso_pasan_a_texto_completo"]))
        l.append("- Sin firmar todavía: {}".format(f["sin_firmar"]))
        l.append("- De las decisiones firmadas, las que una persona tomó adoptando en bloque "
                 "la propuesta del agente: {}. Se declaran en el método.".format(
                     f["firmados_adoptando_la_propuesta_del_agente"]))
        for motivo, n in f.get("excluidos_por_personas_con_motivo", {}).items():
            l.append("  - Excluidos por una persona, «{}»: {}".format(motivo, n))
    if "informes_buscados" in f:
        l += ["- Informes buscados para texto completo: {}".format(f["informes_buscados"]),
              "- Informes no conseguidos: {}".format(f["informes_no_conseguidos"]),
              "- Informes evaluados a texto completo: {}".format(f["informes_evaluados"])]
        for motivo, n in f.get("informes_excluidos_con_motivo", {}).items():
            l.append("  - Excluidos a texto completo, «{}»: {}".format(motivo, n))
    l += ["", "## Incluidos", "",
          "- Estudios incluidos: {}".format(f.get("estudios_incluidos", "sin calcular")),
          "- Fichas escritas: {}".format(f.get("fichas_escritas", 0))]
    return "\n".join(l) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carpeta", default=".", help="carpeta del proyecto")
    a = ap.parse_args()
    f = contar(a.carpeta)
    raiz = Path(a.carpeta)
    with open(raiz / "flujo_prisma.json", "w", encoding="utf-8") as fh:
        json.dump(f, fh, ensure_ascii=False, indent=2)
    (raiz / "flujo_prisma.md").write_text(como_texto(f), encoding="utf-8")
    print(como_texto(f))


if __name__ == "__main__":
    main()
