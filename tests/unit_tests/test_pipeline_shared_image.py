import time
import unittest
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import numpy as np

from dedoc.pipeline.shared_image import ShmRef, close, get_array, put_array


# --- module-level workers (must be importable for Windows spawn) ---

def _read_and_double(ref: ShmRef) -> np.ndarray:
    arr = get_array(ref)          # read the input from shared memory (parent owns the segment)
    return arr * 2                # return via the normal pickle path


def _busy(n: int) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total


def _noop(_x: int) -> int:
    return 0


class TestSharedImage(unittest.TestCase):
    def test_numpy_roundtrip_through_process(self) -> None:
        arr = (np.arange(3 * 64 * 64, dtype=np.uint8) % 251).reshape(3, 64, 64)
        ref, shm = put_array(arr)
        try:
            with ProcessPoolExecutor(max_workers=1) as pool:
                out = pool.submit(_read_and_double, ref).result()
        finally:
            close(shm)
        self.assertTrue(np.array_equal(out, arr.astype(np.uint8) * 2))
        self.assertEqual(out.shape, arr.shape)

    def test_processes_beat_threads_on_gil_bound_work(self) -> None:
        n = 5_000_000   # ~pure-Python CPU work, GIL-bound
        jobs = 8
        with ThreadPoolExecutor(max_workers=jobs) as tpool, ProcessPoolExecutor(max_workers=jobs) as ppool:
            list(tpool.map(_noop, range(jobs)))   # warm
            list(ppool.map(_noop, range(jobs)))   # warm (pay spawn cost before timing)

            t0 = time.perf_counter()
            list(tpool.map(_busy, [n] * jobs))
            thread_time = time.perf_counter() - t0

            t0 = time.perf_counter()
            list(ppool.map(_busy, [n] * jobs))
            process_time = time.perf_counter() - t0

        # GIL serializes threads; processes parallelize -> should be clearly faster on a multi-core box
        self.assertLess(process_time, thread_time / 2.0,
                        f"threads={thread_time:.2f}s processes={process_time:.2f}s (no GIL win)")


if __name__ == "__main__":
    unittest.main()
