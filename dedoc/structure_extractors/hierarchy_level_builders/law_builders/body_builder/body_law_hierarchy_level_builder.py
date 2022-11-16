from dedoc.structure_extractors.hierarchy_level_builders.law_builders.body_builder.abstract_body_hierarchy_level_builder import \
    AbstractBodyHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.structure_unit.law_structure_unit import LawStructureUnitBuilder


class BodyLawHierarchyLevelBuilder(AbstractBodyHierarchyLevelBuilder):
    document_types = ["law"]

    def __init__(self) -> None:
        super().__init__()
        self._structure_unit_builder = LawStructureUnitBuilder()

    @property
    def structure_unit_builder(self) -> LawStructureUnitBuilder:
        return self._structure_unit_builder
