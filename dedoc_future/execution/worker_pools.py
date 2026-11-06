from __future__ import annotations

import os
import threading
from concurrent.futures import Executor, ProcessPoolExecutor, ThreadPoolExecutor

from dedoc_future.abstract import ExecMode, Resource
from dedoc_future.abstract.processor import ResourceProfile


class WorkerPools:

    def __init__(
        self,
        cpu_workers: int | None = None,
        gpu_workers: int = 1,
        *,
        pool_initializer=None,
        pool_initargs: tuple = (),
    ):
        cpu_workers = cpu_workers or max(1, (os.cpu_count() or 1) - 1)
        self._cpu_workers = cpu_workers
        self._gpu_workers = gpu_workers
        self._initializer = pool_initializer
        self._initargs = pool_initargs
        self._pools: dict[str, Executor] = {}
        self._lock = threading.Lock()

    def pool_for(self, profile: ResourceProfile) -> Executor:
        key = self._key(profile)
        with self._lock:
            pool = self._pools.get(key)
            if pool is None:
                pool = self._create(profile)
                self._pools[key] = pool
            return pool

    @staticmethod
    def _key(profile: ResourceProfile) -> str:
        if profile.resource == Resource.GPU:
            return Resource.GPU
        return f"{Resource.CPU}_{profile.concurrency}"

    def _create(self, profile: ResourceProfile) -> Executor:
        if profile.resource == Resource.GPU:
            return ThreadPoolExecutor(
                max_workers=self._gpu_workers,
                thread_name_prefix=profile.resource,
                initializer=self._initializer,
                initargs=self._initargs,
            )
        if profile.concurrency == ExecMode.THREAD:
            return ProcessPoolExecutor(
                max_workers=self._cpu_workers,
                initializer=self._initializer,
                initargs=self._initargs,
            )
        if profile.concurrency == ExecMode.PROCESS:
            return ThreadPoolExecutor(
                max_workers=self._cpu_workers,
                thread_name_prefix=profile.resource,
                initializer=self._initializer,
                initargs=self._initargs,
            )

        raise ValueError(f"Unknown resource {profile.resource} and concurrency {profile.concurrency}")

    def shutdown(self, wait: bool = True) -> None:
        with self._lock:
            pools = list(self._pools.values())
            self._pools.clear()
        for p in pools:
            p.shutdown(wait=wait)

    def __enter__(self) -> WorkerPools:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.shutdown(wait=True)
