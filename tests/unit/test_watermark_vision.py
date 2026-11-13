import sys

import numpy as np
import pytest

from raceframe.watermark.vision import (
    classify_person_mask,
    copy_l008_pixel_buffer,
    scale_person_mask,
)


class Buffer:
    def __init__(self):
        self.address = b"\x10\x20\xfe\xfe\x30\x40\xfd\xfd"

    def as_buffer(self, size):
        assert size == 8
        return self.address


class PixelAPI:
    kCVPixelFormatType_OneComponent8 = 99
    kCVPixelBufferLock_ReadOnly = 7
    kCVReturnSuccess = 0

    def __init__(self, *, lock_status=0, pixel_format=99):
        self.lock_status = lock_status
        self.pixel_format = pixel_format
        self.flags = []
        self.buffer = Buffer()

    def CVPixelBufferGetWidth(self, buffer):
        return 2

    def CVPixelBufferGetHeight(self, buffer):
        return 2

    def CVPixelBufferGetBytesPerRow(self, buffer):
        return 4

    def CVPixelBufferGetPixelFormatType(self, buffer):
        return self.pixel_format

    def CVPixelBufferIsPlanar(self, buffer):
        return False

    def CVPixelBufferLockBaseAddress(self, buffer, flags):
        self.flags.append(("lock", flags))
        return self.lock_status

    def CVPixelBufferGetBaseAddress(self, buffer):
        return self.buffer

    def CVPixelBufferUnlockBaseAddress(self, buffer, flags):
        self.flags.append(("unlock", flags))
        return 0


def test_copy_l008_respects_stride_and_unlocks_with_same_flags():
    api = PixelAPI()
    mask = copy_l008_pixel_buffer(object(), api)
    assert mask.dtype == np.uint8
    assert mask.shape == (2, 2)
    assert mask.tolist() == [[16, 32], [48, 64]]
    assert api.flags == [("lock", 7), ("unlock", 7)]


def test_copy_l008_rejects_format_before_lock():
    api = PixelAPI(pixel_format=0)
    with pytest.raises(ValueError, match="L008"):
        copy_l008_pixel_buffer(object(), api)
    assert api.flags == []


def test_copy_l008_unlocks_after_read_error():
    class BrokenBuffer(Buffer):
        def as_buffer(self, size):
            raise RuntimeError("unavailable")

    api = PixelAPI()
    api.buffer = BrokenBuffer()
    with pytest.raises(RuntimeError, match="unavailable"):
        copy_l008_pixel_buffer(object(), api)
    assert api.flags == [("lock", 7), ("unlock", 7)]


def test_vision_mask_scales_each_axis_to_the_oriented_canvas():
    source = np.array([[0, 255], [64, 128]], dtype=np.uint8)
    result = scale_person_mask(source, 8, 4)
    assert result.shape == (4, 8)
    assert result.dtype == np.uint8
    assert result[0, 0] == 0
    assert result[-1, -1] == 128


@pytest.mark.real_vision
def test_real_vision_request_returns_owned_canvas_sized_mask():
    if sys.platform != "darwin":
        pytest.skip("Vision solo está disponible en macOS")
    from PIL import Image, ImageDraw

    from raceframe.watermark.vision import VisionPersonSegmenter

    image = Image.new("RGB", (160, 120), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((62, 8, 98, 44), fill="black")
    draw.rectangle((67, 43, 93, 96), fill="black")
    draw.rectangle((68, 94, 79, 118), fill="black")
    draw.rectangle((81, 94, 92, 118), fill="black")
    result = VisionPersonSegmenter().segment(image)
    assert result.mask.shape == (120, 160)
    assert result.mask.dtype == np.uint8
    assert result.status in {"ok", "empty", "error"}
    if result.status == "error":
        assert result.reason == "low_confidence_mask"
    assert result.backend == "apple_vision"
    image.close()


def test_empty_matting_means_no_people_but_low_confidence_means_failure():
    assert classify_person_mask(np.zeros((100, 100), dtype=np.uint8)) == ("empty", None)
    low = np.full((100, 100), 20, dtype=np.uint8)
    assert classify_person_mask(low) == ("error", "low_confidence_mask")
    confident = np.zeros((100, 100), dtype=np.uint8)
    confident[:5, :5] = 220
    assert classify_person_mask(confident) == ("ok", None)
