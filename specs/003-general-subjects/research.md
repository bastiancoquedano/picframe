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
