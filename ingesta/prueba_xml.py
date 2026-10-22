
import xml.etree.ElementTree as ET

ruta = r"C:\Users\ximof\Desktop\R_IA_BIGDATA\BigData_Aplicado\Analisis_Academico\2025-26\alumnos.xml"

arbol = ET.parse(ruta)
raiz = arbol.getroot()

print("Raíz:", raiz.tag)

alumnos = raiz.find("alumnos")
print("Número de alumnos:", len(alumnos))

primer_alumno = alumnos.find("alumno")
print("Grupo:", primer_alumno.get("grupo"))

datos_alumno = {
    "curso": primer_alumno.get("curso"),
    "grupo": primer_alumno.get("grupo"),
    "turno": primer_alumno.get("turno"),
}

print("Datos del alumno:", datos_alumno)
print("Atributos disponibles:")
print(list(primer_alumno.attrib.keys()))