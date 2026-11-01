# Contrato de línea de comandos — diseño v1

Comandos futuros, no disponibles todavía. El agente operará la terminal por el propietario.

```text
raceframe process INPUT [--output DEST] --model LOCAL_FILE
  [--recursive] [--mode conservative|balanced|tight]
  [--aspect original|3:2|4:5] [--margin FLOAT] [--quality INT]
  [--device cpu|mps|auto] [--config LOCAL_JSON]
raceframe report JOB_DIRECTORY [--recover]
raceframe --version
```

Defaults en plan.md. Precedencia: argumentos explícitos > archivo de configuración > defaults.
Config acepta únicamente campos conocidos; error temprano para claves, rangos o rutas inválidas.
Pesos/config/INPUT nunca URLs. process no descarga pesos. --model es obligatorio y el archivo
debe existir antes de crear trabajo. Validar carga del modelo y soporte del dispositivo antes
de iniciar exportación. El instalador/preparación de pesos queda documentado por separado.

stdout: un resumen JSON final con job_id, estado, contadores, duración y ruta de manifiesto.
stderr: progreso en español por fotografía, advertencias y errores, sin mezclar con stdout JSON.
Con error previo al trabajo, stdout contiene un objeto error sin job_id y stderr explicación.
--help es texto y --version devuelve versión. No mostrar fotografías ni metadatos privados en servicios.

Códigos: 0 completado sin errores (incluye revisión y lote vacío); 1 completado con errores;
2 parámetros/preparación inválidos; 3 fallo global de ejecución o auditoría; 130 cancelación
por SIGINT. report devuelve 0 si lectura íntegra, 1 si trabajo interrumpido o errores registrados,
2 si argumentos inválidos y 3 si no se puede leer/reconciliar con seguridad.

Destino: si se omite, hermano Raceframe_Output; crear subdirectorio job-<uuid> con exclusión.
Resolver rutas antes de comprobar identidad/contención; rechazar destino igual a entrada,
dentro de entrada recursiva o cualquier destino que pueda escribir un original del inventario.
Por petición del propietario (2026-11-01), permitir un destino anidado cuando recursive=false:
el inventario solo incluye JPEG del nivel superior y no vuelve a importar exportaciones.
No seguir enlaces a directorios y omitir archivos enlazados fuera de raíz con advertencia.
No sobrescribir salidas, inventarios ni informes de otros trabajos.

SIGINT marca cancelación cooperativa; no comenzar otra foto una vez reconocida. Puede terminar
la inferencia/escritura activa antes de cerrar diario y resumen. Si no hay espacio para el
manifiesto, informar en stderr y código 3; el diario durable facilita report --recover después.
No afirmar que SIGKILL o pérdida de energía permiten terminar limpiamente el informe.

report lee sin cargar YOLO ni requerir modelo. --recover requiere que el trabajo esté inactivo,
valida hashes de exportaciones preparadas y escribe manifest-recovered-<uuid>.json sin
sobrescribir manifest.json ni reanudar procesamiento. No se incluye reanudación automática.
