from bs4 import Tag


class FootnoteExtractor:

    def __init__(self, xml: Tag, key: str = "footnote") -> None:
        """
        :param xml: BeautifulSoup tree with styles
        :param key: footnote or endnote
        """
        self.id2footnote = {}
        if not xml:
            return

        for footnote in xml.find_all("w:{}".format(key)):
            footnote_id = footnote.get("w:id")
            footnote_text = " ".join(t.text for t in footnote.find_all("w:t") if t.text)
            if footnote_id and footnote_text:
                self.id2footnote[footnote_id] = footnote_text
