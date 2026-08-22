import os
import signal
from collections import Counter
from copy import deepcopy
from typing import Any, List, Optional, Union

from dedocutils.data_structures import BBox

from dedoc.config import get_config
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.pdf_reader.data_classes.tables.location import Location


def get_full_path(path: str, file: str = __file__) -> str:
    dir_path = os.path.dirname(file)
    return os.path.join(dir_path, path)


def get_by_tree_path(tree: dict, path: Union[List[int], str]) -> dict:
    if isinstance(path, str):
        path = [int(i) for i in path.split(".")][1:]
    for child_id in path:
        tree = tree["subparagraphs"][child_id]
    return tree


def get_test_config() -> dict:
    config = deepcopy(get_config())
    return config


def create_line_by_coordinates(x_top_left: int, y_top_left: int, width: int, height: int, page: int) -> LineWithLocation:
    bbox = BBox(x_top_left=x_top_left, y_top_left=y_top_left, width=width, height=height)
    location = Location(bbox=bbox, page_number=page)
    line = LineWithLocation(line="Some text", metadata=LineMetadata(page_id=page, line_id=0), annotations=[], location=location)
    return line


class TestTimeout:
    def __init__(self, seconds: int, error_message: Optional[str] = None) -> None:
        if error_message is None:
            error_message = f"tests timed out after {seconds}s."
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum: Any, frame: Any) -> None:  # noqa
        raise Exception(self.error_message)

    def __enter__(self) -> None:
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:  # noqa
        signal.alarm(0)


def tree2linear(tree: dict) -> List[dict]:
    lines = []
    stack = [tree]
    while len(stack) > 0:
        line = stack.pop()
        lines.append(line)
        stack.extend(line["subparagraphs"])
    lines.sort(key=lambda line: (line["metadata"]["page_id"], line["metadata"]["line_id"]))
    return lines


def collect_annotation_values(root: Any, name: str) -> List[str]:
    """
    Collect annotation values of the given name from an API tree dict or a TreeNode.
    """
    values = []
    if isinstance(root, dict):
        for line in tree2linear(root):
            for annotation in line["annotations"]:
                if annotation["name"] == name:
                    values.append(annotation["value"])
        return values

    stack = [root]
    while stack:
        node = stack.pop()
        for annotation in node.annotations:
            if annotation.name == name:
                values.append(annotation.value)
        stack.extend(node.subparagraphs)
    return values


def check_object_refs(object_uids: List[str],
                      annotation_uids: List[str],
                      *,
                      require_all_linked: bool = True,
                      require_one_to_one: bool = False,
                      kind: str = "object") -> List[str]:
    """
    Compare object uids with annotation values.

    Always rejects dangling annotations (annotation without an object).
    ``require_all_linked`` also rejects objects that no annotation points to.
    ``require_one_to_one`` compares multisets and catches lost refs when several objects share a uid.
    """
    errors = []
    object_set = set(object_uids)
    annotation_set = set(annotation_uids)

    dangling = sorted(annotation_set - object_set)
    if dangling:
        errors.append(f"dangling {kind} annotations: {dangling}")

    if require_all_linked:
        orphaned = sorted(object_set - annotation_set)
        if orphaned:
            errors.append(f"unlinked {kind}s: {orphaned}")

    if require_one_to_one:
        object_counts = Counter(object_uids)
        annotation_counts = Counter(annotation_uids)
        if object_counts != annotation_counts:
            errors.append(f"{kind} uid counts differ: objects={dict(object_counts)} annotations={dict(annotation_counts)}")

    return errors
