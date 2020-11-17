from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader
import json
import re


class TestApiDocxAnnotations(AbstractTestApiDocReader):

    @staticmethod
    def __get_indent(annotations):
        for annotation in annotations:
            if 'value' in annotation and annotation['value'].startswith('indent'):
                return json.loads(re.sub("'", '"', annotation['value'][7:]))

    def test_example_1(self):
        result = self._send_request("annotation_docx/example_1.docx")['content']['structure']['subparagraphs']
        annotations = [subparagraph['annotations'] for subparagraph in result]
        # bold, italic, underlined
        self.assertTrue({'start': 0, 'end': 10, 'value': 'style:body'} in annotations[1])
        self.assertTrue({'start': 0, 'end': 11, 'value': 'italic'} in annotations[2])
        self.assertTrue({'start': 0, 'end': 9, 'value': 'bold'} in annotations[3])
        self.assertTrue({'start': 0, 'end': 15, 'value': 'underlined'} in annotations[4])
        self.assertTrue({'start': 0, 'end': 6, 'value': 'italic'} in annotations[5])
        self.assertTrue({'start': 8, 'end': 12, 'value': 'bold'} in annotations[6])
        self.assertTrue({'start': 0, 'end': 19, 'value': 'bold'} in annotations[7] and
                        {'start': 5, 'end': 19, 'value': 'underlined' in annotations[7]})
        # alignment
        self.assertTrue({'start': 0, 'end': 9, 'value': 'alignment:left'} in annotations[9])
        self.assertTrue({'start': 0, 'end': 13, 'value': 'alignment:center'} in annotations[10])
        self.assertTrue({'start': 0, 'end': 10, 'value': 'alignment:right'} in annotations[11])
        self.assertTrue({'start': 0, 'end': 28, 'value': 'alignment:both'} in annotations[12])
        # indent
        self.assertEqual({'left': 0, 'firstLine': 0, 'hanging': 0, 'start': 0}, self.__get_indent(annotations[13]))
        self.assertEqual({'left': 720, 'firstLine': 0, 'hanging': 0, 'start': 0}, self.__get_indent(annotations[14]))
        self.assertEqual({'left': 1440, 'firstLine': 0, 'hanging': 0, 'start': 0}, self.__get_indent(annotations[15]))

    def test_example_2(self):
        result = self._send_request("annotation_docx/example_2.docx")['content']['structure']['subparagraphs']
        annotations = [subparagraph['annotations'] for subparagraph in result]

        # heading, italic, bold, underlined
        self.assertTrue({'start': 0, 'end': 31, 'value': 'italic'} in annotations[3] and
                        {'start': 0, 'end': 31, 'value': 'style:heading 4'} in annotations[3])
        self.assertTrue({'start': 0, 'end': 29, 'value': 'italic'} in annotations[8] and
                        {'start': 0, 'end': 29, 'value': 'style:heading 9'} in annotations[8])
        self.assertTrue({'start': 66, 'end': 73, 'value': 'italic'} in annotations[35] and
                        {'start': 75, 'end': 89, 'value': 'bold'} in annotations[35] and
                        {'start': 91, 'end': 111, 'value': 'underlined'} in annotations[35] and
                        {'start': 0, 'end': 153, 'value': 'size:40'} in annotations[35] and
                        {'start': 153, 'end': 175, 'value': 'size:28'} in annotations[35] and
                        {'start': 175, 'end': 183, 'value': 'size:22'} in annotations[35])
        # alignment
        self.assertTrue({'start': 0, 'end': 45, 'value': 'alignment:right'} in annotations[43])
        self.assertTrue({'start': 0, 'end': 39, 'value': 'alignment:center'} in annotations[44])
        self.assertTrue({'start': 0, 'end': 159, 'value': 'alignment:both'})
        # bold, italic, underlined
        self.assertTrue({'start': 0, 'end': 25, 'value': 'bold'} in annotations[47])
        self.assertTrue({'start': 0, 'end': 28, 'value': 'italic'} in annotations[48])
        self.assertTrue({'start': 0, 'end': 31, 'value': 'underlined'} in annotations[49])
        self.assertTrue({'start': 0, 'end': 34, 'value': 'bold'} in annotations[50] and
                        {'start': 0, 'end': 34, 'value': 'italic'} in annotations[50])
        self.assertTrue({'start': 0, 'end': 50, 'value': 'bold'} in annotations[51] and
                        {'start': 0, 'end': 50, 'value': 'underlined'} in annotations[51] and
                        {'start': 0, 'end': 50, 'value': 'italic'} in annotations[51])
