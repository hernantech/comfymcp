"""Type definitions for ComfyUI API responses."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExecutionEventType(str, Enum):
    """Types of execution events from WebSocket."""

    STATUS = "status"
    EXECUTION_START = "execution_start"
    EXECUTION_CACHED = "execution_cached"
    EXECUTING = "executing"
    EXECUTED = "executed"
    PROGRESS = "progress"
    EXECUTION_SUCCESS = "execution_success"
    EXECUTION_ERROR = "execution_error"
    EXECUTION_INTERRUPTED = "execution_interrupted"


@dataclass
class QueueResponse:
    """Response from POST /prompt."""

    prompt_id: str
    number: int
    node_errors: dict[str, Any] = field(default_factory=dict)


@dataclass
class QueueItem:
    """A single item in the queue."""

    number: int
    prompt_id: str
    prompt: dict[str, Any]
    extra_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class QueueStatus:
    """Response from GET /queue."""

    running: list[QueueItem]
    pending: list[QueueItem]

    @property
    def queue_remaining(self) -> int:
        return len(self.running) + len(self.pending)


@dataclass
class DeviceInfo:
    """Information about a compute device."""

    name: str
    type: str
    index: int
    vram_total: int
    vram_free: int
    torch_vram_total: int
    torch_vram_free: int


@dataclass
class SystemStats:
    """Response from GET /system_stats."""

    system: dict[str, Any]
    devices: list[DeviceInfo]

    @classmethod
    def from_dict(cls, data: dict) -> "SystemStats":
        devices = [
            DeviceInfo(
                name=d.get("name", ""),
                type=d.get("type", ""),
                index=d.get("index", 0),
                vram_total=d.get("vram_total", 0),
                vram_free=d.get("vram_free", 0),
                torch_vram_total=d.get("torch_vram_total", 0),
                torch_vram_free=d.get("torch_vram_free", 0),
            )
            for d in data.get("devices", [])
        ]
        return cls(system=data.get("system", {}), devices=devices)


@dataclass
class UploadResponse:
    """Response from POST /upload/image or /upload/mask."""

    name: str
    subfolder: str
    type: str


@dataclass
class ExecutionEvent:
    """A WebSocket execution event."""

    type: ExecutionEventType
    data: dict[str, Any]
    prompt_id: str | None = None

    @classmethod
    def from_message(cls, message: dict) -> "ExecutionEvent":
        event_type = ExecutionEventType(message.get("type", "status"))
        data = message.get("data", {})
        prompt_id = data.get("prompt_id")
        return cls(type=event_type, data=data, prompt_id=prompt_id)


@dataclass
class ProgressEvent:
    """Progress update during node execution."""

    node_id: str
    prompt_id: str
    value: int
    max: int

    @property
    def percentage(self) -> float:
        if self.max == 0:
            return 0.0
        return (self.value / self.max) * 100

    @classmethod
    def from_data(cls, data: dict) -> "ProgressEvent":
        return cls(
            node_id=data.get("node", ""),
            prompt_id=data.get("prompt_id", ""),
            value=data.get("value", 0),
            max=data.get("max", 0),
        )


@dataclass
class HistoryEntry:
    """A single history entry."""

    prompt_id: str
    prompt: dict[str, Any]
    outputs: dict[str, Any]
    status: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, prompt_id: str, data: dict) -> "HistoryEntry":
        return cls(
            prompt_id=prompt_id,
            prompt=data.get("prompt", [None, {}])[1] if data.get("prompt") else {},
            outputs=data.get("outputs", {}),
            status=data.get("status"),
        )


@dataclass
class ImageInfo:
    """Information about a generated image."""

    filename: str
    subfolder: str
    type: str  # "output", "input", or "temp"

    @property
    def view_url(self) -> str:
        """Get the /view URL for this image."""
        params = f"filename={self.filename}&type={self.type}"
        if self.subfolder:
            params += f"&subfolder={self.subfolder}"
        return f"/view?{params}"


@dataclass
class ModelInfo:
    """Information about an available model."""

    name: str
    path: str


@dataclass
class NodeInputSpec:
    """Specification for a node input."""

    name: str
    type: str | list[str]  # Type name or list of options (combo)
    required: bool
    default: Any = None
    min: float | None = None
    max: float | None = None
    step: float | None = None
    multiline: bool = False
    tooltip: str | None = None


@dataclass
class NodeOutputSpec:
    """Specification for a node output."""

    name: str
    type: str
    slot: int
    is_list: bool = False
    tooltip: str | None = None


@dataclass
class NodeDef:
    """Full definition of a ComfyUI node."""

    name: str  # class_type
    display_name: str
    category: str
    description: str
    inputs: dict[str, NodeInputSpec]  # name -> spec
    outputs: list[NodeOutputSpec]
    output_node: bool = False
    deprecated: bool = False
    experimental: bool = False

    def get_output_slot(self, name: str) -> int:
        """Get the slot index for an output by name."""
        for output in self.outputs:
            if output.name == name:
                return output.slot
        raise ValueError(f"No output named '{name}'. Available: {[o.name for o in self.outputs]}")
