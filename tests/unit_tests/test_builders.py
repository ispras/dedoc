import unittest

from dedoc.structure_extractors.hierarchy_level_builders.header_builder.header_hierarchy_level_builder import HeaderHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.application_builder.application_foiv_hierarchy_level_builder import \
    ApplicationFoivHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.application_builder.application_law_hierarchy_level_builder import \
    ApplicationLawHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.body_builder.body_foiv_hierarchy_level_builder import \
    BodyFoivHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.body_builder.body_law_hierarchy_level_builder import \
    BodyLawHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.composition_hierarchy_level_builder import HierarchyLevelBuilderComposition


class TestBuilders(unittest.TestCase):
    builders = [HeaderHierarchyLevelBuilder(),
                BodyLawHierarchyLevelBuilder(),
                BodyFoivHierarchyLevelBuilder(),
                ApplicationLawHierarchyLevelBuilder(),
                ApplicationFoivHierarchyLevelBuilder()]
    composition_builder = HierarchyLevelBuilderComposition(builders=builders)

    def test_item(self) -> None:
        builders = self.composition_builder._get_builders(["header"], 'law')
        self.assertTrue(isinstance(builders[0], HeaderHierarchyLevelBuilder))

        builders = self.composition_builder._get_builders(["header"], 'foiv')
        self.assertTrue(isinstance(builders[0], HeaderHierarchyLevelBuilder))

        builders = self.composition_builder._get_builders(["application"], 'law')
        self.assertTrue(isinstance(builders[0], ApplicationLawHierarchyLevelBuilder))

        builders = self.composition_builder._get_builders(["body"], 'foiv')
        self.assertTrue(isinstance(builders[0], BodyFoivHierarchyLevelBuilder))
