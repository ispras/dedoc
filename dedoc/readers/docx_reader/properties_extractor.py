from bs4 import BeautifulSoup


def check_if_true(value: str):
    if value == '1' or value == 'True' or value == 'true':
        return True
    return False


def change_paragraph_properties(old_properties: "BaseProperties",
                                tree: BeautifulSoup):
    """
    changes old properties indent, size, jc, spacing_before, spacing_after if they were found in tree
    :param old_properties: Paragraph
    :param tree: BeautifulSoup tree with properties
    """
    change_indent(old_properties, tree)
    change_size(old_properties, tree)
    change_jc(old_properties, tree)
    change_spacing(old_properties, tree)


def change_run_properties(old_properties: "BaseProperties",
                          tree: BeautifulSoup):
    """
    changes old properties: bold, italic, underlined, size if they were found in tree
    :param old_properties: Run
    :param tree: BeautifulSoup tree with properties
    """
    change_size(old_properties, tree)
    change_caps(old_properties, tree)
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


def change_indent(old_properties: "BaseProperties",
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


def change_size(old_properties: "BaseProperties",
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


def change_jc(old_properties: "BaseProperties",
              tree: BeautifulSoup):
    """
    changes old_properties: jc (alignment) if tag jc was found in tree
    :param old_properties: Paragraph
    :param tree: BeautifulSoup tree with properties
    """
    # alignment values: left, right, center, both
    # left is default value
    if not tree.jc:
        return
    if tree.bidi:
        try:
            if tree.bidi['w:val'] == '1' or tree.bidi['w:val'] == 'True':
                right_to_left = True
            else:
                right_to_left = False
        except KeyError:
            right_to_left = True
    else:
        right_to_left = False
    try:
        if tree.jc['w:val'] == 'both':
            old_properties.jc = 'both'
        elif tree.jc['w:val'] == 'center':
            old_properties.jc = 'center'
        elif tree.jc['w:val'] == 'right':
            old_properties.jc = 'right'
        elif tree.jc['w:val'] == 'end' and not right_to_left:
            old_properties.jc = 'right'
        elif tree.jc['w:val'] == 'start' and right_to_left:
            old_properties.jc = 'right'
    except KeyError:
        pass


def change_caps(old_properties: "BaseProperties",
                tree: BeautifulSoup):
    """
    changes old_properties: caps if tag caps was found in tree
    :param old_properties: Paragraph or Run
    :param tree: BeautifulSoup tree with properties
    """
    if not tree.caps:
        return
    try:
        if tree.caps['w:val'] == '1' or tree.caps['w:val'] == 'True' or tree.caps['w:val'] == 'true':
            old_properties.caps = True
        else:
            old_properties.caps = False
    except KeyError:
        old_properties.caps = True


def change_spacing(old_properties: "BaseProperties",
                   tree: BeautifulSoup):
    """
    changes old_properties: spacing_before, spacing_after if tag spacing was found in tree
    :param old_properties: Paragraph
    :param tree: BeautifulSoup tree with properties
    """
    # tag <spacing> may have the following attributes for spacing between paragraphs:
    # after / before (measured in twentieths of a point), ignored if afterLines or afterAutospacing are specified
    # afterAutospacing / beforeAutospacing (we set 0 if specified) if is specified, other attributes are ignored
    # afterLines / beforeLines (measured in one hundredths of a line)

    # if we have spacing after value for the previous paragraph and spacing before value for the next paragraph
    # we choose maximum between these two values
    if not tree.spacing:
        return

    before, after = 0, 0
    before_autospacing = tree.spacing.get("w:beforeAutospacing", False)
    before_autospacing = check_if_true(before_autospacing) if before_autospacing else before_autospacing

    after_autospacing = tree.spacing.get("w:afterAutospacing", False)
    after_autospacing = check_if_true(after_autospacing) if after_autospacing else after_autospacing

    if not before_autospacing:
        before_lines = tree.spacing.get("w:beforeLines", False)
        before_lines = int(before_lines) if before_lines else before_lines
        if not before_lines:
            before_tag = tree.spacing.get("w:before", False)
            before = int(before_tag) if before_tag else before
        else:
            before = before_lines

    if not after_autospacing:
        after_lines = tree.spacing.get("w:afterLines", False)
        after_lines = int(after_lines) if after_lines else after_lines
        if not after_lines:
            after_tag = tree.spacing.get("w:after", False)
            after = int(after_tag) if after_tag else after
        else:
            after = after_lines

    old_properties.spacing_before = before
    old_properties.spacing_after = after
