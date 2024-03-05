from textblob import TextBlob


class TextBlobCorrector:
    def __init__(self) -> None:
        return

    def correct(self, text: str) -> str:
        return str(TextBlob(text).correct())
