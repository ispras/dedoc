import os
import signal
from typing import Union, List, Optional, Any


def get_full_path(path: str, file: str = __file__) -> str:
    dir_path = os.path.dirname(file)
    return os.path.join(dir_path, path)


def get_by_tree_path(tree: dict, path: Union[List[int], str]) -> dict:
    if isinstance(path, str):
        path = [int(i) for i in path.split(".")][1:]
    for child_id in path:
        tree = tree["subparagraphs"][child_id]
    return tree


class TestTimeout:
    def __init__(self, seconds: int, error_message: Optional[str] = None) -> None:
        if error_message is None:
            error_message = 'tests timed out after {}s.'.format(seconds)
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum: Any, frame: Any) -> None:
        raise Exception(self.error_message)

    def __enter__(self) -> None:
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        signal.alarm(0)
