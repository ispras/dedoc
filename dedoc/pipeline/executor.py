"""
Execution backends for the :class:`~dedoc.pipeline.scheduler.Scheduler`.

The scheduler decides *what* to run and *when*; an Executor decides *where* - in-process threads, or
persistent worker processes. Both expose ``submit(poolname, tasks) -> Future[List[output]]`` and ``shutdown()``.

- :class:`LocalExecutor` runs each task's ``spec.process`` directly on a thread pool (used by unit tests
  and any single-process use). Callables and numpy arrays are shared in-process, nothing is pickled.
- :class:`ProcessExecutor` runs pure-Python CPU tasks on **persistent process workers** (one model load per
  worker via an ``initializer``; handlers resolved by name so the model/reader is never pickled), passing
  page images through **shared memory**. ``exec_mode=PROCESS`` tasks (e.g. Tesseract, which self-forks) run
  on a thread pool in the parent; GPU tasks run on a single persistent GPU worker process, batched by type.
"""
import os
from concurrent.futures import Future, ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from multiprocessing import shared_memory
from typing import Any, Callable, Dict, List, Optional

import numpy as np

_WHERE_SEEN = set()


def _seen_where(name: str, kind: str) -> None:
    if os.environ.get("DEDOC_WHERE") and (name, kind) not in _WHERE_SEEN:
        _WHERE_SEEN.add((name, kind))
        print(f"[WHERE] stage={name:14} -> {kind:16} pid={os.getpid()}", flush=True)


# per-stage wall-time profiling (env-gated); each process dumps its accumulator to a file, the caller aggregates
import atexit  # noqa: E402
import json  # noqa: E402
import time  # noqa: E402
from collections import defaultdict  # noqa: E402

_STAGE_PROF = os.environ.get("DEDOC_STAGE_PROF")
_STAGE_TIME: Dict[str, list] = defaultdict(lambda: [0.0, 0])


def _timed(name: str, fn):
    if not _STAGE_PROF:
        return fn()
    t = time.perf_counter()
    r = fn()
    e = _STAGE_TIME[name]
    e[0] += time.perf_counter() - t
    e[1] += 1
    return r


def _dump_stage_prof() -> None:
    if _STAGE_PROF and _STAGE_TIME:
        try:
            with open(os.path.join(_STAGE_PROF, f"stageprof_{os.getpid()}.json"), "w") as f:
                json.dump({k: v for k, v in _STAGE_TIME.items()}, f)
        except Exception:
            pass


if _STAGE_PROF:
    atexit.register(_dump_stage_prof)

from dedoc.pipeline.shared_image import ShmRef, close, get_array, put_array
from dedoc.pipeline.stage import Resource


@dataclass
class Handler:
    """A named stage implementation living in a worker's toolkit."""
    process: Callable[[dict, Any], Any]
    batch_process: Optional[Callable[[List[dict], List[Any]], List[Any]]] = None


def _is_gpu(spec: Any) -> bool:
    return spec.resource == Resource.GPU


# ---------------------------------------------------------------- Local (thread) executor

def _local_run(tasks: List[Any]) -> List[Any]:
    spec = tasks[0].spec
    if len(tasks) > 1 or (_is_gpu(spec) and spec.batch_process is not None):
        if spec.batch_process is not None:
            return list(spec.batch_process([t.config for t in tasks], [t.input for t in tasks]))
        return [spec.process(t.config, t.input) for t in tasks]
    return [spec.process(tasks[0].config, tasks[0].input)]


class LocalExecutor:
    def __init__(self, pool_sizes: Dict[str, int]) -> None:
        self.pool_sizes = pool_sizes
        self._pools = {name: ThreadPoolExecutor(max_workers=size, thread_name_prefix=name) for name, size in pool_sizes.items()}

    def submit(self, poolname: str, tasks: List[Any]) -> Future:
        return self._pools[poolname].submit(_local_run, tasks)

    def shutdown(self) -> None:
        for pool in self._pools.values():
            pool.shutdown(wait=True)


# ---------------------------------------------------------------- Process executor

_TOOLKIT: Dict[str, Handler] = {}  # per-worker-process handler registry, built by the initializer


def _worker_init(setup_fn: Callable[[Any], Dict[str, Handler]], setup_arg: Any) -> None:
    global _TOOLKIT
    _TOOLKIT = setup_fn(setup_arg)


def _unwrap(value: Any) -> Any:
    """Restore shared-memory arrays. Supports a bare array/handle or a document dict of possibly-array values."""
    if isinstance(value, ShmRef):
        return get_array(value)
    if isinstance(value, dict):
        return {k: (get_array(v) if isinstance(v, ShmRef) else v) for k, v in value.items()}
    return value


