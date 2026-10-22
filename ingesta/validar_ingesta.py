from pathlib import Path
import json
import logging
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)
logger = logging.getLogger("validar_ingesta")

CARPETA = Path("data/raw")
ANOS = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]

ESQUEMA = {
    "alumnos": {
        "Anyo", "NIA", "Curso", "Grupo", "Turno",
        "Ensenanza", "Linea", "Modalidad",
    },
    "modulos": {"Anyo", "Curso", "Modulo", "Nombre_Modulo"},
    "calificaciones": {
        "Anyo", "NIA", "Curso", "Modulo", "Nota", "Evaluacion",
    },
    "grupos": {
        "Anyo", "Codigo", "Nombre", "Ensenanza", "Linea",
        "Turno", "Modalidad", "Aula", "Capacidad",
    },
    "horas": set(),
}

CAMPOS_PERSONALES = {
    "nombre", "nombre_cas", "nombre_val",
    "apellido1", "apellido2", "documento",
    "telefono1", "telefono2", "telefono3",
    "email1", "email2", "fecha_nac", "sip",
}


def cargar_json(ruta: Path) -> list[dict]:
    with ruta.open("r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    if not isinstance(datos, list):
        raise ValueError("El JSON no contiene una lista")

    if not all(isinstance(fila, dict) for fila in datos):
        raise ValueError("Hay elementos que no son objetos JSON")

    return datos


def buscar_archivo(tabla: str, anyo: str) -> Path | None:
    archivos = list(CARPETA.glob(f"{tabla}_{anyo}_*.json"))

    if len(archivos) != 1:
        logger.error(
            "%s (%s): se esperaba un archivo y se encontraron %d",
            tabla, anyo, len(archivos),
        )
        return None

    return archivos[0]


def validar() -> None:
    if not CARPETA.exists():
        logger.error("No existe la carpeta %s", CARPETA)
        raise SystemExit(1)

    errores = 0
    advertencias = 0
    datos = {}

    # 1. Cargar y comprobar las 25 salidas esperadas.
    for anyo in ANOS:
        for tabla, campos_esperados in ESQUEMA.items():
            ruta = buscar_archivo(tabla, anyo)

            if ruta is None:
                errores += 1
                continue

            try:
                filas = cargar_json(ruta)
            except (OSError, json.JSONDecodeError, ValueError) as error:
                logger.error("%s: %s", ruta.name, error)
                errores += 1
                continue

            datos[(tabla, anyo)] = filas

            campos_encontrados = set()
            for fila in filas:
                campos_encontrados.update(fila.keys())

            faltantes = campos_esperados - campos_encontrados
            personales = campos_encontrados & CAMPOS_PERSONALES

            if faltantes:
                logger.error(
                    "%s: faltan campos %s", ruta.name, sorted(faltantes)
                )
                errores += 1

            if personales:
                logger.error(
                    "%s: contiene campos personales %s",
                    ruta.name, sorted(personales),
                )
                errores += 1

            if tabla == "alumnos":
                ids = [fila.get("NIA") for fila in filas]
                invalidos = [
                    nia for nia in ids
                    if not isinstance(nia, str)
                    or re.fullmatch(r"[0-9a-f]{10}", nia) is None
                ]

                if invalidos:
                    logger.error(
                        "%s: hay NIA con formato inesperado", ruta.name
                    )
                    errores += 1

            logger.info("%s: %d registros", ruta.name, len(filas))

    # 2. Comprobar las relaciones dentro de cada curso académico.
    for anyo in ANOS:
        alumnos = datos.get(("alumnos", anyo))
        notas = datos.get(("calificaciones", anyo))
        modulos = datos.get(("modulos", anyo))
        grupos = datos.get(("grupos", anyo))

        if alumnos is not None and notas is not None:
            ids_alumnos = {
                fila.get("NIA") for fila in alumnos if fila.get("NIA")
            }
            ids_notas = {
                fila.get("NIA") for fila in notas if fila.get("NIA")
            }
            sin_alumno = ids_notas - ids_alumnos

            if sin_alumno:
                advertencias += 1
                logger.warning(
                    "%s: %d identificadores de calificaciones "
                    "no aparecen en Alumnos",
                    anyo, len(sin_alumno),
                )
            else:
                logger.info("%s: relación Alumnos-Calificaciones correcta", anyo)

        if notas is not None and modulos is not None:
            codigos_modulos = {
                str(fila.get("Modulo"))
                for fila in modulos
                if fila.get("Modulo") not in (None, "")
            }
            referencias = {
                str(fila.get("Modulo"))
                for fila in notas
                if fila.get("Modulo") not in (None, "")
            }
            sin_modulo = referencias - codigos_modulos

            if sin_modulo:
                advertencias += 1
                logger.warning(
                    "%s: %d referencias de calificaciones "
                    "no aparecen en Modulos",
                    anyo, len(sin_modulo),
                )
            else:
                logger.info("%s: relación Calificaciones-Modulos correcta", anyo)

        if alumnos is not None and grupos is not None:
            codigos_grupos = {
    str(fila["Codigo"]).strip()
    for fila in grupos
    if fila.get("Codigo") is not None
    and str(fila["Codigo"]).strip()
            }
            referencias_grupos = {
    str(fila["Grupo"]).strip()
    for fila in alumnos
    if fila.get("Grupo") is not None
    and str(fila["Grupo"]).strip()
            }
            sin_grupo = referencias_grupos - codigos_grupos

            if sin_grupo:
                advertencias += 1
                logger.warning(
                    "%s: %d referencias de alumnos no coinciden "
                    "con códigos de Grupos; hay que revisar la clave",
                    anyo, len(sin_grupo),
                )
            else:
                logger.info("%s: relación Alumnos-Grupos correcta", anyo)

    # 3. Resumen final.
    total = sum(len(filas) for filas in datos.values())
    print("\n--- Resumen de validación ---")
    print(f"Archivos cargados: {len(datos)} de {len(ANOS) * len(ESQUEMA)}")
    print(f"Registros cargados: {total}")
    print(f"Errores estructurales: {errores}")
    print(f"Advertencias de relaciones: {advertencias}")

    if errores:
        logger.error("Validación fallida: corrige los errores antes de entregar")
        raise SystemExit(1)

    if advertencias:
        logger.warning(
            "La estructura es válida, pero quedan relaciones por revisar"
        )
    else:
        logger.info("Validación completada sin errores ni advertencias")


if __name__ == "__main__":
    validar()
