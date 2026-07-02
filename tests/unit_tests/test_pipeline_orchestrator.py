import threading
import time
import unittest

from dedoc.pipeline import DocState, Orchestrator, Resource, Stage
from dedoc.pipeline.stage import Scope


class TestPipelineOrchestrator(unittest.TestCase):
    def test_chain_correctness_and_order(self) -> None:
        orchestrator = Orchestrator(cpu_workers=4, gpu_max_batch=8, gpu_max_latency=0.02)
        page_stages = [
            Stage("x10", lambda p, ctx: p * 10, resource=Resource.CPU),
            Stage("gpu_plus1", lambda batch, ctx: [x + 1 for x in batch], resource=Resource.GPU),
            Stage("x2", lambda p, ctx: p * 2, resource=Resource.CPU),
        ]
        n = 50
        state = orchestrator.run(pages=range(n), page_stages=page_stages)
        self.assertEqual(state.pages, [((i * 10) + 1) * 2 for i in range(n)])
        self.assertEqual(state.warnings, [])

    def test_gpu_batch_decoupled_from_cpu_workers(self) -> None:
        ctx = {"sizes": [], "lock": threading.Lock()}

        def gpu_fn(batch: list, ctx: dict) -> list:
            with ctx["lock"]:
                ctx["sizes"].append(len(batch))
            return [x + 1 for x in batch]

        def slow_pre(p: int, ctx: dict) -> int:
            time.sleep(0.003)
            return p

        orchestrator = Orchestrator(cpu_workers=2, gpu_max_batch=32, gpu_max_latency=0.1, max_inflight=64)
        page_stages = [Stage("slow_pre", slow_pre, resource=Resource.CPU), Stage("gpu", gpu_fn, resource=Resource.GPU)]
        state = orchestrator.run(pages=range(60), page_stages=page_stages, ctx=ctx)
        self.assertEqual(state.pages, [i + 1 for i in range(60)])
        # only 2 CPU workers, yet batches far exceed 2 -> a page does not hold a worker while parked at the GPU
        self.assertGreater(max(ctx["sizes"]), 2, f"observed GPU batch sizes: {ctx['sizes']}")

    def test_failed_page_becomes_warning(self) -> None:
        def maybe_fail(p: int, ctx: object) -> int:
            if p == 7:
                raise ValueError("boom")
            return p

        orchestrator = Orchestrator(cpu_workers=4)
        state = orchestrator.run(pages=range(10), page_stages=[Stage("maybe_fail", maybe_fail)])
        self.assertIsNone(state.pages[7])
        self.assertEqual([p for i, p in enumerate(state.pages) if i != 7], [i for i in range(10) if i != 7])
        self.assertEqual(len(state.warnings), 1)
        self.assertIn("page 7 failed", state.warnings[0])
        self.assertIn("ValueError", state.warnings[0])

    def test_gpu_batch_failure_marks_those_pages(self) -> None:
        def gpu_fail(batch: list, ctx: object) -> list:
            raise RuntimeError("gpu down")

        orchestrator = Orchestrator(cpu_workers=2, gpu_max_batch=8, gpu_max_latency=0.02)
        state = orchestrator.run(pages=range(5), page_stages=[Stage("gpu", gpu_fail, resource=Resource.GPU)])
        self.assertTrue(all(p is None for p in state.pages))
        self.assertEqual(len(state.warnings), 5)

    def test_document_barrier_runs_after_pages(self) -> None:
        def sum_pages(state: DocState) -> DocState:
            state.data["sum"] = sum(p for p in state.pages if p is not None)
            return state

        orchestrator = Orchestrator(cpu_workers=4)
        page_stages = [Stage("identity", lambda p, ctx: p)]
        doc_stages = [Stage("sum", sum_pages, scope=Scope.DOCUMENT)]
        state = orchestrator.run(pages=range(10), page_stages=page_stages, doc_stages=doc_stages)
        self.assertEqual(state.data["sum"], sum(range(10)))

    def test_optional_stage_toggled_by_ctx(self) -> None:
        page_stages = [
            Stage("x2", lambda p, ctx: p * 2),
            Stage("x100", lambda p, ctx: p * 100, optional=True, enabled=lambda ctx: ctx.get("use_x100", False)),
        ]
        orchestrator = Orchestrator(cpu_workers=2)
        off = orchestrator.run(pages=range(5), page_stages=page_stages, ctx={"use_x100": False})
        self.assertEqual(off.pages, [i * 2 for i in range(5)])
        on = orchestrator.run(pages=range(5), page_stages=page_stages, ctx={"use_x100": True})
        self.assertEqual(on.pages, [i * 2 * 100 for i in range(5)])

    def test_empty_document(self) -> None:
        orchestrator = Orchestrator(cpu_workers=2)
        state = orchestrator.run(pages=[], page_stages=[Stage("identity", lambda p, ctx: p)])
        self.assertEqual(state.pages, [])
        self.assertEqual(state.warnings, [])


if __name__ == "__main__":
    unittest.main()