def _wrap_value(value: Any):
    """Move large numpy arrays (page images) into shared memory; leave everything else untouched.
    Supports a bare array or a document dict whose values may be arrays. Returns (wrapped, [shm, ...])."""
    if isinstance(value, np.ndarray):
        ref, shm = put_array(value)
        return ref, [shm]
    if isinstance(value, dict):
        out, shms = {}, []
        for key, val in value.items():
            if isinstance(val, np.ndarray):
                ref, shm = put_array(val)
                out[key] = ref
                shms.append(shm)
            else:
                out[key] = val
        return out, shms
    return value, []


_MIN_SHM_BYTES = 1_000_000  # only LARGE arrays (page image, det preprocess) go to shared buffers; small ones pickle
_BUFS_PER_TASK = 2          # max large arrays per output (page image + detection preprocess)


def _write_output_arrays(doc: Any, buf_names: List[str], buf_size: int) -> Any:
    """In the worker: write the doc's large numpy fields (page image, detection preprocess, ...) into parent-owned
    shared buffers and replace each with a handle, so they are not pickled back through the pool pipe. One buffer
    per large field, up to the lent count; anything over the buffer size or beyond the count falls back to pickling."""
    if not isinstance(doc, dict) or not buf_names:
        return doc
    out, i = dict(doc), 0
    for key, val in doc.items():
        if i >= len(buf_names):
            break
        if isinstance(val, np.ndarray) and _MIN_SHM_BYTES < val.nbytes <= buf_size:
            arr = np.ascontiguousarray(val)
            shm = shared_memory.SharedMemory(name=buf_names[i])
            try:
                np.ndarray(arr.shape, dtype=arr.dtype, buffer=shm.buf)[:] = arr[:]
            finally:
                shm.close()  # the parent owns the buffer and keeps it alive
            out[key] = ShmRef(name=buf_names[i], shape=tuple(arr.shape), dtype=str(arr.dtype))
            i += 1
    return out


def _remote_run(name: str, is_batch: bool, configs: List[dict], inputs: List[Any],
                out_names: List[Any], buf_size: int) -> List[Any]:
    """Runs inside a worker process: read shared-memory inputs, run the handler, write output arrays into the
    parent-owned shared buffers (so large arrays never go back through the pipe). ``out_names[i]`` is the buffer
    list lent to task i."""
    handler = _TOOLKIT[name]
    _seen_where(name, "worker-process")
    real_inputs = [_unwrap(i) for i in inputs]
    if is_batch and handler.batch_process is not None:
        outputs = _timed(name, lambda: list(handler.batch_process(configs, real_inputs)))
    else:
        outputs = [_timed(name, lambda c=c, i=i: handler.process(c, i)) for c, i in zip(configs, real_inputs)]
    return [_write_output_arrays(out, bufs, buf_size) for out, bufs in zip(outputs, out_names)]


def _toolkit_run(toolkit: Dict[str, Handler], name: str, is_batch: bool, configs: List[dict], inputs: List[Any]) -> List[Any]:
    """In-parent (thread pool) variant for self-forking tasks. Inputs may reference parent-owned shared buffers."""
    handler = toolkit[name]
    _seen_where(name, "parent-thread")
    real_inputs = [_unwrap(i) for i in inputs]
    if is_batch and handler.batch_process is not None:
        return _timed(name, lambda: list(handler.batch_process(configs, real_inputs)))
    return [_timed(name, lambda c=c, i=i: handler.process(c, i)) for c, i in zip(configs, real_inputs)]


class _BufferPool:
    """Parent-owned pool of reusable shared-memory buffers for worker output images. The parent creates the
    segments (so they survive on Windows regardless of the worker), lends one per task, and takes it back when
    the scheduler frees the image."""
    def __init__(self, buf_size: int) -> None:
        self._buf_size = buf_size
        self._free: List[str] = []
        self._all: Dict[str, Any] = {}

    def acquire(self) -> str:
        if self._free:
            return self._free.pop()
        shm = shared_memory.SharedMemory(create=True, size=self._buf_size)
        self._all[shm.name] = shm
        import os as _os
        if _os.environ.get("DEDOC_BUF_PROF"):
            import sys as _sys
            print(f"BUFPOOL created buffer #{len(self._all)} ({self._buf_size//(1<<20)}MB each, total {len(self._all)*self._buf_size//(1<<20)}MB)", file=_sys.stderr, flush=True)
        return shm.name

    def release(self, name: str) -> None:
        if name in self._all and name not in self._free:
            self._free.append(name)

    def close(self) -> None:
        for shm in self._all.values():
            try:
                shm.close()
                shm.unlink()
            except Exception:  # noqa - best-effort cleanup
                pass
        self._free.clear()
        self._all.clear()


