"""Segmentación local de personas mediante Apple Vision y copia segura de CVPixelBuffer."""

import platform
from dataclasses import dataclass

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class VisionMaskResult:
    mask: np.ndarray
    status: str
    backend: str = "apple_vision"
    quality: str = "accurate"
    revision: int | None = None
    reason: str | None = None
    backend_version: str | None = None
    compute_device: str = "automatic"


def copy_l008_pixel_buffer(pixel_buffer, pixel_api):
    """Copia L008 a RAM propia, respetando padding por fila y lock/unlock simétricos."""
    width = pixel_api.CVPixelBufferGetWidth(pixel_buffer)
    height = pixel_api.CVPixelBufferGetHeight(pixel_buffer)
    if width <= 0 or height <= 0:
        raise ValueError("Apple Vision devolvió dimensiones de máscara inválidas")
    if pixel_api.CVPixelBufferGetPixelFormatType(pixel_buffer) != (
        pixel_api.kCVPixelFormatType_OneComponent8
    ):
        raise ValueError("Apple Vision debe devolver el formato L008")
    if pixel_api.CVPixelBufferIsPlanar(pixel_buffer):
        raise ValueError("La máscara de Vision no debe ser planar")
    stride = pixel_api.CVPixelBufferGetBytesPerRow(pixel_buffer)
    if stride < width:
        raise ValueError("Stride de la máscara menor que su ancho")
    flags = pixel_api.kCVPixelBufferLock_ReadOnly
    status = pixel_api.CVPixelBufferLockBaseAddress(pixel_buffer, flags)
    if status != pixel_api.kCVReturnSuccess:
        raise RuntimeError(f"No se pudo bloquear la máscara de Vision: {status}")
    try:
        base = pixel_api.CVPixelBufferGetBaseAddress(pixel_buffer)
        if base is None or getattr(base, "__class__", None).__name__ == "_NULL_type":
            raise ValueError("Apple Vision devolvió una máscara sin memoria CPU")
        payload = base.as_buffer(stride * height)
        return np.frombuffer(payload, dtype=np.uint8).reshape(height, stride)[:, :width].copy()
    finally:
        pixel_api.CVPixelBufferUnlockBaseAddress(pixel_buffer, flags)


def classify_person_mask(mask):
    """Un matte vacío vale sin personas; ruido con confianza insuficiente exige fallback."""
    array = np.asarray(mask)
    if array.ndim != 2 or array.dtype != np.uint8 or array.size == 0:
        raise ValueError("La máscara Vision debe ser un mapa L uint8 no vacío")
    if not np.any(array):
        return "empty", None
    foreground = array >= 128
    minimum_pixels = max(8, int(array.size * 1e-6))
    if int(foreground.sum()) < minimum_pixels:
        return "error", "low_confidence_mask"
    return "ok", None


def scale_person_mask(mask, width, height):
    """Lleva una máscara grayscale al canvas orientado, escalando X e Y por separado."""
    array = np.asarray(mask)
    if array.ndim != 2 or array.dtype != np.uint8 or array.size == 0:
        raise ValueError("La máscara Vision debe ser un mapa L uint8 no vacío")
    if width <= 0 or height <= 0:
        raise ValueError("Dimensiones inválidas del canvas Vision")
    if array.shape == (height, width):
        return array.copy()
    with Image.fromarray(array) as source:
        with source.resize((width, height), resample=Image.Resampling.BILINEAR) as resized:
            return np.asarray(resized, dtype=np.uint8).copy()


class VisionPersonSegmenter:
    """Wrapper creado por imagen para que autorelease y CVPixelBuffer vivan lo mínimo posible."""

    def __init__(self, quality="accurate"):
        if quality not in {"accurate", "balanced", "fast"}:
            raise ValueError("La calidad de segmentación no es válida")
        self.quality = quality
        self.version = platform.mac_ver()[0]

    @staticmethod
    def available():
        try:
            import objc  # noqa: F401
            import Quartz  # noqa: F401
            import Vision  # noqa: F401
        except ImportError:
            return False
        return True

    def segment(self, image):
        if image.mode != "RGB":
            raise ValueError("Vision requiere un JPEG orientado en RGB")
        try:
            import objc
            import Quartz
            import Vision
        except ImportError as exc:
            raise RuntimeError("Apple Vision requiere el extra local watermark-vision") from exc

        width, height = image.size
        data = bytes(image.tobytes())
        with objc.autorelease_pool():
            color_space = Quartz.CGColorSpaceCreateWithName(Quartz.kCGColorSpaceSRGB)
            provider = Quartz.CGDataProviderCreateWithData(None, data, len(data), None)
            cg_image = Quartz.CGImageCreate(
                width,
                height,
                8,
                24,
                width * 3,
                color_space,
                Quartz.kCGImageAlphaNone,
                provider,
                None,
                False,
                Quartz.kCGRenderingIntentDefault,
            )
            if cg_image is None:
                raise RuntimeError("No se pudo crear el buffer orientado para Apple Vision")
            request_handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
                cg_image, {}
            )
            request = Vision.VNGeneratePersonSegmentationRequest.alloc().initWithCompletionHandler_(
                None
            )
            request.setQualityLevel_(
                {
                    "accurate": Vision.VNGeneratePersonSegmentationRequestQualityLevelAccurate,
                    "balanced": Vision.VNGeneratePersonSegmentationRequestQualityLevelBalanced,
                    "fast": Vision.VNGeneratePersonSegmentationRequestQualityLevelFast,
                }[self.quality]
            )
            request.setOutputPixelFormat_(Quartz.kCVPixelFormatType_OneComponent8)
            # On-device Vision may otherwise select the Neural Engine. Pinning the
            # supported CPU device avoids backend-plan failures on some macOS builds.
            devices, _ = request.supportedComputeStageDevicesAndReturnError_(None)
            compute_device = "automatic"
            if devices is not None:
                main_devices = devices.get(Vision.VNComputeStageMain, ())
                cpu = next(
                    (device for device in main_devices if "CPU" in device.__class__.__name__),
                    None,
                )
                if cpu is not None:
                    request.setComputeDevice_forComputeStage_(cpu, Vision.VNComputeStageMain)
                    compute_device = "cpu"
            succeeded, error = request_handler.performRequests_error_([request], None)
            if not succeeded:
                raise RuntimeError(f"Falló la segmentación local Vision: {error}")
            observations = request.results() or ()
            if not observations:
                return VisionMaskResult(
                    np.zeros((height, width), dtype=np.uint8),
                    "empty",
                    quality=self.quality,
                    backend_version=self.version,
                    compute_device=compute_device,
                )
            observation = observations[0]
            pixel_buffer = observation.pixelBuffer()
            mask = copy_l008_pixel_buffer(pixel_buffer, Quartz)
            mask = scale_person_mask(mask, width, height)
            revision = int(request.resolvedRevision())
            status, reason = classify_person_mask(mask)
            return VisionMaskResult(
                mask,
                status,
                quality=self.quality,
                revision=revision,
                reason=reason,
                backend_version=self.version,
                compute_device=compute_device,
            )
