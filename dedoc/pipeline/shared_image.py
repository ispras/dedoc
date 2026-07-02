"""
Zero-copy-ish transport of numpy arrays (page images) between the scheduler process and worker
processes via ``multiprocessing.shared_memory``. Only a small handle (name + shape + dtype) is pickled
through the pool's pipe; the pixel buffer is written/read directly in shared memory.

Lifecycle (important on Windows, where a segment lives only while a handle is open):
    ref, shm = put_array(arr)     # creator keeps `shm` alive
    ... submit ref to a worker; worker calls get_array(ref) which copies out and closes its handle ...
    close(shm)                    # creator releases after the worker has finished (i.e. after result)
"""
from dataclasses import dataclass
from multiprocessing import shared_memory
from typing import Tuple

import numpy as np


@dataclass
class ShmRef:
    """Picklable handle to an array living in shared memory."""
    name: str
    shape: Tuple[int, ...]
    dtype: str


def put_array(arr: np.ndarray) -> Tuple[ShmRef, shared_memory.SharedMemory]:
    """Copy ``arr`` into a fresh shared-memory segment. Returns the handle and the SharedMemory object,
    which the creator MUST keep alive (and later ``close``) until every worker has read it."""
    arr = np.ascontiguousarray(arr)
    shm = shared_memory.SharedMemory(create=True, size=max(1, arr.nbytes))
    view = np.ndarray(arr.shape, dtype=arr.dtype, buffer=shm.buf)
    view[:] = arr[:]
    return ShmRef(name=shm.name, shape=tuple(arr.shape), dtype=str(arr.dtype)), shm


def get_array(ref: ShmRef) -> np.ndarray:
    """Open the segment named by ``ref``, copy the array out, and close the local handle."""
    shm = shared_memory.SharedMemory(name=ref.name)
    try:
        view = np.ndarray(ref.shape, dtype=np.dtype(ref.dtype), buffer=shm.buf)
        return np.array(view)  # copy so the caller is independent of the segment's lifetime
    finally:
        shm.close()


def close(shm: shared_memory.SharedMemory) -> None:
    """Release a segment held by its creator (and unlink on POSIX; unlink is a no-op on Windows)."""
    try:
        shm.close()
        shm.unlink()
    except FileNotFoundError:
        pass
    except Exception:  # noqa - best-effort cleanup, segment may already be gone
        pass
