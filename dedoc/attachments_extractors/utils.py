import pickle
from io import BytesIO

from dedoc.utils import get_unique_name


def create_note(content: str, modified_time: int, created_time: int, author: str, size: int = None) -> [str, bytes]:
    filename = get_unique_name("note.note.pickle")
    note_dict = {"content": content,
                 "modified_time": modified_time,
                 "created_time": created_time,
                 "size": size if size else len(content),
                 "author": author}
    stream = BytesIO()
    pickle.dump(note_dict, stream)
    return filename, stream.getbuffer()
