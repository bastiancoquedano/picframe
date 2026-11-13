"""Modelos/configuración versionables para las capas de Smart Watermark."""

from dataclasses import asdict, dataclass
from hashlib import file_digest
from pathlib import Path

from PIL import Image, UnidentifiedImageError

FALLBACK_POLICIES = {"traditional_foreground", "copy_original", "skip_image"}
ANCHORS = {
    "center",
    "top_left",
    "top_center",
    "top_right",
    "center_left",
    "center_right",
    "bottom_left",
    "bottom_center",
    "bottom_right",
}


def _sha256(path):
    with Path(path).open("rb") as handle:
        return file_digest(handle, "sha256").hexdigest()


def _finite(value, low, high):
    return type(value) in (int, float) and low <= value <= high


@dataclass(frozen=True)
class WatermarkLayer:
    asset_path: Path | str
    asset_sha256: str | None = None
    width_fraction: float = 0.65
    opacity: float = 0.30
    anchor: str = "center"
    offset_x: float = 0.0
    offset_y: float = 0.0
    repeat: bool = False
    spacing_x: float = 1.8
    spacing_y: float = 1.8

    def __post_init__(self):
        path = Path(self.asset_path).expanduser()
        object.__setattr__(self, "asset_path", path)
        if path.suffix.lower() != ".png":
            raise ValueError("La marca principal debe ser un archivo PNG")
        if self.asset_sha256 is not None and (
            not isinstance(self.asset_sha256, str)
            or len(self.asset_sha256) != 64
            or any(char not in "0123456789abcdef" for char in self.asset_sha256.lower())
        ):
            raise ValueError("Hash PNG de marca principal inválido")
        if self.asset_sha256 is not None:
            object.__setattr__(self, "asset_sha256", self.asset_sha256.lower())
        if not _finite(self.width_fraction, 0.01, 2.0):
            raise ValueError("El ancho de la marca debe estar entre 1% y 200% de la foto")
        if not _finite(self.opacity, 0.01, 1.0):
            raise ValueError("La opacidad debe estar entre 1% y 100%")
        _validate_position(self.anchor, self.offset_x, self.offset_y)
        if type(self.repeat) is not bool:
            raise ValueError("repeat debe ser booleano")
        if not _finite(self.spacing_x, 0.5, 8) or not _finite(self.spacing_y, 0.5, 8):
            raise ValueError("La separación del patrón debe estar entre 0,5 y 8 veces la marca")


@dataclass(frozen=True)
class SignatureConfig:
    enabled: bool = False
    asset_sha256: str | None = None
    kind: str = "text"
    text: str = ""
    asset_path: Path | str | None = None
    size_fraction: float = 0.035
    opacity: float = 0.9
    anchor: str = "bottom_center"
    margin_fraction: float = 0.02

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise ValueError("enabled debe ser booleano")
        if self.kind not in {"text", "png"}:
            raise ValueError("La identificación debe ser texto o PNG")
        if not _finite(self.size_fraction, 0.005, 0.5):
            raise ValueError(
                "El tamaño de la identificación debe estar entre 0,5% y 50% del lado largo"
            )
        if not _finite(self.opacity, 0.01, 1):
            raise ValueError("La opacidad de la identificación debe estar entre 1% y 100%")
        if not _finite(self.margin_fraction, 0, 0.2):
            raise ValueError("El margen debe estar entre 0% y 20%")
        _validate_position(self.anchor, 0, 0)
        if self.asset_path is not None:
            path = Path(self.asset_path).expanduser()
            object.__setattr__(self, "asset_path", path)
        if self.asset_sha256 is not None and (
            not isinstance(self.asset_sha256, str)
            or len(self.asset_sha256) != 64
            or any(char not in "0123456789abcdef" for char in self.asset_sha256.lower())
        ):
            raise ValueError("Hash PNG de identificación inválido")
        if self.asset_sha256 is not None:
            object.__setattr__(self, "asset_sha256", self.asset_sha256.lower())
        if self.enabled:
            if self.kind == "text" and (not isinstance(self.text, str) or not self.text.strip()):
                raise ValueError("Escribe el texto que se mostrará como identificación")
            if self.kind == "png" and self.asset_path is None:
                raise ValueError("Selecciona el PNG de la identificación")
            if self.kind == "png" and Path(self.asset_path).suffix.lower() != ".png":
                raise ValueError("La identificación de imagen debe ser PNG")


