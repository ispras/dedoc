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

        for note in xml.find_all(f"w:{key}"):
            note_id = note.get("w:id")
            note_text = " ".join(t.text for t in note.find_all("w:t") if t.text)
            author = note.get("w:author")
            note_text = f"{author}: {note_text}" if author else note_text
            if note_id and note_text:
                self.id2note[note_id] = note_text

    def get_notes(self, xml: Tag) -> List[str]:
        notes_xml = xml.find_all(f"w:{self.key}Reference")
        notes = []
        for note in notes_xml:
            note_id = note.get("w:id")
            if note_id in self.id2note:
                notes.append(self.id2note[note_id])
        return notes
