from copy import deepcopy

from dedoc.common.exceptions.structure_extractor_error import StructureExtractorError
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


def get_pattern(pattern_parameters: dict) -> AbstractPattern:
    import dedoc.structure_extractors.patterns as patterns_module

    if "name" not in pattern_parameters:
        raise StructureExtractorError(msg="Pattern parameter missing 'name'")

    supported_patterns = {pattern.name(): pattern for pattern in patterns_module.__all__}
    pattern_class = supported_patterns.get(pattern_parameters["name"])

    if pattern_class is None:
        raise StructureExtractorError(msg=f"Pattern {pattern_parameters['name']} is not found in supported patterns: {supported_patterns.keys()}")

    pattern_parameters_copy = deepcopy(pattern_parameters)
    pattern_parameters_copy.pop("name")
    try:
        pattern = pattern_class(**pattern_parameters_copy)
    except TypeError as e:
        raise StructureExtractorError(msg=str(e))
    return pattern
