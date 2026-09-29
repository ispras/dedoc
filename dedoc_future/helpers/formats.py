from dedoc_future.datamodel.nodes.file import FileNode


def format_suits(node: FileNode, extensions: set[str], mimes: set[str]) -> bool:
    if node.metadata.extension and node.metadata.extension.lower() in extensions:
        return True

    if node.metadata.mime and node.metadata.mime in mimes:
        return True

    return False
