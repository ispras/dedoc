from enum import Enum


class Scope(str, Enum):
    """
    Granularity at which processor operates.

    Attributes
    ----------
    NODE:
        processor runs once per some type of node (parallelizable across nodes)
    DOCUMENT:
        processor needs the whole document, runs after all pages are done
    """
    NODE = "node"
    DOCUMENT = "document"


class Resource(str, Enum):
    """
    Resource that processor needs for a faster work.

    Attributes
    ----------
    CPU:
        processor runs on CPU (cannot be accelerated on GPU)
    GPU:
        processor runs on GPU
    """
    CPU = "cpu"
    GPU = "gpu"


class ExecMode(str, Enum):
    """
    How a task achieves parallelism on its own - this characterizes the *task*, not the orchestrator.

    Attributes
    ----------
    PROCESS:
        the task spawns its own OS process (e.g. Tesseract OCR, Java tabby); no extra wrapper needed,
        a thread worker is enough because the real work runs in the child process (GIL is released).
    THREAD:
        the task cannot spawn its own process; on its own it runs at most in a thread. To get real
        CPU parallelism (past the GIL) the orchestrator hosts such a task inside a persistent CPU process worker.
    """
    PROCESS = "process"
    THREAD = "thread"
