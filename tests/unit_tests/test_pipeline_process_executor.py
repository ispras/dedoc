import unittest

import numpy as np

from dedoc.pipeline.executor import Handler, ProcessExecutor
from dedoc.pipeline.scheduler import Scheduler
from dedoc.pipeline.stage import Resource
from dedoc.pipeline.task import ExecMode, TaskSpec


# --- module-level toolkit builder (runs in each worker's initializer AND in the parent) ---

def _setup(_arg):
    def double(config, img):                       # CPU process task: numpy in -> numpy out (via shared memory)
        return img * 2

    def gpu_sum_batch(configs, imgs):              # GPU batched task: report the batch length back for assertions
        batch_len = len(imgs)
        return [(int(img.sum()), batch_len) for img in imgs]

    return {
        "double": Handler(process=double),
        "gpu_sum": Handler(process=None, batch_process=gpu_sum_batch),
    }


def _seed(page):
    return np.full((4, 4), page, dtype=np.int64)   # a small "page image"


# --- document-passing model: one dict flows through the stages, each augments it ---

def _doc_setup(_arg):
    def binarize(config, doc):
        return {**doc, "image": doc["image"] * 2, "binarized": True}

    def ocr(config, doc):
        return {**doc, "lines": int(doc["image"].sum())}

    def table(config, doc):
        return {**doc, "tables": int(doc["image"].max())}

    return {"binarize": Handler(binarize), "ocr": Handler(ocr), "table": Handler(table)}


def _doc_seed(page):
    return {"image": np.full((3, 3), page + 1, dtype=np.int64), "page": page}


class TestProcessExecutor(unittest.TestCase):
    def test_process_workers_shared_memory_and_gpu_batch(self):
        specs = [
            TaskSpec(name="double", process=None, resource=Resource.CPU, exec_mode=ExecMode.THREAD),
            TaskSpec(name="gpu_sum", process=None, resource=Resource.GPU, blockers=["double"], batch_size=4),
        ]
        executor = ProcessExecutor(pool_sizes={"cpu_process": 2, "thread": 1, "gpu": 1}, setup_fn=_setup)
        scheduler = Scheduler(executor=executor, gpu_batch_timeout=0.1)
        try:
            pages = list(range(6))
            result = scheduler.run(specs, pages, seed=_seed)
        finally:
            scheduler.shutdown()

        batch_lens = []
        for p in pages:
            total, batch_len = result.output("gpu_sum", p)
            self.assertEqual(total, (p * 2) * 16)   # double then sum of a 4x4 == 16 cells
            batch_lens.append(batch_len)
        self.assertEqual(result.warnings, [])
        # the GPU process worker actually batched several pages into one forward
        self.assertGreater(max(batch_lens), 1, batch_lens)

    def test_document_flows_and_augments_across_processes(self):
        specs = [
            TaskSpec(name="binarize", process=None, resource=Resource.CPU, exec_mode=ExecMode.THREAD),
            TaskSpec(name="ocr", process=None, resource=Resource.CPU, exec_mode=ExecMode.THREAD, blockers=["binarize"]),
            TaskSpec(name="table", process=None, resource=Resource.CPU, exec_mode=ExecMode.THREAD, blockers=["binarize"]),
        ]
        executor = ProcessExecutor(pool_sizes={"cpu_process": 3}, setup_fn=_doc_setup)
        scheduler = Scheduler(executor=executor)
        try:
            pages = list(range(4))
            result = scheduler.run(specs, pages, seed=_doc_seed)
        finally:
            scheduler.shutdown()

        for p in pages:
            binarized_value = (p + 1) * 2
            ocr_doc = result.output("ocr", p)
            table_doc = result.output("table", p)
            self.assertTrue(ocr_doc["binarized"])                 # augmentation inherited from the blocker
            self.assertEqual(ocr_doc["page"], p)                  # original seed field preserved
            self.assertEqual(ocr_doc["lines"], binarized_value * 9)   # 3x3 sum of the shared-memory image
            self.assertEqual(table_doc["tables"], binarized_value)    # max of the same image (sibling branch)


if __name__ == "__main__":
    unittest.main()
