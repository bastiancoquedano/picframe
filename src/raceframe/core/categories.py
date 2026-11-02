"""Catálogo COCO admitido; no interpreta clases personalizadas como COCO."""

CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    4: "airplane",
    5: "bus",
    6: "train",
    7: "truck",
    8: "boat",
    14: "bird",
    15: "cat",
    16: "dog",
    17: "horse",
    18: "sheep",
    19: "cow",
    20: "elephant",
    21: "bear",
    22: "zebra",
    23: "giraffe",
}
CATEGORIES = {
    "people": {"person"},
    "animals": {CLASSES[i] for i in range(14, 24)},
    "vehicles": {CLASSES[i] for i in range(1, 9)},
}
LABELS = dict(
    zip(
        CLASSES.values(),
        (
            "Persona",
            "Bicicleta",
            "Auto",
            "Moto",
            "Avión",
            "Bus",
            "Tren",
            "Camión",
            "Embarcación",
            "Ave",
            "Gato",
            "Perro",
            "Caballo",
            "Oveja",
            "Vaca",
            "Elefante",
            "Oso",
            "Cebra",
            "Jirafa",
        ),
        strict=True,
    )
)


def target_classes(categories):
    if isinstance(categories, str):
        categories = (categories,)
    return set().union(*(CATEGORIES[category] for category in categories))


def detection_classes(categories):
    if isinstance(categories, str):
        categories = (categories,)
    names = target_classes(categories)
    if "people" in categories:
        names |= {"bicycle", "motorcycle", "horse"}
    if "animals" in categories or "vehicles" in categories:
        names.add("person")
    return [i for i, name in CLASSES.items() if name in names]


def class_label(name):
    return LABELS.get(name, name)
