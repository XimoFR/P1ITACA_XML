## Bloque 1. Ingesta de datos académicos de ITACA

### Fuentes de datos

La práctica utiliza exportaciones XML de datos académicos correspondientes a los cursos 2021-22, 2022-23, 2023-24, 2024-25 y 2025-26. Los archivos de origen son `alumnos.xml`, `calificaciones.xml`, `contenidos.xml`, `cursos.xml` y `grupos.xml`, organizados por curso académico.

El proceso se ejecuta mediante Python y la biblioteca estándar `xml.etree.ElementTree`. Los registros se transforman a diccionarios y se guardan en formato JSON dentro de `data/raw/`. La actualización se realiza cuando se dispone de nuevas exportaciones.

### Proceso de ingesta

El script `ingesta/ingesta_itaca_xml.py` procesa los archivos XML, adapta los campos disponibles y registra el resultado mediante el módulo `logging`.

Se generan las siguientes salidas:

- **Alumnos:** identificador seudonimizado, curso académico, curso, grupo, turno, enseñanza, línea y modalidad.
- **Modulos:** código del contenido, curso académico, curso y nombre del módulo.
- **Calificaciones:** identificador seudonimizado del alumno, curso, módulo, nota y evaluación.
- **Grupos:** código, nombre, enseñanza, línea, turno, modalidad, aula y capacidad.
- **Horas:** archivo JSON vacío, dado que las exportaciones disponibles no contienen datos explícitos de horas lectivas.

Los campos que no están presentes en los XML no se inventan. El archivo `cursos.xml` se utiliza como fuente auxiliar y no se confunde con información de horas lectivas.

### Seudonimización y privacidad

Antes de guardar los datos, el NIA se transforma mediante SHA-256, conservando los primeros diez caracteres hexadecimales del hash. Se aplica la misma función a los identificadores presentes en Alumnos y Calificaciones para mantener la posibilidad de relacionar ambas tablas.

Este procedimiento es una seudonimización, no una garantía de anonimización irreversible. Los archivos generados excluyen los campos personales directos que no son necesarios para el análisis.

### Validación

La validación se realiza con `ingesta/validar_ingesta.py`. Se comprueba la existencia de los JSON esperados, su estructura, los campos personales detectables y las relaciones entre alumnos, calificaciones, módulos y grupos.

La relación de grupos se establece mediante `Alumnos.Grupo` y `Grupos.Codigo`. En la revisión de los cursos 2022-23 a 2025-26 se encontraron coincidencias entre los valores no vacíos de ambos campos.

En el curso 2023-24 se detectaron nueve identificadores seudonimizados en Calificaciones que no aparecen en la tabla Alumnos del mismo curso. Esta incidencia se conserva como advertencia pendiente de aclaración, sin eliminar ni modificar registros de origen.

### Limitaciones

La fuente disponible no aporta información explícita de horas lectivas, por lo que la tabla Horas se genera vacía. Antes de completar esta tabla será necesario obtener una fuente que contenga dichos datos.

La correspondencia de módulos se basa en el código de `contenidos.xml` y el campo `contenido` de `calificaciones.xml`. Las relaciones deben revisarse cuando cambien los formatos de las exportaciones.

### Evidencias

La ejecución de la ingesta y de la validación se comprueba desde el terminal integrado de VS Code. Las capturas de las ejecuciones satisfactorias se pueden incorporar como evidencia de la práctica.
