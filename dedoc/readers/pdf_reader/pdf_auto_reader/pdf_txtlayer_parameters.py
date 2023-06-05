class PdfTxtlayerParameters:

    def __init__(self, correct_text_layout: bool, correct_first_page: bool, is_booklet: bool) -> None:
        super().__init__()
        self.correct_text_layout = correct_text_layout
        self.correct_first_page = correct_first_page
        self.is_booklet = is_booklet
