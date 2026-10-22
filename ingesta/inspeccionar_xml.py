
from pathlib import Path
import xml.etree.ElementTree as ET

carpeta = Path(
    r"C:\Users\ximof\Desktop\R_IA_BIGDATA\BigData_Aplicado\Analisis_Academico"
)

for ruta in sorted(carpeta.glob("*/*.xml")):
    raiz = ET.parse(ruta).getroot()

    print(f"\nArchivo: {ruta.parent.name}/{ruta.name}")
    print("Raíz:", raiz.tag)
    print("Secciones:", [hijo.tag for hijo in raiz])

    for seccion in raiz:
        registros = list(seccion)

        if registros:
            primero = registros[0]
            print("  Tipo de registro:", primero.tag)
            print("  Atributos:", list(primero.attrib.keys()))
            print("  Etiquetas hijas:", [hijo.tag for hijo in primero])
            break


for nombre in ["alumnos", "calificaciones", "contenidos", "cursos", "grupos"]:
    ruta = carpeta / "2025-26" / f"{nombre}.xml"
    raiz = ET.parse(ruta).getroot()
    registros = list(raiz[0])

    print(f"\n{nombre}: {len(registros)} registros")

    if registros:
        primero = registros[0]
        print("  Tipo:", primero.tag)

        for campo in ["curso", "codigo", "ensenanza", "contenido",
                      "alumno", "grupo", "evaluacion"]:
            if campo in primero.attrib:
                print(f"  Tiene atributo {campo}")
