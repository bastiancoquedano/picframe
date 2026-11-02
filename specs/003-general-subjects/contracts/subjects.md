# Contratos CLI/UI/manifiesto

Opciones CLI: --subject-category people|animals|vehicles; --selection-strategy manual|dominant|group;
--dominance-ratio FLOAT. Aliases picframe/raceframe y picframe-gui/raceframe-gui.
UI: categoría, estrategia y ventaja mínima (opciones avanzadas). Cambios invalidan análisis.
Etiquetas de clase españolas y cajas de todos los miembros elegidos; filtro de revisión existente.

Manifiesto v1 conserva campos y lectura histórica; extensión aditiva documentada:
selected_detection_ids: lista de enteros, subject_box: xyxy|null, subject_kind: individual|associated|group|null,
selection_metrics: objeto (ratio requerido/observado, candidatos), associations: lista de miembros/razón.
selected_detection_id es representante compatible, no sustituye a la lista completa de miembros.
selection_status añade no_subject; esquema admite no_person anterior. Sin modificar resultados previos.
Head_reference solo detection_top para persona individual; null para resto. Crop contiene margen y
unión de todos los miembros. Caché y corrección manual/exportada conservan lista/caja auditables.
Selección dudosa exporta copia original verificada por bytes; ningún recorte parcial se publica.
