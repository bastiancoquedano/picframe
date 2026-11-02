# Validación

Usar entorno existente con extras detector/gui/build, sin descargas de modelos.
Ejecutar ruff check y format --check; QT_QPA_PLATFORM=offscreen RACEFRAME_TEST_MODEL=models/yolo11n.pt pytest.
Probar escenas sintéticas: perro sin persona; auto+persona; persona+bici; persona+caballo;
parejas competidas; tamaño dominante lateral, empate, grupo a bordes y proporción inviable.
En UI cambiar categoría/estrategia, revisar selección manual y grupo, comprobar invalidación y
exportación íntegra con metadatos. Construir Picframe.app, ejecutar diagnóstico con red denegada.
No atribuir precisión fotográfica a cajas simuladas: evaluación del propietario sigue pendiente.
