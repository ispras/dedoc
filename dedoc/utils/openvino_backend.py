"""Optional OpenVINO CPU inference backend, shared by the pipeline's neural stages.

On an Intel CPU OpenVINO is markedly faster than both torch and onnxruntime for these models -- measured single-thread:
the RT-DETR layout transformer 1961 ms (torch) / 2018 ms (onnxruntime) -> 1453 ms (OpenVINO, 1.35x), and the
orientation EfficientNet 633 ms (onnxruntime) -> 419 ms (OpenVINO, 1.51x) -- because OpenVINO fuses the graph more
aggressively for its own CPU. It reads the same exported ONNX graph the onnxruntime path already produces.

Everything here degrades gracefully: if the ``openvino`` package is absent or a model fails to compile, the callers
fall back to their onnxruntime / torch path. Compilation is single-thread + latency-hinted to match one pipeline
worker (the pipeline gets parallelism from the worker processes, not from intra-op threads).
"""
import logging
import os
import time
from typing import Callable, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

_CORE = None


def export_once(onnx_path: str, export_fn: Callable[[str], None]) -> str:
    """Ensure ``onnx_path`` exists, running the (heavy) export at most once across concurrent processes.

    A lock file guards the export so only ONE worker loads the torch model and exports; the others wait for the
    finished graph to appear. Without this, all N pipeline workers would load the ~230 MB model simultaneously on the
    first run (no cached ONNX yet) and can exhaust memory. ``export_fn(onnx_path)`` must write the file atomically.
    """
    if os.path.isfile(onnx_path):
        return onnx_path
    lock = onnx_path + ".export.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)  # atomic winner election
        os.close(fd)
    except FileExistsError:
        for _ in range(1800):  # another worker is exporting -> wait up to ~3 min for the graph
            time.sleep(0.1)
            if os.path.isfile(onnx_path):
                return onnx_path
        return onnx_path  # timed out; caller handles a still-missing file via its own fallback
    try:
        if not os.path.isfile(onnx_path):
            export_fn(onnx_path)
    finally:
        try:
            os.remove(lock)
        except OSError:
            pass
    return onnx_path


def openvino_available() -> bool:
    """Whether the optional ``openvino`` package can be imported (cheap check, no compilation).

    ``DEDOC_NO_OV=1`` forces this off (escape hatch: fall back to onnxruntime/torch without uninstalling openvino).
    """
    if os.environ.get("DEDOC_NO_OV") == "1":
        return False
    try:
        import openvino  # noqa: F401
        return True
    except Exception:
        return False


def compile_cpu_model(onnx_path: str) -> Optional[Callable[[Dict[str, np.ndarray]], List[np.ndarray]]]:
    """Compile an ONNX model for single-thread CPU inference via OpenVINO.

    Returns a callable ``{input_name: ndarray} -> [ndarray, ...]`` (outputs in graph order), or ``None`` if OpenVINO
    is unavailable or the model cannot be compiled -- in which case the caller uses its own fallback backend.
    """
    global _CORE
    try:
        import openvino
    except Exception:
        return None
    try:
        if _CORE is None:
            _CORE = openvino.Core()
        # The NN stages run in ONE dedicated pool worker (see build_specs), so OpenVINO gets all cores to parallelize
        # the batched forward (~5.5x on this machine; a single batched inference, and the OMP/BLAS caps set for the
        # CPU-OCR workers do not apply -- OpenVINO uses its own TBB pool). That worker is the pipeline bottleneck (the
        # CPU workers wait on it), so giving it every core beats leaving some idle -- measured 45.1 s vs 48.5 s on a
        # 40-page slice, and the full 297-page doc 315.6 -> 268.3 s vs the onnxruntime/torch baseline. Its bursts
        # interleave with the OCR workers via the OS scheduler; DEDOC_OV_THREADS tunes it down if OCR-bound.
        threads = int(os.environ.get("DEDOC_OV_THREADS", str(os.cpu_count() or 1)))
        compiled = _CORE.compile_model(_CORE.read_model(onnx_path), "CPU",
                                       {"INFERENCE_NUM_THREADS": threads, "PERFORMANCE_HINT": "LATENCY"})
    except Exception as e:
        logger.warning(f"OpenVINO CPU compile failed for {onnx_path} ({e}); falling back")
        return None

    outputs = list(compiled.outputs)

    def run(feed: Dict[str, np.ndarray]) -> List[np.ndarray]:
        result = compiled(feed)
        return [result[o] for o in outputs]

    return run
