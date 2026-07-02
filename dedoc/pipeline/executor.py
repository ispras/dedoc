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
from concurrent.futures import Future, ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import numpy as np

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


def _remote_run(name: str, is_batch: bool, configs: List[dict], inputs: List[Any]) -> List[Any]:
    """Runs inside a worker process: resolve the handler by name, read shared-memory inputs, execute."""
    handler = _TOOLKIT[name]
    real_inputs = [_unwrap(i) for i in inputs]
    if is_batch and handler.batch_process is not None:
        return list(handler.batch_process(configs, real_inputs))
    return [handler.process(c, i) for c, i in zip(configs, real_inputs)]


def _toolkit_run(toolkit: Dict[str, Handler], name: str, is_batch: bool, configs: List[dict], inputs: List[Any]) -> List[Any]:
    """In-parent (thread pool) variant for self-forking tasks: no shared memory, direct numpy."""
    handler = toolkit[name]
    if is_batch and handler.batch_process is not None:
        return list(handler.batch_process(configs, inputs))
    return [handler.process(c, i) for c, i in zip(configs, inputs)]


class ProcessExecutor:
    def __init__(self, pool_sizes: Dict[str, int], setup_fn: Callable[[Any], Dict[str, Handler]], setup_arg: Any = None,
                 gpu_setup_fn: Optional[Callable[[Any], Dict[str, Handler]]] = None, gpu_setup_arg: Any = None) -> None:
        import atexit

        self.pool_sizes = pool_sizes
        self._pools: Dict[str, Any] = {}
        self._shm_keep: Dict[Future, list] = {}
        self._is_shutdown = False
        atexit.register(self.shutdown)  # shut pools down while multiprocessing is still alive (avoids teardown noise)
        # handlers for self-forking (thread) tasks run in the parent, so build a parent-side toolkit too
        self._parent_toolkit = setup_fn(setup_arg)

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
        future = pool.submit(_remote_run, spec.name, is_batch, configs, wrapped)
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

    def shutdown(self) -> None:
        if self._is_shutdown:
            return
        self._is_shutdown = True
        for pool in self._pools.values():
            pool.shutdown(wait=True)
