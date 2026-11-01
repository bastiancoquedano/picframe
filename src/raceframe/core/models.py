"""Contratos puros: coordenadas visualmente orientadas, xyxy semiabiertas."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from math import isfinite
from pathlib import Path


class SelectionStatus(StrEnum):
    SELECTED = "selected"
    AMBIGUOUS = "ambiguous"
    LOW_CONFIDENCE = "low_confidence"
    NO_PERSON = "no_person"
    NOT_ANALYZED = "not_analyzed"


class CompositionStatus(StrEnum):
    CROPPED = "cropped"
    UNCHANGED = "unchanged"
    REVIEW_REQUIRED = "review_required"


class OperationStatus(StrEnum):
    EXPORTED = "exported"
    OMITTED = "omitted"
    ERROR = "error"
    NOT_ATTEMPTED = "not_attempted"


class JobStatus(StrEnum):
    PREPARING = "preparing"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    CANCELLED = "cancelled"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


@dataclass(frozen=True)
class Box:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    @property
    def valid(self) -> bool:
        return all(isfinite(v) for v in self.as_tuple()) and self.width > 0 and self.height > 0

    def as_tuple(self) -> tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2, self.y2)

    def contains(self, other: "Box") -> bool:
        return (
            self.x1 <= other.x1
            and self.y1 <= other.y1
            and self.x2 >= other.x2
            and self.y2 >= other.y2
        )


@dataclass(frozen=True)
class Detection:
    detection_id: int
    box: Box
    confidence: float
    score: float | None = None
    factors: dict[str, float] = field(default_factory=dict)
    class_name: str = "person"
    eligible: bool = False
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class Selection:
    status: SelectionStatus
    detections: tuple[Detection, ...] = ()
    selected_id: int | None = None
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class Composition:
    status: CompositionStatus
    crop: Box
    protected: Box | None = None
    reasons: tuple[str, ...] = ()
    retained_area: float = 1.0
    retained_reference_area: float = 1.0
    margin_requested: float = 0.08
    margin_effective_pixels: tuple[float, ...] = ()
    mode: str = "conservative"
    requested_aspect: str = "original"
    effective_aspect: str = "original"


@dataclass(frozen=True)
class InputImage:
    image_id: str
    path: Path
    relative_path: str
    size_bytes: int
    mtime_ns: int
    device: int
    inode: int
    stored_size: tuple[int, int] | None = None
    oriented_size: tuple[int, int] | None = None
    source_orientation: int | None = None


@dataclass(frozen=True)
class Inventory:
    root: Path
    destination: Path
    images: tuple[InputImage, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ImageResult:
    image_id: str
    operation_status: OperationStatus
    composition: Composition | None = None
    selection: Selection | None = None
    output_path: str | None = None
    output_sha256: str | None = None
    final_dimensions: tuple[int, int] | None = None
    warnings: tuple[str, ...] = ()
    error: dict[str, str] | None = None


@dataclass
class Job:
    job_id: str
    input_root: Path
    output_root: Path
    job_directory: Path
    config: dict[str, object]
    schema_version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    finished_at: str | None = None
    runtime: dict[str, object] = field(default_factory=dict)
    summary: dict[str, int | float] = field(default_factory=dict)
    status: JobStatus = JobStatus.PREPARING
    results: list[ImageResult] = field(default_factory=list)
