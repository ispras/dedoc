class PdfTxtlayerParameters:

    def __init__(self, is_correct_text_layer: bool, is_first_page_correct: bool) -> None:
        super().__init__()
        self.is_correct_text_layer = is_correct_text_layer
        self.is_first_page_correct = is_first_page_correct
