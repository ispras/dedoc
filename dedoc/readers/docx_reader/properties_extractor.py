from bs4 import BeautifulSoup


def change_paragraph_properties(old_properties,
                                tree: BeautifulSoup):
    """
    changes old properties indent, size if they were found in tree
    :param old_properties: Paragraph
    :param tree: BeautifulSoup tree with properties
    """
    change_indent(old_properties, tree)
    change_size(old_properties, tree)


def change_run_properties(old_properties,
                          tree: BeautifulSoup):
    """
    changes old properties: bold, italic, underlined, size if they were found in tree
    :param old_properties: Run
    :param tree: BeautifulSoup tree with properties
    """
    change_size(old_properties, tree)
    # bold
    if tree.b:
        try:
            if tree.b['w:val'] == '1' or tree.b['w:val'] == 'True':
                old_properties.bold = True
            else:
                old_properties.bold = False
        except KeyError:
            old_properties.bold = True

    # italic
    if tree.i:
        try:
            if tree.i['w:val'] == '1' or tree.i['w:val'] == 'True':
                old_properties.italic = True
            else:
                old_properties.italic = False
        except KeyError:
            old_properties.italic = True

    # underlined
    if tree.u:
        try:
            if tree.u['w:val'] == 'none':
                old_properties.underlined = False
            else:
                old_properties.underlined = True
        except KeyError:
            pass


def change_indent(old_properties,
                  tree: BeautifulSoup):
    """
    changes old properties: indent if it was found in tree
    :param old_properties: Paragraph
    :param tree: BeautifulSoup tree with properties
    """
    if tree.ind:
        indent_properties = ['firstLine', 'hanging', 'start', 'left']
        for indent_property in indent_properties:
            try:
                old_properties.indent[indent_property] = int(tree.ind['w:' + indent_property])
            except KeyError:
                pass


def change_size(old_properties,
                tree: BeautifulSoup):
    """
    changes old properties: size if it was found in tree
    :param old_properties: Paragraph or Run
    :param tree: BeautifulSoup tree with properties
    """
    if tree.sz:
        try:
            old_properties.size = int(tree.sz['w:val'])
        except KeyError:
            pass
