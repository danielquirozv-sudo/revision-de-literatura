# -*- coding: utf-8 -*-
"""Crea y revisa el protocolo de nueve puntos, y lee la hoja del taller.

Uso (desde cualquier carpeta; <skill> es la carpeta de esta skill y
<proyecto> la de la revisión):
  python3 <skill>/scripts/protocolo.py crear --carpeta <proyecto>
  python3 <skill>/scripts/protocolo.py revisar --carpeta <proyecto>
  python3 <skill>/scripts/protocolo.py leer-hoja hoja.docx --carpeta <proyecto>

El protocolo lo escribe la persona. El agente puede transcribirlo desde la hoja
o desde lo que la persona dicte, pero no decide ninguno de los nueve puntos.
Cuando la persona confirma que el protocolo es suyo, el agente escribe esa
fecha en la línea «Confirmado por la persona el:». Sin esa fecha no se busca.
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import SKILL, carpeta  # noqa: E402

PUNTOS = [
    "1. Tipo de revisión",
    "2. Pregunta de revisión y su marco",
    "3. Criterios de inclusión",
    "4. Criterios de exclusión",
    "5. Ventana temporal e idiomas",
    "6. Bases y ecuación por bloques de términos",
    "7. Reparto entre personas",
    "8. Uso de asistencia automática",
    "9. Registro del protocolo",
]
ETIQUETA_CONFIRMACION = "Confirmado por la persona el:"


def ruta_protocolo(proyecto):
    return carpeta(proyecto, "protocolo") / "protocolo.md"


def crear(proyecto):
    destino = ruta_protocolo(proyecto)
    if destino.exists():
        print("Ya existe {}; no se toca.".format(destino))
        return
    destino.write_text((SKILL / "plantillas" / "protocolo.md").read_text(
        encoding="utf-8"), encoding="utf-8")
    print("Plantilla copiada en {}. La persona la llena.".format(destino))


def secciones(texto):
    """Devuelve {punto: líneas propias}, sin las líneas de guía (> ...)."""
    out, actual = {}, None
    for linea in texto.splitlines():
        m = re.match(r"^##\s+(\d)\.", linea)
        if m:
            actual = int(m.group(1))
            out[actual] = []
            continue
        if actual is None:
            continue
        s = linea.strip()
        if not s or s.startswith(">"):
            continue
        out[actual].append(s)
    return out


def vacio(lineas):
    """Un punto está vacío si solo tiene etiquetas sin llenar, números sueltos o huecos."""
    partes = []
    for linea in lineas:
        if re.match(r"^(\d+\.|-|\*)\s*$", linea):
            continue
        m = re.match(r"^([^:]{1,90}):\s*(.*)$", linea)
        partes.append(m.group(2) if m else linea)
    contenido = re.sub(r"\[[^\]]*\]", "", " ".join(partes))  # huecos entre corchetes
    return len(contenido.strip()) < 3


def criterios(proyecto):
    """Criterios de inclusión (punto 3) y de exclusión (punto 4) tal como los
    escribió la persona, sin el número de la lista. Listas vacías si no hay."""
    p = carpeta(proyecto, "protocolo", crear=False) / "protocolo.md"
    if not p.exists():
        return [], []
    sec = secciones(p.read_text(encoding="utf-8"))

    def lista(punto):
        out = []
        for linea in sec.get(punto, []):
            m = re.match(r"^(?:\d+[.)]|[-*])\s*(.+)$", linea)
            if m and m.group(1).strip():
                out.append(m.group(1).strip())
        return out
    return lista(3), lista(4)


def confirmacion(texto):
    """Fecha escrita en «Confirmado por la persona el:», o cadena vacía."""
    for linea in texto.splitlines():
        if linea.strip().startswith(ETIQUETA_CONFIRMACION):
            valor = linea.split(":", 1)[1].strip()
            return re.sub(r"\[[^\]]*\]", "", valor).strip()
    return ""


def estado(proyecto):
    """Devuelve (faltan, fecha_de_confirmación)."""
    p = ruta_protocolo(proyecto)
    if not p.exists():
        return list(PUNTOS), ""
    texto = p.read_text(encoding="utf-8")
    sec = secciones(texto)
    faltan = [PUNTOS[i - 1] for i in range(1, 10) if vacio(sec.get(i, []))]
    return faltan, confirmacion(texto)


def revisar(proyecto, callado=False):
    """True si los nueve puntos tienen contenido y la persona confirmó el protocolo."""
    if not ruta_protocolo(proyecto).exists():
        print("No hay protocolo. Se crea con: protocolo.py crear --carpeta <proyecto>")
        return False
    faltan, fecha = estado(proyecto)
    if faltan:
        print("El protocolo no está completo. Faltan:")
        for f in faltan:
            print("  - " + f)
        return False
    if not fecha:
        print("Los nueve puntos tienen contenido, pero falta la fecha en «{}»: la "
              "persona no ha confirmado que es su protocolo.".format(ETIQUETA_CONFIRMACION))
        return False
    if not callado:
        print("Protocolo completo, confirmado por la persona el {}.".format(fecha))
    return True


def leer_hoja(ruta, proyecto):
    """Saca el texto de la hoja del taller en el orden en que aparece."""
    ruta = Path(ruta)
    destino = carpeta(proyecto, "protocolo") / "hoja_extraida.txt"
    if ruta.suffix.lower() in (".md", ".txt"):
        destino.write_text(ruta.read_text(encoding="utf-8"), encoding="utf-8")
        print("Texto de la hoja copiado en {}.".format(destino))
        return
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(ruta) as z:
        raiz = ElementTree.fromstring(z.read("word/document.xml"))
    lineas = []
    for nodo in raiz.find("w:body", ns):
        etiqueta = nodo.tag.split("}")[1]
        if etiqueta == "p":
            t = "".join(x.text or "" for x in nodo.iter("{%s}t" % ns["w"])).strip()
            if t:
                lineas.append(t)
        elif etiqueta == "tbl":
            for fila in nodo.iter("{%s}tr" % ns["w"]):
                celdas = [" ".join((x.text or "") for x in celda.iter(
                    "{%s}t" % ns["w"])).strip() for celda in fila.iter("{%s}tc" % ns["w"])]
                if any(celdas):
                    lineas.append(" | ".join(celdas))
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("Texto de la hoja en {}. El agente lo pasa a protocolo.md punto por "
          "punto y la persona lo confirma.".format(destino))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["crear", "revisar", "leer-hoja"])
    ap.add_argument("archivo", nargs="?", help="la hoja (.docx, .md o .txt), para leer-hoja")
    ap.add_argument("--carpeta", default=".", help="carpeta del proyecto")
    a = ap.parse_args()
    if a.accion == "crear":
        crear(a.carpeta)
    elif a.accion == "revisar":
        sys.exit(0 if revisar(a.carpeta) else 1)
    else:
        if not a.archivo:
            ap.error("leer-hoja necesita la ruta de la hoja")
        leer_hoja(a.archivo, a.carpeta)


if __name__ == "__main__":
    main()
