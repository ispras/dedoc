from dataclasses import dataclass
from enum import Enum


class LifeTime(str, Enum):
    keep = "keep"
    persist_to_disk = "persist_to_disk"
    drop_after_step = "drop_after_step"


NodeId = str
BlobId = str

@dataclass(frozen=True)
class BlobRef:
    id: BlobId
    shape: tuple[int, ...]
    dtype: str
    lifetime: LifeTime
    refcount: int
