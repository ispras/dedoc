from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader
import json
import re


class TestApiDocxAnnotations(AbstractTestApiDocReader):

    def test_example_1(self):
        result = self._send_request("annotation_docx/example_1.docx")['content']['structure']['subparagraphs']
        annotations = [subparagraph['annotations'] for subparagraph in result]
        # bold, italic, underlined
        self.assertTrue({'start': 0, 'end': 10, 'name': 'style', 'value': 'body'} in annotations[1])
        self.assertTrue({'start': 0, 'end': 11, 'name': 'italic', 'value': 'True'} in annotations[2])
        self.assertTrue({'start': 0, 'end': 9, 'name': 'bold', 'value': 'True'} in annotations[3])
        self.assertTrue({'start': 0, 'end': 15, 'name': 'underlined', 'value': 'True'} in annotations[4])
        self.assertTrue({'start': 0, 'end': 6, 'name': 'italic', 'value': 'True'} in annotations[5])
        self.assertTrue({'start': 8, 'end': 12, 'name': 'bold', 'value': 'True'} in annotations[6])
        self.assertTrue({'start': 0, 'end': 19, 'name': 'bold', 'value': 'True'} in annotations[7] and
                        {'start': 5, 'end': 19, 'name': 'underlined', 'value': 'True'} in annotations[7])
        # alignment
        self.assertTrue({'start': 0, 'end': 9, 'name': 'alignment', 'value': 'left'} in annotations[9])
        self.assertTrue({'start': 0, 'end': 13, 'name': 'alignment', 'value': 'center'} in annotations[10])
        self.assertTrue({'start': 0, 'end': 10, 'name': 'alignment', 'value': 'right'} in annotations[11])
        self.assertTrue({'start': 0, 'end': 28, 'name': 'alignment', 'value': 'both'} in annotations[12])
        # indent
        self.assertTrue({'start': 0, 'end': 11, 'name': 'indentation', 'value': '0'} in annotations[13])
        self.assertTrue({'start': 0, 'end': 10, 'name': 'indentation', 'value': '720'} in annotations[14])
        self.assertTrue({'start': 0, 'end': 11, 'name': 'indentation', 'value': '1440'} in annotations[15])

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
                        {'start': 0, 'end': 153, 'name': 'size', 'value': '20.0'} in annotations[35] and
                        {'start': 153, 'end': 175, 'name': 'size', 'value': '14.0'} in annotations[35] and
                        {'start': 175, 'end': 183, 'name': 'size', 'value': '11.0'} in annotations[35])
        # alignment
        self.assertTrue({'start': 0, 'end': 45, 'name': 'alignment', 'value': 'right'} in annotations[43])
        self.assertTrue({'start': 0, 'end': 39, 'name': 'alignment', 'value': 'center'} in annotations[44])
        self.assertTrue({'start': 0, 'end': 159, 'name': 'alignment', 'value': 'both'})
        # bold, italic, underlined
        self.assertTrue({'start': 0, 'end': 25, 'name': 'bold', 'value': 'True'} in annotations[47])
        self.assertTrue({'start': 0, 'end': 28, 'name': 'italic', 'value': 'True'} in annotations[48])
        self.assertTrue({'start': 0, 'end': 31, 'name': 'underlined', 'value': 'True'} in annotations[49])
        self.assertTrue({'start': 0, 'end': 34, 'name': 'bold', 'value': 'True'} in annotations[50] and
                        {'start': 0, 'end': 34, 'name': 'italic', 'value': 'True'} in annotations[50])
        self.assertTrue({'start': 0, 'end': 50, 'name': 'bold', 'value': 'True'} in annotations[51] and
                        {'start': 0, 'end': 50, 'name': 'underlined', 'value': 'True'} in annotations[51] and
                        {'start': 0, 'end': 50, 'name': 'italic', 'value': 'True'} in annotations[51])
