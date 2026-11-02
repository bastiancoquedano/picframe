"""Candidatos geométricos; no identifica semánticamente jinetes o ciclistas."""

from dataclasses import dataclass

from raceframe.core.categories import CATEGORIES
from raceframe.core.models import Box


@dataclass(frozen=True)
class Candidate:
    primary_id: int
    member_ids: tuple[int, ...]
    box: Box
    kind: str
    ambiguous: bool = False


def union_boxes(boxes):
    boxes = tuple(boxes)
    return Box(
        min(b.x1 for b in boxes),
        min(b.y1 for b in boxes),
        max(b.x2 for b in boxes),
        max(b.y2 for b in boxes),
    )


def possible_pair(person, partner):
    a, b = person.box, partner.box
    horizontal = max(0, min(a.x2, b.x2) - max(a.x1, b.x1))
    intersection = horizontal * max(0, min(a.y2, b.y2) - max(a.y1, b.y1))
    return (
        horizontal / min(a.width, b.width) >= 0.35
        and intersection / min(a.area, b.area) >= 0.15
        and a.center[1] < b.center[1]
        and a.y1 < b.y1 < a.y2
    )


def build_candidates(detections, config):
    people = [
        d
        for d in detections
        if d.class_name == "person" and d.confidence >= config.selection_confidence
    ]
    partners = [
        d
        for d in detections
        if d.class_name in {"bicycle", "motorcycle", "horse"}
        and d.confidence >= config.selection_confidence
    ]
    links = {}
    for person in people:
        for partner in partners:
            if possible_pair(person, partner):
                links.setdefault(person.detection_id, set()).add(partner.detection_id)
                links.setdefault(partner.detection_id, set()).add(person.detection_id)
    by_id = {d.detection_id: d for d in detections}
    candidates = []
    associations = []
    for detection in detections:
        if detection.class_name not in CATEGORIES[config.subject_category]:
            continue
        linked = sorted(links.get(detection.detection_id, ()))
        ids = tuple(sorted({detection.detection_id, *linked}))
        ambiguous = bool(linked) and (len(linked) != 1 or any(len(links[i]) != 1 for i in linked))
        kind = "associated" if linked else "individual"
        candidates.append(
            Candidate(
                detection.detection_id, ids, union_boxes(by_id[i].box for i in ids), kind, ambiguous
            )
        )
        if linked:
            associations.append(
                {
                    "member_ids": list(ids),
                    "reason": "ambiguous_geometry" if ambiguous else "unique_mutual_geometry",
                }
            )
    return candidates, associations
