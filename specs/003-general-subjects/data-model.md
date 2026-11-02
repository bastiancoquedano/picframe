# Datos y estados

Config añade subject_category=people|animals|vehicles, selection_strategy=manual|dominant|group,
dominance_ratio>=1,01 (inicial1,5). CLI manual; ventana dominant. Huella incluye los campos nuevos.
Detection conserva class_name y añade class_id opcional; catálogo COCO válido, coordenadas orientadas.
SubjectCandidate: primary_id, member_ids, box unión, kind=individual|associated, association_ambiguous.
Selection amplía selected_id con selected_ids, subject_box, subject_kind, metrics y associations.
Registro: selected_detection_ids, subject_box, subject_kind, selection_metrics, associations.
selected_detection_id se conserva como representante. no_person se mantiene para Personas;
no_subject en otras categorías. Sin selección: miembros vacíos y caja null.
Manual elige un candidato, conservando compañeros; grupo usa unión completa. Config/categoría
cambiante invalida sesión. Exportación caché comprueba protección contra miembros registrados.

0.3.1: subject_categories opcional (tupla/lista normalizada en orden people, animals, vehicles)
prima sobre subject_category singular. active_categories expone la selección efectiva.
Interfaz inicia con todas activas vía Automático; casillas permiten cualquier subconjunto no vacío.
Candidatos con mismos member_ids se deduplican antes de puntuación/comparación; representante
persona preferente cuando forma parte de las categorías activas, independiente del orden de detección.
