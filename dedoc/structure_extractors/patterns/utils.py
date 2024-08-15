from dedoc.common.exceptions.structure_extractor_error import StructureExtractorError
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


def get_pattern(pattern_parameters: dict) -> AbstractPattern:
    import dedoc.structure_extractors.patterns as patterns_module

    assert isinstance(pattern_parameters, dict), "Pattern configuration must be a dict"
    assert "name" in pattern_parameters, "Pattern parameter missing 'name'"

    supported_patterns = {pattern.name(): pattern for pattern in patterns_module.__all__}
    pattern_class = supported_patterns.get(pattern_parameters["name"])
    assert pattern_class is not None, f"Pattern {pattern_parameters['name']} is not found in supported patterns: {supported_patterns.keys()}"

    pattern_parameters.pop("name")
    try:
        pattern = pattern_class(**pattern_parameters)
    except TypeError as e:
        raise StructureExtractorError(msg=str(e))
    return pattern
