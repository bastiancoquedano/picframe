# Medición de rendimiento — pendiente de un evento real

T043 permanece pendiente. El propietario reservará sus fotografías para evaluación posterior.
No hay una cifra medida de fotos/segundo ni de memoria para 2.000–3.500 fotografías reales.
Las duraciones de pruebas sintéticas no se extrapolan a un evento.

Cuando se disponga del lote, el agente registrará localmente:

- Número de fotos y distribución de dimensiones.
- Versión del sistema, CPU/MPS efectivo, modelo/hash y dependencias.
- Tiempo total, fotos/segundo, RSS máximo y errores.
- Una comparación CPU/MPS sobre el mismo conjunto, si procede.

En macOS puede usarse `/usr/bin/time -l` sobre el comando CLI; la salida con rutas/datos
privados queda fuera de Git. La arquitectura mantiene un modelo y la imagen activa;
los registros JSON sí crecen con el número de archivos y su coste debe medirse.
No se promete un límite de RAM o una mejora de velocidad sin esa medición.
