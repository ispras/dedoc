from dedoc.structure_extractors.feature_extractors.list_features.prefix.dotted_prefix import DottedPrefix


def get_dotted_item_depth(text: str) -> int:
    match = DottedPrefix.regexp.match(text)
    if match:
        prefix = DottedPrefix(match.group().strip(), indent=0)
        return len(prefix.numbers)
    else:
        return -1
