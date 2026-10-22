from pathlib import Path
import json

CARPETA = Path("data/raw")

ANOS = [
    "2022-23",
    "2023-24",
    "2024-25",
    "2025-26",
]


def cargar(tabla: str, anyo: str) -> list[dict]:
    """Carga el JSON de una tabla y un curso académico."""
    archivos = list(CARPETA.glob(f"{tabla}_{anyo}_*.json"))

    if len(archivos) != 1:
        raise ValueError(
            f"Se esperaba un archivo {tabla} para {anyo}, "
            f"pero se encontraron {len(archivos)}"
        )

    with archivos[0].open("r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    if not isinstance(datos, list):
        raise ValueError(f"{archivos[0].name} no contiene una lista JSON")

    return datos


def valores_no_vacios(registros: list[dict], campo: str) -> set[str]:
    """Extrae valores únicos de un campo, ignorando los valores vacíos."""
    return {
        str(registro[campo]).strip()
        for registro in registros
        if registro.get(campo) is not None
        and str(registro[campo]).strip()
    }


def revisar_relaciones() -> None:
    for anyo in ANOS:
        alumnos = cargar("alumnos", anyo)
        grupos = cargar("grupos", anyo)

        grupos_alumnos = valores_no_vacios(alumnos, "Grupo")
        codigos_grupos = valores_no_vacios(grupos, "Codigo")
        nombres_grupos = valores_no_vacios(grupos, "Nombre")

        sin_codigo = grupos_alumnos - codigos_grupos
        sin_nombre = grupos_alumnos - nombres_grupos

        coincidencias_codigo = grupos_alumnos & codigos_grupos
        coincidencias_nombre = grupos_alumnos & nombres_grupos

        print(f"\nCurso académico: {anyo}")
        print("Grupos distintos en Alumnos:", len(grupos_alumnos))
        print("Códigos distintos en Grupos:", len(codigos_grupos))
        print("Nombres distintos en Grupos:", len(nombres_grupos))

        print(
            "Coincidencias con Codigo:",
            len(coincidencias_codigo),
        )
        print(
            "Coincidencias con Nombre:",
            len(coincidencias_nombre),
        )

        print(
            "Valores de Grupo sin coincidencia en Codigo:",
            sorted(sin_codigo)[:10],
        )
        print(
            "Valores de Grupo sin coincidencia en Nombre:",
            sorted(sin_nombre)[:10],
        )


if __name__ == "__main__":
    revisar_relaciones()