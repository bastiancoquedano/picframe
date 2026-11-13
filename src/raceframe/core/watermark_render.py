"""Compositor RGBA sin Qt ni modelos; ocluye únicamente las marcas, no la fotografía."""

from math import ceil

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from raceframe.core.watermark_models import validate_assets


class WatermarkRenderer:
    def __init__(self, config):
        self.config = config
        paths = validate_assets(config)
        self.assets = {}
        for path in paths:
            key = str(path.resolve())
            if key not in self.assets:
                with Image.open(path) as image:
                    self.assets[key] = image.convert("RGBA")

    def close(self):
        for image in self.assets.values():
            image.close()
        self.assets.clear()

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()

    @staticmethod
    def _position(anchor, canvas, overlay, offset_x=0, offset_y=0, margin=0):
        width, height = canvas
        overlay_width, overlay_height = overlay
        inset_x, inset_y = margin * width, margin * height
        if anchor.endswith("left"):
            x = inset_x
        elif anchor.endswith("right"):
            x = width - overlay_width - inset_x
        else:
            x = (width - overlay_width) / 2
        if anchor.startswith("top"):
            y = inset_y
        elif anchor.startswith("bottom"):
            y = height - overlay_height - inset_y
        else:
            y = (height - overlay_height) / 2
        return round(x + offset_x * width), round(y + offset_y * height)

    @staticmethod
    def _fit(source, canvas, fraction):
        width, height = canvas
        max_width = max(1, round(width * fraction))
        max_height = max(1, round(height * fraction))
        scale = min(max_width / source.width, max_height / source.height)
        return source.resize(
            (max(1, round(source.width * scale)), max(1, round(source.height * scale))),
            Image.Resampling.LANCZOS,
        )

    @staticmethod
    def _opacity(image, opacity):
        alpha = image.getchannel("A")
        adjusted = alpha.point(lambda value: round(value * opacity))
        image.putalpha(adjusted)
        alpha.close()
        adjusted.close()

    def _main_overlay(self, canvas_size):
        overlay = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        for layer in self.config.layers:
            asset = self.assets[str(layer.asset_path.resolve())]
            stamp = self._fit(asset, canvas_size, layer.width_fraction)
            self._opacity(stamp, layer.opacity)
            if layer.repeat:
                step_x = max(1, round(stamp.width * layer.spacing_x))
                step_y = max(1, round(stamp.height * layer.spacing_y))
                columns = ceil(canvas_size[0] / step_x) + 2
                rows = ceil(canvas_size[1] / step_y) + 2
                if columns * rows > 5000:
                    stamp.close()
                    overlay.close()
                    raise ValueError("El patrón generaría más de 5.000 marcas por fotografía")
                for row in range(rows):
                    for column in range(columns):
                        center_x = column * step_x
                        center_y = row * step_y
                        position = (
                            round(center_x - stamp.width / 2),
                            round(center_y - stamp.height / 2),
                        )
                        overlay.alpha_composite(stamp, dest=position)
            else:
                position = self._position(
                    layer.anchor,
                    canvas_size,
                    stamp.size,
                    layer.offset_x,
                    layer.offset_y,
                )
                overlay.alpha_composite(stamp, dest=position)
            stamp.close()
        return overlay

    @staticmethod
    def _foreground_mask(person_mask, size):
        import numpy as np

        if person_mask is None:
            return Image.new("L", size, 0)
        values = np.asarray(person_mask)
        if values.dtype != np.uint8 or values.ndim != 2:
            raise ValueError("La máscara debe ser un mapa L uint8")
        if values.shape != (size[1], size[0]):
            raise ValueError("La máscara debe tener las dimensiones orientadas de la fotografía")
        binary = Image.fromarray(np.where(values >= 128, 255, 0).astype(np.uint8))
        # Protege un píxel alrededor de las siluetas; solo controla alfa del overlay.
        expanded = binary.filter(ImageFilter.MaxFilter(3))
        binary.close()
        return expanded

    def _draw_signature(self, result):
        signature = self.config.signature
        if not signature.enabled:
            return result
        if signature.kind == "png":
            asset = self.assets[str(signature.asset_path.resolve())]
            stamp = self._fit(asset, result.size, signature.size_fraction)
            self._opacity(stamp, signature.opacity)
            position = self._position(
                signature.anchor, result.size, stamp.size, margin=signature.margin_fraction
            )
            result.alpha_composite(stamp, dest=position)
            stamp.close()
            return result

        font_size = max(8, round(max(result.size) * signature.size_fraction))
        font = ImageFont.load_default(size=font_size)
        stroke = max(1, round(font_size / 14))
        probe = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        bbox = ImageDraw.Draw(probe).textbbox(
            (0, 0), signature.text, font=font, stroke_width=stroke
        )
        probe.close()
        width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        stamp = Image.new("RGBA", (max(1, width), max(1, height)), (0, 0, 0, 0))
        ImageDraw.Draw(stamp).text(
            (-bbox[0], -bbox[1]),
            signature.text,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=stroke,
            stroke_fill=(0, 0, 0, 255),
        )
        self._opacity(stamp, signature.opacity)
        position = self._position(
            signature.anchor, result.size, stamp.size, margin=signature.margin_fraction
        )
        result.alpha_composite(stamp, dest=position)
        stamp.close()
        return result

    def render(self, original, person_mask=None, *, include_signature=True):
        if original.mode != "RGB":
            raise ValueError("La fotografía orientada debe estar en RGB")
        source = original.convert("RGBA")
        overlay = self._main_overlay(source.size)
        marked = Image.alpha_composite(source, overlay)
        if self.config.mode == "smart":
            foreground = self._foreground_mask(person_mask, source.size)
            result = Image.composite(source, marked, foreground)
            foreground.close()
            marked.close()
        else:
            result = marked
        overlay.close()
        source.close()
        if include_signature:
            result = self._draw_signature(result)
        rgb = result.convert("RGB")
        result.close()
        return rgb
