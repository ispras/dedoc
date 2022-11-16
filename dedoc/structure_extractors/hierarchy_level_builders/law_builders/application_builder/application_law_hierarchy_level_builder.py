from dedoc.structure_extractors.hierarchy_level_builders.law_builders.application_builder.abstract_application_hierarchy_level_builder import \
    AbstractApplicationHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.structure_unit.abstract_structure_unit import AbstractStructureUnit
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.structure_unit.law_structure_unit import LawStructureUnitBuilder


class ApplicationLawHierarchyLevelBuilder(AbstractApplicationHierarchyLevelBuilder):

    document_types = ["law"]

    def __init__(self) -> None:
        super().__init__()
        self._structure_unit_builder = LawStructureUnitBuilder()

    @property
    def structure_unit_builder(self) -> AbstractStructureUnit:
        return self._structure_unit_builder
