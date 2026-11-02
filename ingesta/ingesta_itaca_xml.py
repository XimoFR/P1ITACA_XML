import hashlib
import json
import logging
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("ingesta_itaca_xml")

CARPETA_ORIGEN = Path("data/exportaciones")
CARPETA_SALIDA = Path("data/raw")

TABLAS = ["cursos", "alumnos", "contenidos", "calificaciones"]
CAMPOS = {
    "cursos": ["codigo", "nombre_cas", "nombre_val", "abreviatura", "ensenanza", "padre"],
    "alumnos": ["NIA", "sexo", "nacionalidad", "provincia", "municipio", "ensenanza",
                "curso", "grupo", "turno", "linea", "modalidad", "repite",
                "estado_matricula", "tipo_matricula", "fecha_matricula",
                "fecha_ingreso_centro"],
    "contenidos": ["codigo", "nombre_cas", "nombre_val", "ensenanza", "curso"],
    "calificaciones": ["evaluacion", "alumno", "ensenanza", "curso", "contenido",
                       "bloque_contenido", "nota_numerica", "tipo_nota"],
}
# Campos que contienen un NIA y deben anonimizarse
CAMPO_NIA = {"alumnos": "NIA", "calificaciones": "alumno"}


def anonimizar_nia(nia: str) -> str:
    return hashlib.sha256(str(nia).encode()).hexdigest()[:10]


def parsear_xml(ruta: Path, tabla: str) -> list[dict]:
    """Devuelve los registros de la tabla; Anyo es el campo curso de la cabecera."""
    raiz = ET.parse(ruta).getroot()
    anyo = raiz.get("curso")
    registros = []
    for nodo in raiz.find(tabla):
        fila = {"Anyo": anyo}
        for campo in CAMPOS[tabla]:
            fila[campo] = (nodo.get(campo) or "").strip() or None
        if tabla in CAMPO_NIA:
            campo = CAMPO_NIA[tabla]
            fila[campo] = anonimizar_nia(nodo.get(campo))
        registros.append(fila)
    return registros


def codigos_grupos(ruta: Path) -> set[tuple]:
    """grupos.xml solo se usa para validar alumnos.grupo; no se guarda."""
    raiz = ET.parse(ruta).getroot()
    return {(raiz.get("curso"), g.get("codigo")) for g in raiz.find("grupos")}


def guardar(datos: list[dict], nombre: str) -> None:
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = CARPETA_SALIDA / f"{nombre}_{date.today().isoformat()}.json"
    with ruta.open("w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    logger.info("Guardados %d registros en %s", len(datos), ruta)


def validar(datos: dict[str, list[dict]], grupos: set[tuple]) -> None:
    """Comprueba la coherencia entre tablas (todas las claves incluyen Anyo)."""
    nias = {(a["Anyo"], a["NIA"]) for a in datos["alumnos"]}
    contenidos = {(c["Anyo"], c["codigo"], c["curso"]) for c in datos["contenidos"]}
    cursos = {(c["Anyo"], c["codigo"]) for c in datos["cursos"]}

    comprobaciones = {
        "calificaciones.alumno en alumnos": sum(
            (c["Anyo"], c["alumno"]) not in nias for c in datos["calificaciones"]),
        "calificaciones.contenido en contenidos": sum(
            (c["Anyo"], c["contenido"], c["curso"]) not in contenidos
            for c in datos["calificaciones"]),
        "alumnos.grupo en grupos": sum(
            a["grupo"] is not None and (a["Anyo"], a["grupo"]) not in grupos
            for a in datos["alumnos"]),
        "alumnos.curso en cursos": sum(
            (a["Anyo"], a["curso"]) not in cursos for a in datos["alumnos"]),
        "contenidos.curso en cursos": sum(
            (c["Anyo"], c["curso"]) not in cursos for c in datos["contenidos"]),
    }
    for nombre, huerfanos in comprobaciones.items():
        if huerfanos:
            logger.warning("Validación %s: %d registros huérfanos", nombre, huerfanos)
        else:
            logger.info("Validación %s: OK", nombre)


if __name__ == "__main__":
    datos = {tabla: [] for tabla in TABLAS}
    grupos = set()
    for carpeta in sorted(p for p in CARPETA_ORIGEN.iterdir() if p.is_dir()):
        for tabla in TABLAS:
            datos[tabla] += parsear_xml(carpeta / f"{tabla}.xml", tabla)
        grupos |= codigos_grupos(carpeta / "grupos.xml")
    for tabla in TABLAS:
        guardar(datos[tabla], tabla)
    validar(datos, grupos)