def _validate_position(anchor, offset_x, offset_y):
    if anchor not in ANCHORS:
        raise ValueError("Posición de marca no válida")
    if not _finite(offset_x, -1, 1) or not _finite(offset_y, -1, 1):
        raise ValueError("El desplazamiento debe estar entre −100% y 100% del lienzo")


@dataclass(frozen=True)
class WatermarkConfig:
    mode: str = "traditional"
    layers: tuple[WatermarkLayer, ...] = ()
    signature: SignatureConfig = SignatureConfig()
    quality: int = 95
    fallback_policy: str = "traditional_foreground"
    recursive: bool = False

    def __post_init__(self):
        if self.mode not in {"traditional", "smart"}:
            raise ValueError("Modo de marca de agua no válido")
        if not isinstance(self.layers, (tuple, list)) or any(
            not isinstance(layer, WatermarkLayer) for layer in self.layers
        ):
            raise ValueError("Las capas principales deben ser PNG configurados")
        object.__setattr__(self, "layers", tuple(self.layers))
        if self.mode == "smart" and len(self.layers) > 1:
            raise ValueError("Smart admite un PNG principal; la firma va en otra capa")
        if not isinstance(self.signature, SignatureConfig):
            raise ValueError("La configuración de identificación no es válida")
        if type(self.quality) is not int or not 1 <= self.quality <= 95:
            raise ValueError("La calidad JPEG debe ser un entero entre 1 y 95")
        if self.fallback_policy not in FALLBACK_POLICIES:
            raise ValueError("La política de fallback no es válida")
        if type(self.recursive) is not bool:
            raise ValueError("recursive debe ser booleano")

    def validate_for_run(self):
        if not self.layers:
            raise ValueError("Selecciona al menos una marca PNG principal")
        return validate_assets(self)


def validate_assets(config):
    paths = [layer.asset_path for layer in config.layers]
    signature = config.signature
    if signature.enabled and signature.kind == "png":
        paths.append(signature.asset_path)
    expected = [layer.asset_sha256 for layer in config.layers]
    if config.signature.enabled and config.signature.kind == "png":
        expected.append(config.signature.asset_sha256)
    for path, expected_hash in zip(paths, expected, strict=True):
        path = Path(path)
        if not path.is_file():
            raise ValueError(f"No existe la marca PNG: {path.name}")
        try:
            with Image.open(path) as image:
                if image.format != "PNG":
                    raise ValueError(f"El recurso no es PNG válido: {path.name}")
                image.verify()
            with Image.open(path) as image:
                alpha = image.convert("RGBA").getchannel("A")
                if alpha.getbbox() is None:
                    raise ValueError(f"La marca está completamente transparente: {path.name}")
                alpha.close()
            if expected_hash is not None:
                actual_hash = _sha256(path)
                if actual_hash != expected_hash:
                    raise ValueError(f"El PNG cambió desde que se guardó el preset: {path.name}")
        except (OSError, UnidentifiedImageError) as exc:
            raise ValueError(f"No se puede leer la marca PNG: {path.name}") from exc
    return tuple(paths)


def preset_to_dict(name, config):
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 80:
        raise ValueError("El preset requiere un nombre de hasta 80 caracteres")
    validate_assets(config)
    value = asdict(config)
    value["layers"] = [
        {
            **layer,
            "asset_path": str(layer["asset_path"]),
            "asset_sha256": layer["asset_sha256"] or _sha256(layer["asset_path"]),
        }
        for layer in value["layers"]
    ]
    signature_path = value["signature"]["asset_path"]
    if signature_path is not None:
        value["signature"]["asset_path"] = str(signature_path)
        if value["signature"]["kind"] == "png":
            value["signature"]["asset_sha256"] = value["signature"]["asset_sha256"] or _sha256(
                signature_path
            )
    return {"schema_version": 1, "name": name.strip(), "config": value}


def preset_from_dict(value):
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("El archivo de preset Smart Watermark no es compatible")
    name = value.get("name")
    raw = value.get("config")
    if not isinstance(name, str) or not name.strip() or not isinstance(raw, dict):
        raise ValueError("El preset no incluye nombre y configuración")
    try:
        layers = tuple(WatermarkLayer(**item) for item in raw.get("layers", ()))
        signature = SignatureConfig(**raw.get("signature", {}))
        config = WatermarkConfig(
            mode=raw.get("mode", "traditional"),
            layers=layers,
            signature=signature,
            quality=raw.get("quality", 95),
            fallback_policy=raw.get("fallback_policy", "traditional_foreground"),
            recursive=raw.get("recursive", False),
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"El preset contiene opciones no válidas: {exc}") from exc
    return name.strip(), config
