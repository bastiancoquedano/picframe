# Investigación — Picframe

Investigación delegada de lectura, sin escritores adicionales.

- Decisión: reutilizar YOLO11n y catálogo COCO de la instalación. Animales: bird, cat, dog, horse,
  sheep, cow, elephant, bear, zebra, giraffe. Vehículos: bicycle, car, motorcycle, airplane, bus,
  train, truck, boat. Personas incluye compañeros bicycle/motorcycle/horse; otras categorías
  incluyen personas auxiliares para asociación. Validar nombres esperados del modelo antes de inferir.
  Razón: modelo ya preparado; no prometer cualquier especie/vehículo. Alternativa descartada:
  otros pesos/servicios por alcance y privacidad.
  Fuentes: https://docs.ultralytics.com/datasets/detect/coco/ y
  https://docs.ultralytics.com/modes/predict/ ; catálogo instalado confirmado.
- Decisión: entidades con miembros y caja unión, antes de puntuar tamaño. Parejas geométricas
  person+bicycle/motorcycle/horse: confianza >=selection_confidence, solapamiento relativo >=0,15,
  horizontal >=0,35 y centro humano más alto. Pareja única mutua para auto; cualquier competencia
  requiere revisión. Sin clasificación semántica de montar ni espectadores.
  Razón: proteger compañeros completos sin pose. Umbrales iniciales por probar con propietario.
- Decisión: dominante por área con ventaja mínima 1,5 y candidatos confiables; manual conserva
  puntuación centralidad/tamaño/confianza/aislamiento. Grupo une todos los candidatos confiables.
  Alternativa descartada: elegir siempre el más grande aunque sean casi iguales.
- Decisión: tercio superior solo persona individual. Objetos/grupos usan ocupación máxima en
  ancho/alto para focal larga; contexto con focal corta/ausente. Se conserva margen/resolución/aspecto.
- Decisión: marca Picframe, dist/Picframe.app, alias picframe y repo picframe. Conservar módulo
  raceframe, alias antiguos, historial, rutas de runtime existentes y checkout local para compatibilidad.
  El propietario autorizó el renombrado explícitamente; GitHub confirmó nuevo full_name.

## Estabilidad Qt/Python observada en CI 0.3.1

El runner Linux terminó con SIGSEGV durante Garbage-collecting dentro de un worker al cargar
una imagen del lote mixto. Inferencia de causa: ciclos de envolturas Qt recolectados por el hilo
que asigna memoria, incompatible con afinidad GUI. No fue un fallo de aserción de selección.
Decisión: mientras vive la interfaz, desactivar solo recolección automática de ciclos y ejecutar
gc.collect mediante QTimer del hilo GUI cada 2 s. Conteo de referencias sigue activo; al salir se
restaura política anterior. CLI no cambia. No sustituye deleteLater ni cancelación cooperativa.
Prueba crea 3.000 ciclos en worker y comprueba destrucción en hilo GUI.
Fuentes oficiales: https://doc.qt.io/qtforpython-6/PySide6/QtCore/QObject.html y
https://docs.python.org/3.11/library/gc.html . Confirmar con nueva ejecución Linux y bundle local.
