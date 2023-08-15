from dedoc.structure_extractors.hierarchy_level_builders.law_builders.body_builder.abstract_body_hierarchy_level_builder import \
    AbstractBodyHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.structure_unit.foiv_structure_unit import FoivStructureUnitBuilder
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_item_with_bracket, regexps_subitem


class BodyFoivHierarchyLevelBuilder(AbstractBodyHierarchyLevelBuilder):
    document_types = ["foiv"]
    regexps_item = AbstractBodyHierarchyLevelBuilder.regexps_part
    regexps_subitem_with_char = regexps_subitem
    regexps_subitem_with_number = regexps_item_with_bracket

    def __init__(self) -> None:
        super().__init__()
        self._structure_unit_builder = FoivStructureUnitBuilder()

    @property
    def structure_unit_builder(self) -> FoivStructureUnitBuilder:
        return self._structure_unit_builder
