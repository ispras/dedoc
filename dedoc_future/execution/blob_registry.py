import logging
import os
from dataclasses import replace
from multiprocessing import shared_memory

import numpy as np

from dedoc_future.abstract.blob_ref import BlobId, BlobRef, LifeTime

logger = logging.getLogger(__name__)


class BlobRegistry:

    def __init__(self, shm_manager, disk_dir: str, ram_limit_mb: int):
        self._mgr = shm_manager
        self._refs: dict[BlobId, BlobRef] = self._mgr.dict()   # id -> BlobRef (picklable)
        self._blobs = self._mgr.dict()                          # id -> shm name | None
        self._lock = self._mgr.RLock()
        self._disk_dir = disk_dir
        self._ram_limit = ram_limit_mb * 1024 * 1024
        self._ram_used = self._mgr.Value("q", 0)

    def register(self, ref: BlobRef, data) -> BlobRef:
        with self._lock:
            if ref.id in self._refs:
                raise ValueError(f"blob already registered: {ref.id}")
            self._refs[ref.id] = ref
            self._blobs[ref.id] = self._store(ref, data)
            self._ram_used.value += self._size_of(data)
        self._evict_if_needed()
        return ref

    def _store(self, ref: BlobRef, data):
        if ref.lifetime == LifeTime.persist_to_disk:
            return self._to_disk(ref, data)
        if isinstance(data, np.ndarray):
            name = f"blob_{ref.id}"
            shm = shared_memory.SharedMemory(name=name, create=True, size=data.nbytes)
            arr = np.ndarray(data.shape, dtype=data.dtype, buffer=shm.buf)
            arr[:] = data
            shm.close()
            return name
        return data

    def _to_disk(self, ref: BlobRef, data):
        path = os.path.join(self._disk_dir, f"{ref.id}.bin")
        np.save(path, data, allow_pickle=False)
        return path

    def retain(self, ref: BlobRef, n: int = 1) -> None:
        with self._lock:
            current = self._refs[ref.id]
            self._refs[ref.id] = replace(current, refcount=current.refcount + n)

    def release(self, ref: BlobRef, n: int = 1) -> None:
        with self._lock:
            current = self._refs[ref.id]
            new_count = current.refcount - n
            if new_count > 0:
                self._refs[ref.id] = replace(current, refcount=new_count)
                return
            self._refs.pop(ref.id, None)
            self._free(ref)
        self._ram_used.value -= 0                 # пересчёт после освобождения

    def _free(self, ref: BlobRef) -> None:
        name = self._blobs.pop(ref.id, None)
        if name:
            shm = shared_memory.SharedMemory(name=name)
            try:
                shm.unlink()
            finally:
                shm.close()
        disk_path = os.path.join(self._disk_dir, f"{ref.id}.bin")
        if ref.lifetime == "persist_to_disk" and os.path.exists(disk_path):
            os.remove(disk_path)

    def materialize(self, ref: BlobRef):
        with self._lock:
            name = self._blobs.get(ref.id)
        if name:
            shm = shared_memory.SharedMemory(name=name)
            try:
                return np.ndarray(ref.shape, dtype=ref.dtype, buffer=shm.buf)
            finally:
                shm.close()
        if ref.lifetime == "persist_to_disk":
            return np.load(os.path.join(self._disk_dir, f"{ref.id}.bin"))
        raise KeyError(f"blob not found: {ref.id}")

    def _evict_if_needed(self) -> None:
        if self._ram_used.value <= self._ram_limit:
            return
        with self._lock:
            for bid, name in list(self._blobs.items()):
                ref = self._refs.get(bid)
                if not ref or ref.lifetime != "persist_to_disk" or name is None:
                    continue
                data = self.materialize(ref)
                self._blobs[bid] = self._to_disk(ref, data)
                logger.warning("blob %s evicted to disk (ram limit)", bid)
                if self._ram_used.value <= self._ram_limit:
                    break

    def _size_of(self, data) -> int:
        return data.nbytes if isinstance(data, np.ndarray) else 0
