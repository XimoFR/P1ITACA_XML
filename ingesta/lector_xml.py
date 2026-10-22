
from pathlib import Path
import xml.etree.ElementTree as ET
import hashlib


def anonimizar_id(identificador: str) -> str:
    """Genera un identificador seudonimizado consistente."""
    return hashlib.sha256(
        str(identificador).encode("utf-8")
    ).hexdigest()[:16]


def leer_registros(ruta: Path) -> list[dict]:
    """Lee los registros XML y devuelve sus atributos como diccionarios."""
    arbol = ET.parse(ruta)
    raiz = arbol.getroot()

    registros = []

    for seccion in raiz:
        for nodo in seccion:
            registro = dict(nodo.attrib)
            registros.append(registro)

    return registros


def preparar_alumnos(registros: list[dict], anyo: str) -> list[dict]:
    """Selecciona campos académicos y seudonimiza el identificador."""
    alumnos_preparados = []

    for alumno in registros:
        registro = {
            "Anyo": anyo,
            "NIA": anonimizar_id(alumno["NIA"]),
            "Curso": alumno.get("curso"),
            "Ensenanza": alumno.get("ensenanza"),
            "Grupo": alumno.get("grupo"),
            "Turno": alumno.get("turno"),
            "Linea": alumno.get("linea"),
            "Modalidad": alumno.get("modalidad"),
        }

        alumnos_preparados.append(registro)

    return alumnos_preparados


def preparar_calificaciones(
    registros: list[dict], anyo: str
) -> list[dict]:
    """Selecciona campos de calificaciones y seudonimiza al alumno."""
    calificaciones_preparadas = []

    for calificacion in registros:
        registro = {
            "Anyo": anyo,
            "NIA": anonimizar_id(calificacion["alumno"]),
            "Curso": calificacion.get("curso"),
            "Ensenanza": calificacion.get("ensenanza"),
            "Modulo": calificacion.get("contenido"),
            "Evaluacion": calificacion.get("evaluacion"),
            "Nota": calificacion.get("nota_numerica"),
            "Tipo_Nota": calificacion.get("tipo_nota"),
        }

        calificaciones_preparadas.append(registro)

    return calificaciones_preparadas

def resumir_campos(registros: list[dict], campos: list[str]) -> None:
    """Muestra ejemplos de campos sin imprimir datos personales."""
    for campo in campos:
        valores = {
            registro.get(campo)
            for registro in registros
            if registro.get(campo) not in (None, "")
        }

        print(f"  {campo}: {len(valores)} valores distintos")

if __name__ == "__main__":
    carpeta = Path(
        r"C:\Users\ximof\Desktop\R_IA_BIGDATA\BigData_Aplicado\Analisis_Academico"
    )

    anyo = "2025-26"
    tablas = [
        "alumnos",
        "calificaciones",
        "contenidos",
        "cursos",
        "grupos",
    ]

    for tabla in tablas:
        ruta = carpeta / anyo / f"{tabla}.xml"
        registros = leer_registros(ruta)

        print(f"{tabla}: {len(registros)} registros")

        if registros:
            print(f"  Campos: {list(registros[0].keys())}")


    ruta_alumnos = carpeta / anyo / "alumnos.xml"
    alumnos = leer_registros(ruta_alumnos)
    alumnos_preparados = preparar_alumnos(alumnos, anyo)

    print("\nPrueba de preparación de alumnos:")
    print("Registros preparados:", len(alumnos_preparados))
    print("Campos finales:", list(alumnos_preparados[0].keys()))
    print("¿Se conserva el NIA original?",
          alumnos_preparados[0]["NIA"] == alumnos[0]["NIA"])


    ruta_calificaciones = carpeta / anyo / "calificaciones.xml"
    calificaciones = leer_registros(ruta_calificaciones)

    calificaciones_preparadas = preparar_calificaciones(
        calificaciones, anyo
    )

    print("\nPrueba de preparación de calificaciones:")
    print("Registros preparados:", len(calificaciones_preparadas))
    print(
        "Campos finales:",
        list(calificaciones_preparadas[0].keys())
    )

    ids_alumnos = {a["NIA"] for a in alumnos_preparados}
    ids_calificaciones = {
        c["NIA"] for c in calificaciones_preparadas
    }

    print(
        "Identificadores de calificaciones presentes en alumnos:",
        len(ids_calificaciones & ids_alumnos),
        "de",
        len(ids_calificaciones),
    )

    print("\nResumen de contenidos:")
    contenidos = leer_registros(carpeta / anyo / "contenidos.xml")
    resumir_campos(
        contenidos,
        ["codigo", "nombre_cas", "ensenanza", "curso"]
    )

    print("\nResumen de cursos:")
    cursos = leer_registros(carpeta / anyo / "cursos.xml")
    resumir_campos(
        cursos,
        ["codigo", "nombre_cas", "abreviatura", "ensenanza", "padre"]
    )



