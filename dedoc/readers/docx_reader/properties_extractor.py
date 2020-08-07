from bs4 import BeautifulSoup


def change_properties(old_properties,
                      tree: BeautifulSoup):
    """
    changes old properties if they were found in tree
    :param old_properties: Paragraph or Raw
    :param tree: BeautifulSoup tree with properties
    """
    # size
    if tree.sz:
        try:
            old_properties.size = int(tree.sz['w:val'])
        except KeyError:
            pass
    # indent
    if tree.ind:
        indent_properties = ['firstLine', 'hanging', 'start', 'left']
        for indent_property in indent_properties:
            try:
                old_properties.indent[indent_property] = int(tree.ind['w:' + indent_property])
            except KeyError:
                pass

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
