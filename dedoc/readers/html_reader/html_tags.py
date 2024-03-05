class HtmlTags:
    service_tags = ["script", "style"]

    list_items = ["li", "dd", "dt"]
    block_tags = ["aside", "article", "body", "div", "blockquote", "footer", "header", "html", "main", "nav", "section", "form", *list_items]
    unordered_list = ["ul", "dl", "dir"]
    ordered_list = ["ol"]
    list_tags = unordered_list + ordered_list
    header_tags = ["h1", "h2", "h3", "h4", "h5", "h6"]

    strike_tags = ["del", "strike", "s"]
    bold_tags = ["strong", "b"]
    underlined_tags = ["ins", "u"]
    italic_tags = ["em", "i", "dfn", "var", "address"]
    subscript_tags = ["sub"]
    superscript_tags = ["sup"]
    link_tags = ["a"]

    paragraphs = ["p"] + block_tags + list_items + header_tags

    styled_tag = bold_tags + italic_tags + underlined_tags + strike_tags + superscript_tags + subscript_tags
    simple_text_tags = [
        "a", "abbr", "acronym", "applet", "area", "article", "aside", "bdi", "bdo", "big", "canvas", "caption", "center", "cite", "code", "data",
        "font", "kbd", "mark", "output", "p", "pre", "q", "samp", "small", "span", "tt", "wbr"
    ]
    text_tags = simple_text_tags + styled_tag

    table_tags = ["table"]
    table_rows = ["tr"]
    table_cells = ["td", "th"]

    special_symbol_tags = {"br": "\n"}
    available_tags = block_tags + list_tags + header_tags + text_tags + list(special_symbol_tags.keys()) + paragraphs
    available_tags = sorted(set(available_tags))
