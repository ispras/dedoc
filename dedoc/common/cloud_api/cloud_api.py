from dedoc.utils.utils import splitext_


def check_filename_length(filename: str) -> str:
    max_filename_length = 255  # posix name limitation
    if len(filename) > max_filename_length:
        name, ext = splitext_(filename)
        filename = name[:max_filename_length - len(ext)] + ext

    return filename
