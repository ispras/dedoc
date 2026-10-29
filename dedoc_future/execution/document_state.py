import logging
import threading
from enum import Enum

from tdm import TalismanDocument
from tdm.abstract.datamodel import AbstractNode, AbstractNodeLink

from dedoc_future.abstract.blob_ref import NodeId
from dedoc_future.abstract.processor import ProcessorResult

StepId = str
logger = logging.getLogger(__name__)


class DepsPolicy(str, Enum):
    fail = "fail"
    cascade = "cascade"
    keep_and_warn = "keep_and_warn"


class DocumentState:
    def __init__(self, doc: TalismanDocument):
        self._doc = doc
        self._lock = threading.RLock()
        self.completed_steps: set[StepId] = set()
        self.failed_steps: set[StepId] = set()

    @property
    def doc(self) -> TalismanDocument:
        with self._lock:
            return self._doc

    def mark_failed(self, step: StepId) -> None:
        with self._lock:
            self.failed_steps.add(step)

    def apply(
        self,
        step: StepId,
        scope: frozenset[NodeId],
        result: ProcessorResult,
        *,
        on_dependency: DepsPolicy = DepsPolicy.fail,
        allow_new_nodes: bool = True,
    ) -> None:
        with self._lock:
            doc = self._doc
            updated, added, removed = self._delta(doc, result.doc)

            touched = {n.id for n in updated} | set(removed)
            foreign = touched - scope
            if foreign:
                raise ValueError(f"step {step}: touched nodes outside scope: {foreign}")
            if not allow_new_nodes:
                existing_outside = {
                    n.id for n in added
                    if n.id in doc.id2node and n.id not in scope
                }
                if existing_outside:
                    raise ValueError(
                        f"step {step}: re-added existing ids outside scope: {existing_outside}"
                    )

            affected = {n.id for n in updated} | set(removed)
            if affected:
                links_to_drop = [
                    link for link in self._all_links(doc)
                    if self._link_references(link, affected)
                ]
                if links_to_drop:
                    doc = doc.without_node_links(links_to_drop)

            if removed:
                try:
                    doc = doc.without_nodes(list(removed))
                except ValueError:
                    if on_dependency == "fail":
                        raise
                    elif on_dependency == "cascade":
                        doc = doc.without_nodes(list(removed), cascade=True)
                    else:
                        logger.warning("step %s: cannot remove %s, keeping", step, removed)
                        removed = set()

            to_put = updated + added
            if to_put:
                doc = doc.with_nodes(to_put)

            local_ids = (set(scope) | {n.id for n in added}) - set(removed)
            structure = self._extract_structure(result.doc, local_ids)
            if structure:
                doc = doc.with_structure(structure, update=True, force=True)

            links = [
                l for l in self._all_links(result.doc)
                if self._link_within(l, local_ids)
            ]
            if links:
                doc = doc.with_node_links(links, update=True)

            self._doc = doc
            self.completed_steps.add(step)

    @staticmethod
    def _delta(
        container: TalismanDocument, result: TalismanDocument
    ) -> tuple[list[AbstractNode], list[AbstractNode], set[NodeId]]:
        old_ids = set(container.id2node)
        new_ids = set(result.id2node)
        updated = [
            result.id2node[i] for i in (old_ids & new_ids)
            if result.id2node[i] != container.id2node[i]
        ]
        removed = old_ids - new_ids
        added   = [result.id2node[i] for i in (new_ids - old_ids)]
        return updated, added, removed

    @staticmethod
    def _all_links(doc: TalismanDocument) -> list[AbstractNodeLink]:
        out: list[AbstractNodeLink] = []
        for links_of_type in doc.node_links.values():
            out.extend(links_of_type)
        return out

    @staticmethod
    def _link_references(link: AbstractNodeLink, ids: set[NodeId]) -> bool:
        return link.source.id in ids or link.target.id in ids

    @staticmethod
    def _link_within(link: AbstractNodeLink, ids: set[NodeId]) -> bool:
        return link.source.id in ids and link.target.id in ids

    @staticmethod
    def _extract_structure(
        result: TalismanDocument, local_ids: set[NodeId]
    ) -> dict[AbstractNode, list[AbstractNode]]:
        structure: dict[AbstractNode, list[AbstractNode]] = {}
        for nid in local_ids:
            node = result.id2node[nid]
            parent = result.parent(node)
            if parent is None or parent.id not in local_ids:
                continue
            children = [c for c in result.child_nodes(node) if c.id in local_ids]
            if children:
                structure[node] = children
        return structure
