from typing import List, Optional

from dedoc.structure_extractors.hierarchy_level_builders.abstract_hierarchy_level_builder import AbstractHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.stub_hierarchy_level_builder import StubHierarchyLevelBuilder


class HierarchyLevelBuilderComposition(object):

    def __init__(self, builders: List[AbstractHierarchyLevelBuilder]) -> None:
        self.builders = builders

    def _get_builder(self, start_tag: str, document_type: str) -> Optional[AbstractHierarchyLevelBuilder]:
        for builder in self.builders:
            if builder.can_build(start_tag, document_type):
                return builder

        return None

    def _get_builders(self, start_tags: List[str], doc_types: str) -> List[AbstractHierarchyLevelBuilder]:
        builders = []
        for start_tag in start_tags:
            builder = self._get_builder(start_tag, doc_types)
            if builder is not None:
                builders.append(builder)

        return builders if builders else [StubHierarchyLevelBuilder()]
