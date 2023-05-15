from typing import List

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.structure_extractors.feature_extractors.list_features.prefix.dotted_prefix import DottedPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.empty_prefix import EmptyPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.prefix import LinePrefix


def get_dotted_item_depth(text: str) -> int:
    match = DottedPrefix.regexp.match(text)
    if match:
        prefix = DottedPrefix(match.group().strip(), indent=0)
        return len(prefix.numbers)
    else:
        return -1


def get_prefix(prefix_list: List[LinePrefix], line: LineWithMeta) -> LinePrefix:
    text = line.line.strip().lower()
    indent = AbstractFeatureExtractor._get_indentation(line)

    for prefix in prefix_list:
        match = prefix.regexp.match(text)
        if match:
            return prefix(match.group().strip(), indent=indent)
    return EmptyPrefix(indent=indent)
