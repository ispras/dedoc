import json

from dedoc.utils.utils import get_unique_name


def create_note(content: str, modified_time: int, created_time: int, author: str, size: int = None) -> [str, bytes]:
    filename = get_unique_name("note.json")
    note_dict = {"content": content,
                 "modified_time": modified_time,
                 "created_time": created_time,
                 "size": size if size else len(content),
                 "author": author}
    encode_data = json.dumps(note_dict).encode('utf-8')

    return filename, encode_data
