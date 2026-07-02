import threading
import time
import unittest

from dedoc.pipeline.scheduler import DocResult, Scheduler, _compute_depths
from dedoc.pipeline.stage import Resource
from dedoc.pipeline.task import ExecMode, TaskSpec, TaskState


def spec(name, fn, blockers=None, resource=Resource.CPU, exec_mode=ExecMode.THREAD, batch_size=1, batch_process=None):
    return TaskSpec(name=name, process=fn, blockers=blockers or [], resource=resource,
                    exec_mode=exec_mode, batch_size=batch_size, batch_process=batch_process)


class TestPipelineScheduler(unittest.TestCase):
    def test_linear_chain_and_depths(self) -> None:
        specs = [
            spec("a", lambda c, x: x + 1),
            spec("b", lambda c, x: x * 2, blockers=["a"]),
            spec("c", lambda c, x: x + 100, blockers=["b"]),
        ]
        self.assertEqual(_compute_depths(specs), {"a": 0, "b": 1, "c": 2})

        pages = list(range(5))
        result = Scheduler().run(specs, pages, seed=lambda p: p * 10)
        for p in pages:
            self.assertEqual(result.output("c", p), ((p * 10 + 1) * 2) + 100)
        self.assertEqual(len(result.tasks), len(specs) * len(pages))
        self.assertEqual(result.warnings, [])
        # deeper task => higher priority (rush toward the end / GPU)
        self.assertGreater(result.by_id["c@p0"].priority, result.by_id["a@p0"].priority)

    def test_fanout(self) -> None:
        specs = [
            spec("prep", lambda c, x: x + 1),
            spec("u", lambda c, x: x * 2, blockers=["prep"]),
            spec("v", lambda c, x: x * 3, blockers=["prep"]),
        ]
        result = Scheduler().run(specs, [1, 2], seed=lambda p: p)
        for p in (1, 2):
            self.assertEqual(result.output("u", p), (p + 1) * 2)
            self.assertEqual(result.output("v", p), (p + 1) * 3)

    def test_failed_task_passes_input_through(self) -> None:
        def b_fn(c, x):
            if x == 21:  # page 2: seed=20 -> a=21
                raise ValueError("boom")
            return x * 2

        specs = [
            spec("a", lambda c, x: x + 1),
            spec("b", b_fn, blockers=["a"]),
            spec("c", lambda c, x: x + 100, blockers=["b"]),
        ]
        result = Scheduler().run(specs, [1, 2], seed=lambda p: p * 10)
        # page 1: normal chain
        self.assertEqual(result.output("c", 1), (11 * 2) + 100)
        # page 2: b failed -> c receives b's *input* (a's output = 21) instead of an output
        self.assertIsNone(result.output("b", 2))
        self.assertEqual(result.output("c", 2), 21 + 100)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("b@p2 failed", result.warnings[0])

    def test_gpu_batches_by_type(self) -> None:
        sizes = {"g1": [], "g2": []}
        lock = threading.Lock()

        def batched(name, factor):
            def fn(configs, inputs):
                with lock:
                    sizes[name].append(len(inputs))
                return [x * factor for x in inputs]
            return fn

        def slow_prep(c, x):
            time.sleep(0.005)
            return x + 1

        specs = [
            spec("prep", slow_prep),
            spec("g1", None, blockers=["prep"], resource=Resource.GPU, batch_size=4, batch_process=batched("g1", 10)),
            spec("g2", None, blockers=["prep"], resource=Resource.GPU, batch_size=4, batch_process=batched("g2", 100)),
        ]
        pages = list(range(8))
        result = Scheduler(pool_sizes={"cpu_process": 4, "gpu": 1}, gpu_batch_timeout=0.1).run(specs, pages, seed=lambda p: p)
        for p in pages:
            self.assertEqual(result.output("g1", p), (p + 1) * 10)
            self.assertEqual(result.output("g2", p), (p + 1) * 100)
        # batching actually happened for each type (same-type grouping)
        self.assertGreater(max(sizes["g1"]), 1, sizes)
        self.assertGreater(max(sizes["g2"]), 1, sizes)

    def test_gpu_timeout_flushes_tail(self) -> None:
        seen = []

        def fn(configs, inputs):
            seen.append(len(inputs))
            return [x * 2 for x in inputs]

        specs = [
            spec("prep", lambda c, x: x + 1),
            # batch_size never reached (only 3 pages) -> must flush via timeout / no-more-coming, not deadlock
            spec("g", None, blockers=["prep"], resource=Resource.GPU, batch_size=8, batch_process=fn),
        ]
        result = Scheduler(gpu_batch_timeout=0.05).run(specs, [1, 2, 3], seed=lambda p: p)
        for p in (1, 2, 3):
            self.assertEqual(result.output("g", p), (p + 1) * 2)
        self.assertEqual(sum(seen), 3)  # all three processed despite never filling a batch

    def test_diamond_depths(self) -> None:
        specs = [
            spec("root", lambda c, x: x),
            spec("left", lambda c, x: x, blockers=["root"]),
            spec("right", lambda c, x: x, blockers=["root"]),
            spec("join", lambda c, x: x, blockers=["left", "right"]),
        ]
        self.assertEqual(_compute_depths(specs), {"root": 0, "left": 1, "right": 1, "join": 2})

    def test_windowed_admission_bounds_inflight(self) -> None:
        events = []
        lock = threading.Lock()

        def seed(page):
            with lock:
                events.append(("seed", page))
            return page  # a root task's input; passed through the chain

        def leaf(config, x):
            with lock:
                events.append(("done", x))
            return x

        specs = [spec("a", lambda c, x: x), spec("b", leaf, blockers=["a"])]
        Scheduler(pool_sizes={"cpu_process": 4}, max_inflight_pages=1).run(specs, [0, 1, 2], seed=seed)
        # max_inflight=1 -> each page is fully processed (and only then seeded/rendered) before the next
        self.assertEqual(events, [("seed", 0), ("done", 0), ("seed", 1), ("done", 1), ("seed", 2), ("done", 2)])

    def test_multiple_blockers_input_is_dict(self) -> None:
        captured = {}

        def join_fn(c, x):
            captured["input"] = x
            return x

        specs = [
            spec("root", lambda c, x: x),
            spec("left", lambda c, x: x + 1, blockers=["root"]),
            spec("right", lambda c, x: x + 2, blockers=["root"]),
            spec("join", join_fn, blockers=["left", "right"]),
        ]
        Scheduler().run(specs, [10], seed=lambda p: p)
        self.assertEqual(captured["input"], {"left": 11, "right": 12})


if __name__ == "__main__":
    unittest.main()