class ProcessExecutor:
    def __init__(self, pool_sizes: Dict[str, int], setup_fn: Callable[[Any], Dict[str, Handler]], setup_arg: Any = None,
                 gpu_setup_fn: Optional[Callable[[Any], Dict[str, Handler]]] = None, gpu_setup_arg: Any = None) -> None:
        import atexit

        # Cap per-worker math-library threads BEFORE the worker pools are spawned (children inherit these env vars on
        # spawn, and read them when they first import/call numpy/torch). Each worker would otherwise start a BLAS/OMP
        # thread pool sized to ALL cores: OpenBLAS alone reserves ~500 MB VMS per worker (measured 552 -> 47 MB at 1
        # thread), and ~10 workers x 16 threads oversubscribe the 16 cores 10x. The pipeline parallelizes across
        # pages/workers, so per-worker math libs must be single-threaded. setdefault so an explicit override wins.
        for _var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            os.environ.setdefault(_var, "1")

        self.pool_sizes = pool_sizes
        self._pools: Dict[str, Any] = {}
        self._shm_keep: Dict[Future, list] = {}
        self._is_shutdown = False
        atexit.register(self.shutdown)  # shut pools down while multiprocessing is still alive (avoids teardown noise)
        # handlers for self-forking (thread) tasks run in the parent, so build a parent-side toolkit too
        self._parent_toolkit = setup_fn(setup_arg)
        # Per shared buffer. Sized from the measured page-image distribution (H*W*3 @200 DPI over 2481 pages/91 docs):
        # median/p90 11.6 MB, p99 55.7 MB; the det preprocess is capped at ~8.5 MB by the 960 px downscale. 32 MB keeps
        # ~97.5% of pages (and every det preprocess) in shared memory; the ~2.5% larger pages fall back to pickling
        # (graceful, they are rare and already slow). The pool grows to ~60 buffers on a busy run, so 64 MB -> 32 MB
        # roughly halves its commit (~3.75 GB -> ~1.9 GB) with no measurable wall change. (DEDOC_BUF_MB overrides for A/B.)
        self._buf_size = int(os.environ.get("DEDOC_BUF_MB", 32)) * 1024 * 1024
        self._pool = _BufferPool(self._buf_size)
        self._out_bufs: Dict[Future, list] = {}

        if "cpu_process" in pool_sizes:
            self._pools["cpu_process"] = ProcessPoolExecutor(
                max_workers=pool_sizes["cpu_process"], initializer=_worker_init, initargs=(setup_fn, setup_arg))
        if "thread" in pool_sizes:
            self._pools["thread"] = ThreadPoolExecutor(max_workers=pool_sizes["thread"], thread_name_prefix="thread")
        if "gpu" in pool_sizes:
            gsf = gpu_setup_fn or setup_fn
            gsa = gpu_setup_arg if gpu_setup_fn is not None else setup_arg
            self._pools["gpu"] = ProcessPoolExecutor(
                max_workers=pool_sizes.get("gpu", 1), initializer=_worker_init, initargs=(gsf, gsa))

    def submit(self, poolname: str, tasks: List[Any]) -> Future:
        spec = tasks[0].spec
        is_batch = len(tasks) > 1 or _is_gpu(spec)
        configs = [t.config for t in tasks]
        inputs = [t.input for t in tasks]
        pool = self._pools[poolname]

        if isinstance(pool, ThreadPoolExecutor):  # self-forking tasks: direct, in-parent
            return pool.submit(_toolkit_run, self._parent_toolkit, spec.name, is_batch, configs, inputs)

        wrapped, shms = self._wrap_inputs(inputs)
        out_bufs = [self._pool.acquire() for _ in range(_BUFS_PER_TASK * len(tasks))]  # parent-owned output buffers
        out_names = [out_bufs[_BUFS_PER_TASK * i: _BUFS_PER_TASK * (i + 1)] for i in range(len(tasks))]
        future = pool.submit(_remote_run, spec.name, is_batch, configs, wrapped, out_names, self._buf_size)
        self._out_bufs[future] = out_bufs
        future.add_done_callback(self._release_unused_bufs)  # return the buffers the worker did not write to
        if shms:
            self._shm_keep[future] = shms
            future.add_done_callback(self._free_shms)
        return future

    @staticmethod
    def _wrap_inputs(inputs: List[Any]) -> tuple:
        wrapped, shms = [], []
        for value in inputs:
            wrapped_value, value_shms = _wrap_value(value)
            wrapped.append(wrapped_value)
            shms.extend(value_shms)
        return wrapped, shms

    def _free_shms(self, future: Future) -> None:
        for shm in self._shm_keep.pop(future, []):
            close(shm)

    def _release_unused_bufs(self, future: Future) -> None:
        acquired = self._out_bufs.pop(future, [])
        used = set()
        try:
            for doc in future.result():
                if isinstance(doc, dict):
                    used.update(v.name for v in doc.values() if isinstance(v, ShmRef))
        except Exception:  # noqa - task failed; none of its lent buffers were written
            pass
        for name in acquired:
            if name not in used:
                self._pool.release(name)

    def release_output(self, name: str) -> None:
        """Return an output buffer to the pool once the scheduler has freed a large array that lived in it."""
        self._pool.release(name)

    def shutdown(self) -> None:
        if self._is_shutdown:
            return
        self._is_shutdown = True
        for pool in self._pools.values():
            pool.shutdown(wait=True)
        self._pool.close()
