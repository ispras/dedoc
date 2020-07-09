import os


def get_full_path(path, file=__file__):
    dir_path = os.path.dirname(file)
    return os.path.join(dir_path, path)
