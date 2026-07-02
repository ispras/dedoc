import queue
import threading
import time
from concurrent.futures import Future
from typing import Any, Callable, List


class GpuBatcher:
    """
    Single-worker dynamic batcher for one GPU page-stage.

    Many CPU workers call :meth:`submit` concurrently; one background thread collects the
    submitted payloads into a batch (up to ``max_batch`` items, waiting at most ``max_latency``
    seconds for more once the first item has arrived), runs the stage function once on the whole
    batch, and resolves each caller's future. This amortizes GPU inference across pages while
    keeping a single copy of the model weights.

    The stage function must take ``(list_of_payloads, ctx)`` and return a list of results of the
    same length and order. If it raises, every page in that batch fails individually.
    """
    _STOP = object()

    def __init__(self, fn: Callable[[List[Any], Any], List[Any]], ctx: Any = None,
                 max_batch: int = 8, max_latency: float = 0.02, logger: Any = None) -> None:
        self._fn = fn
        self._ctx = ctx
        self._max_batch = max(1, max_batch)
        self._max_latency = max(0.0, max_latency)
        self._logger = logger
        self._queue: "queue.Queue" = queue.Queue()
        self.max_observed_batch = 0  # diagnostics: largest batch actually formed
        self._thread = threading.Thread(target=self._run, name="gpu-batcher", daemon=True)
        self._thread.start()

    def submit(self, payload: Any) -> Future:
        future: Future = Future()
        self._queue.put((payload, future))
        return future

    def shutdown(self) -> None:
        self._queue.put(self._STOP)
        self._thread.join()

    def _run(self) -> None:
        while True:
            first = self._queue.get()
            if first is self._STOP:
                return
            batch = [first]
            deadline = time.monotonic() + self._max_latency
            stop_after = False
            while len(batch) < self._max_batch:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                try:
                    nxt = self._queue.get(timeout=remaining)
                except queue.Empty:
                    break
                if nxt is self._STOP:
                    stop_after = True
                    break
                batch.append(nxt)
            self._process(batch)
            if stop_after:
                return

    def _process(self, batch: List) -> None:
        payloads = [payload for payload, _ in batch]
        futures = [future for _, future in batch]
        if len(batch) > self.max_observed_batch:
            self.max_observed_batch = len(batch)
        try:
            results = self._fn(payloads, self._ctx)
            if len(results) != len(payloads):
                raise RuntimeError(f"GPU stage returned {len(results)} results for {len(payloads)} inputs")
        except Exception as error:  # whole batch failed -> propagate to each page so it becomes a warning
            if self._logger is not None:
                self._logger.warning(f"GPU batch of {len(payloads)} failed: {error}")
            for future in futures:
                future.set_exception(error)
            return
        for future, result in zip(futures, results):
            future.set_result(result)
