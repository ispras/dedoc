from typing import Dict, List, Optional

from bs4 import BeautifulSoup, Tag


class NoteExtractor:

    def __init__(self, xml: Optional[BeautifulSoup], key: str = "footnote") -> None:
        """
        :param xml: BeautifulSoup tree with styles
        :param key: footnote, endnote or comment
        """
        self.key = key
        self.id2note: Dict[str, str] = {}
        if not xml:
            return

        for footnote in xml.find_all(f"w:{key}"):
            footnote_id = footnote.get("w:id")
            footnote_text = " ".join(t.text for t in footnote.find_all("w:t") if t.text)
            author = footnote.get("w:author")
            footnote_text = f"{author}: {footnote_text}" if author else footnote_text
            if footnote_id and footnote_text:
                self.id2note[footnote_id] = footnote_text

    def get_notes(self, xml: Tag) -> List[str]:
        notes_xml = xml.find_all(f"w:{self.key}Reference")
        notes = []
        for note in notes_xml:
            note_id = note.get("w:id")
            if note_id in self.id2note:
                notes.append(self.id2note[note_id])
        return notes
