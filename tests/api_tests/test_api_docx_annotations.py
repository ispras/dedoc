from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiDocxAnnotations(AbstractTestApiDocReader):

    def test_example_1(self):
        result = self._send_request("annotation_docx/example_1.docx")['content']['structure']['subparagraphs']
        annotations = [subparagraph['annotations'] for subparagraph in result]

        # bold, italic, underlined
        self.assertTrue({'start': 0, 'end': 11, 'name': 'style', 'value': 'body'} in annotations[0])
        self.assertTrue({'start': 0, 'end': 12, 'name': 'italic', 'value': 'True'} in annotations[1])
        self.assertTrue({'start': 0, 'end': 10, 'name': 'bold', 'value': 'True'} in annotations[2])
        self.assertTrue({'start': 0, 'end': 16, 'name': 'underlined', 'value': 'True'} in annotations[3])
        self.assertTrue({'start': 0, 'end': 6, 'name': 'italic', 'value': 'True'} in annotations[4])
        self.assertTrue({'start': 8, 'end': 13, 'name': 'bold', 'value': 'True'} in annotations[5])
        self.assertTrue({'start': 0, 'end': 20, 'name': 'bold', 'value': 'True'} in annotations[6] and
                        {'start': 5, 'end': 20, 'name': 'underlined', 'value': 'True'} in annotations[6])
        # alignment
        self.assertTrue({'start': 0, 'end': 10, 'name': 'alignment', 'value': 'left'} in annotations[8])
        self.assertTrue({'start': 0, 'end': 14, 'name': 'alignment', 'value': 'center'} in annotations[9])
        self.assertTrue({'start': 0, 'end': 11, 'name': 'alignment', 'value': 'right'} in annotations[10])
        self.assertTrue({'start': 0, 'end': 29, 'name': 'alignment', 'value': 'both'} in annotations[11])
        # indent
        self.assertTrue({'start': 0, 'end': 12, 'name': 'indentation', 'value': '0'} in annotations[12])
        self.assertTrue({'start': 0, 'end': 11, 'name': 'indentation', 'value': '720'} in annotations[13])
        self.assertTrue({'start': 0, 'end': 11, 'name': 'indentation', 'value': '1440'} in annotations[14])

    def test_example_2(self):
        result = self._send_request("annotation_docx/example_2.docx")['content']['structure']['subparagraphs']
        annotations = [subparagraph['annotations'] for subparagraph in result]

        # heading, italic, bold, underlined
        self.assertTrue({'start': 0, 'end': 31, 'name': 'italic', 'value': 'True'} in annotations[3] and
                        {'start': 0, 'end': 31, 'name': 'style', 'value': 'heading 4'} in annotations[3])
        self.assertTrue({'start': 0, 'end': 29, 'name': 'italic', 'value': 'True'} in annotations[8] and
                        {'start': 0, 'end': 29, 'name': 'style', 'value': 'heading 9'} in annotations[8])
        self.assertTrue({'start': 66, 'end': 73, 'name': 'italic', 'value': 'True'} in annotations[35] and
                        {'start': 75, 'end': 89, 'name': 'bold', 'value': 'True'} in annotations[35] and
                        {'start': 91, 'end': 111, 'name': 'underlined', 'value': 'True'} in annotations[35] and
                        {'start': 0, 'end': 153, 'name': 'size', 'value': '14.0'} in annotations[35] and
                        {'start': 153, 'end': 175, 'name': 'size', 'value': '20.0'} in annotations[35] and
                        {'start': 183, 'end': 199, 'name': 'size', 'value': '11.0'} in annotations[35])
        # alignment
        self.assertTrue({'start': 0, 'end': 46, 'name': 'alignment', 'value': 'right'} in annotations[43])
        self.assertTrue({'start': 0, 'end': 40, 'name': 'alignment', 'value': 'center'} in annotations[44])
        self.assertTrue({'start': 0, 'end': 159, 'name': 'alignment', 'value': 'both'})
        # bold, italic, underlined
        self.assertTrue({'start': 0, 'end': 26, 'name': 'bold', 'value': 'True'} in annotations[47])
        self.assertTrue({'start': 0, 'end': 29, 'name': 'italic', 'value': 'True'} in annotations[48])
        self.assertTrue({'start': 0, 'end': 32, 'name': 'underlined', 'value': 'True'} in annotations[49])
        self.assertTrue({'start': 0, 'end': 35, 'name': 'bold', 'value': 'True'} in annotations[50] and
                        {'start': 0, 'end': 35, 'name': 'italic', 'value': 'True'} in annotations[50])
        self.assertTrue({'start': 0, 'end': 51, 'name': 'bold', 'value': 'True'} in annotations[51] and
                        {'start': 0, 'end': 51, 'name': 'underlined', 'value': 'True'} in annotations[51] and
                        {'start': 0, 'end': 51, 'name': 'italic', 'value': 'True'} in annotations[51])

    def test_spacing_1(self):
        result = self._send_request("annotation_docx/spacing_libreoffice.docx")['content']['structure']['subparagraphs']
        annotations = [subparagraph['annotations'] for subparagraph in result]

        self.assertTrue({'start': 0, 'end': 10, 'name': 'spacing', 'value': '0'} in annotations[0])
        self.assertTrue({'start': 0, 'end': 10, 'name': 'spacing', 'value': '0'} in annotations[1])
        self.assertTrue({'start': 0, 'end': 10, 'name': 'spacing', 'value': '57'} in annotations[2])
        self.assertTrue({'start': 0, 'end': 10, 'name': 'spacing', 'value': '114'} in annotations[3])
        self.assertTrue({'start': 0, 'end': 10, 'name': 'spacing', 'value': '114'} in annotations[4])
        self.assertTrue({'start': 0, 'end': 10, 'name': 'spacing', 'value': '114'} in annotations[5])
        self.assertTrue({'start': 0, 'end': 10, 'name': 'spacing', 'value': '114'} in annotations[6])
        self.assertTrue({'start': 0, 'end': 9, 'name': 'spacing', 'value': '0'} in annotations[7])

    def test_spacing_2(self):
        result = self._send_request("annotation_docx/"
                                    "spacing_microsoft_word.docx")['content']['structure']['subparagraphs']
        annotations = [subparagraph['annotations'] for subparagraph in result]

        self.assertTrue({'start': 0, 'end': 10, 'name': 'spacing', 'value': '0'} in annotations[0])
        self.assertTrue({'start': 0, 'end': 10, 'name': 'spacing', 'value': '0'} in annotations[1])
        self.assertTrue({'start': 0, 'end': 31, 'name': 'spacing', 'value': '200'} in annotations[2])
        self.assertTrue({'start': 0, 'end': 31, 'name': 'spacing', 'value': '200'} in annotations[3])
        self.assertTrue({'start': 0, 'end': 32, 'name': 'spacing', 'value': '400'} in annotations[4])
        self.assertTrue({'start': 0, 'end': 31, 'name': 'spacing', 'value': '400'} in annotations[5])
        self.assertTrue({'start': 0, 'end': 31, 'name': 'spacing', 'value': '600'} in annotations[6])
        self.assertTrue({'start': 0, 'end': 10, 'name': 'spacing', 'value': '400'} in annotations[7])
        self.assertTrue({'start': 0, 'end': 10, 'name': 'spacing', 'value': '0'} in annotations[8])

    def test_identation(self):
        result = self._send_request("annotation_docx/"
                                    "indentation_libreoffice.docx")['content']['structure']['subparagraphs']
        annotations = [subparagraph['annotations'] for subparagraph in result]
        self.assertTrue({'start': 0, 'end': 188, 'name': 'indentation', 'value': '360'} in annotations[5])
        self.assertTrue({'start': 0, 'end': 152, 'name': 'indentation', 'value': '708'} in annotations[10])
        self.assertTrue({'start': 0, 'end': 0, 'name': 'indentation', 'value': '1429'} in annotations[12])
        self.assertTrue({'start': 0, 'end': 21, 'name': 'indentation', 'value': '709'} in annotations[16])
        self.assertTrue({'start': 0, 'end': 65, 'name': 'indentation', 'value': '786'} in annotations[20])
