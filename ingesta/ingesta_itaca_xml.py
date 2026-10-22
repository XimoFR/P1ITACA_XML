from pathlib import Path
import hashlib
import json
import logging
import xml.etree.ElementTree as ET
from datetime import date

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ingesta_itaca_xml")

CARPETA_ORIGEN = Path(
    r"C:\Users\ximof\Desktop\R_IA_BIGDATA\BigData_Aplicado\Analisis_Academico"
)
CARPETA_SALIDA = Path("data/raw")

ANOS = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
TABLAS_ORIGEN = ["alumnos", "calificaciones", "contenidos", "cursos", "grupos"]


def anonimizar_nia(nia: str) -> str:
    """Genera el identificador seudonimizado consistente para un NIA."""
    return hashlib.sha256(str(nia).encode("utf-8")).hexdigest()[:10]


def leer_xml(ruta: Path) -> list[dict]:
    """Lee los atributos de los registros contenidos en el XML."""
    arbol = ET.parse(ruta)
    raiz = arbol.getroot()
    registros = []

    for seccion in raiz:
        for nodo in seccion:
            registros.append(dict(nodo.attrib))

    return registros


def preparar_tabla(tabla: str, registros: list[dict], anyo: str) -> list[dict]:
    """Transforma los registros de origen al esquema de salida."""
    resultado = []

    for registro in registros:
        if tabla == "alumnos":
            fila = {
                "Anyo": anyo,
                "NIA": anonimizar_nia(registro["NIA"]),
                "Curso": registro.get("curso"),
                "Grupo": registro.get("grupo"),
                "Turno": registro.get("turno"),
                "Ensenanza": registro.get("ensenanza"),
                "Linea": registro.get("linea"),
                "Modalidad": registro.get("modalidad"),
            }

        elif tabla == "calificaciones":
            fila = {
                "Anyo": anyo,
                "NIA": anonimizar_nia(registro["alumno"]),
                "Curso": registro.get("curso"),
                "Modulo": registro.get("contenido"),
                "Nota": registro.get("nota_numerica"),
                "Evaluacion": registro.get("evaluacion"),
            }

        elif tabla == "contenidos":
            fila = {
                "Anyo": anyo,
                "Curso": registro.get("curso"),
                "Modulo": registro.get("codigo"),
                "Nombre_Modulo": registro.get("nombre_cas"),
            }

        elif tabla == "grupos":
            fila = {
                "Anyo": anyo,
                "Codigo": registro.get("codigo"),
                "Nombre": registro.get("nombre"),
                "Ensenanza": registro.get("ensenanza"),
                "Linea": registro.get("linea"),
                "Turno": registro.get("turno"),
                "Modalidad": registro.get("modalidad"),
                "Aula": registro.get("aula"),
                "Capacidad": registro.get("capacidad"),
            }

        elif tabla == "cursos":
            # Se conserva como fuente auxiliar para documentar y
            # contrastar los cursos; no equivale a una tabla de horas.
            fila = {
                "Anyo": anyo,
                "Codigo": registro.get("codigo"),
                "Nombre_Cas": registro.get("nombre_cas"),
                "Nombre_Val": registro.get("nombre_val"),
                "Abreviatura": registro.get("abreviatura"),
                "Ensenanza": registro.get("ensenanza"),
                "Padre": registro.get("padre"),
            }

        else:
            raise ValueError(f"Tabla de origen desconocida: {tabla}")

        resultado.append(fila)

    return resultado


def guardar_json(datos: list[dict], tabla: str, anyo: str) -> None:
    """Guarda los registros como JSON en la zona raw."""
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = CARPETA_SALIDA / f"{tabla}_{anyo}_{date.today().isoformat()}.json"

    with ruta.open("w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)

    logger.info("%s (%s): %d registros guardados", tabla, anyo, len(datos))


def ejecutar_ingesta() -> None:
    """Procesa todos los años y genera las cinco tablas de salida."""
    errores = 0

    for anyo in ANOS:
        datos_ano = {}

        for tabla in TABLAS_ORIGEN:
            ruta = CARPETA_ORIGEN / anyo / f"{tabla}.xml"

            try:
                registros = leer_xml(ruta)
                datos_ano[tabla] = preparar_tabla(tabla, registros, anyo)
                logger.info("%s (%s): %d registros leídos",
                            tabla, anyo, len(registros))

            except (OSError, ET.ParseError, KeyError, ValueError) as error:
                errores += 1
                logger.error("Error procesando %s: %s", ruta, error)

        # No generar salidas incompletas para un año si falta una fuente.
        if len(datos_ano) != len(TABLAS_ORIGEN):
            logger.error("Se omiten las salidas de %s por errores de ingesta", anyo)
            continue

        # Tablas que sí están respaldadas por los XML.
        salidas = {
            "alumnos": datos_ano["alumnos"],
            "modulos": datos_ano["contenidos"],
            "calificaciones": datos_ano["calificaciones"],
            "grupos": datos_ano["grupos"],
        }

        for nombre, datos in salidas.items():
            guardar_json(datos, nombre, anyo)

        # La fuente no contiene horas lectivas explícitas. Se crea
        # un JSON vacío para reflejar la limitación sin inventar datos.
        guardar_json([], "horas", anyo)

    logger.info(
        "Ingesta finalizada. Errores detectados: %d. "
        "La tabla horas queda vacía porque la fuente no aporta esos datos.",
        errores,
    )

    if errores:
        raise SystemExit(1)


if __name__ == "__main__":
    ejecutar_ingesta()