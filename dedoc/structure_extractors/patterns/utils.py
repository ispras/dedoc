from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


def get_pattern(pattern_parameters: dict) -> AbstractPattern:
    import dedoc.structure_extractors.patterns as patterns_module

    assert isinstance(pattern_parameters, dict)
    assert "name" in pattern_parameters, "Pattern parameter missing 'name'"
    assert "line_type" in pattern_parameters, "Pattern parameter missing 'line_type'"
    assert "level_1" in pattern_parameters, "Pattern parameter missing 'level_1'"

    supported_patterns = {pattern.name: pattern for pattern in patterns_module.__all__}
    pattern_class = supported_patterns.get(pattern_parameters["name"])
    if pattern_class is None:
        raise ValueError(f"Pattern {pattern_parameters['name']} is not found in supported patterns: {supported_patterns.keys()}")

    pattern = pattern_class(**pattern_parameters)
    return pattern
