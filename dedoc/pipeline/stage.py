from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, List, Optional


class Scope(Enum):
    """Granularity at which a stage operates."""
    PAGE = "page"          # runs once per page (parallelizable across pages)
    DOCUMENT = "document"  # barrier: needs the whole document, runs after all pages are done


class Resource(Enum):
    """Resource class a stage needs - decides which executor runs it."""
    CPU = "cpu"
    GPU = "gpu"


@dataclass
class Stage:
    """
    A single processing step of the document pipeline.

    Function contract depends on (scope, resource):
        - PAGE + CPU: ``fn(payload, ctx) -> payload``            (transforms one page)
        - PAGE + GPU: ``fn(list[payload], ctx) -> list[result]`` (batched; same length and order)
        - DOCUMENT  : ``fn(doc_state) -> DocState | None``       (barrier over all pages; may mutate in place)

    Page stages of a document form an ordered chain (the orchestrator runs them in list order);
    document stages run sequentially after every page has finished.
    """
    name: str
    fn: Callable
    scope: Scope = Scope.PAGE
    resource: Resource = Resource.CPU
    optional: bool = False
    enabled: Optional[Callable[[Any], bool]] = None  # predicate(ctx) -> bool, consulted only when optional=True

    def is_enabled(self, ctx: Any) -> bool:
        if not self.optional or self.enabled is None:
            return True
        return bool(self.enabled(ctx))


@dataclass
class DocState:
    """Aggregated state passed to document-scope (barrier) stages and returned by the orchestrator."""
    pages: List[Any] = field(default_factory=list)   # index-aligned page payloads; None for a failed/dropped page
    warnings: List[str] = field(default_factory=list)
    ctx: Any = None
    data: dict = field(default_factory=dict)          # scratch space for document stages
