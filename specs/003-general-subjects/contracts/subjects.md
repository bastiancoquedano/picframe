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

Extensión 0.3.1: subject_categories opcional admite lista no vacía y normaliza orden/repetidos.
Si existe, prima sobre subject_category singular. CLI: --auto-subjects equivale a las tres;
--subject-categories people animals combina. Opciones de categoría mutuamente excluyentes.
Un argumento singular explícito sustituye categorías múltiples de un archivo de configuración.
Automático inicial en UI; al desactivarlo se muestran casillas. No cambiar controles entre imágenes.

FR-012 preservation gate: auto decision only. When aspect is original/equivalent, mode != tight,
and selected region plus safety margin >=2% of each frame edge remains inside with a visually
balanced size/position, use the full image and warning already_well_framed. Person uses body
height and head reference; object/association/group uses maximum normalized axis. Manual person
selection or manual crop bypasses the gate. Full-frame output follows the exact-original-byte path.

Automated gate returns false for safety-margin failure, out-of-frame boxes, nonmatching requested
aspect or tight mode. For persons, occupancy floor/max derive from target -0.20/+0.10 and position
is upper-third ±0.08 or balanced center. Other subjects use target ±0.05 and center 15–85%. The
reason code already_well_framed is present on unchanged original-byte exports.
