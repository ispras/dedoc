import os

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiDocxAnnotations(AbstractTestApiDocReader):

    def test_example_1(self) -> None:
        result = self._send_request("annotation_docx/example_1.docx", data={"structure_type": "linear"})
        subparagraphs = result['content']['structure']['subparagraphs']
        annotations = [subparagraph['annotations'] for subparagraph in subparagraphs]

        # bold, italic, underlined
        self.assertIn({'start': 0, 'end': 11, 'name': 'style', 'value': 'Body'}, annotations[0])
        self.assertIn({'start': 0, 'end': 12, 'name': 'italic', 'value': 'True'}, annotations[1])
        self.assertIn({'start': 0, 'end': 10, 'name': 'bold', 'value': 'True'}, annotations[2])
        self.assertIn({'start': 0, 'end': 16, 'name': 'underlined', 'value': 'True'}, annotations[3])
        self.assertIn({'start': 0, 'end': 6, 'name': 'italic', 'value': 'True'}, annotations[4])
        self.assertIn({'start': 8, 'end': 13, 'name': 'bold', 'value': 'True'}, annotations[5])
        self.assertIn({'start': 0, 'end': 20, 'name': 'bold', 'value': 'True'}, annotations[6])
        self.assertIn({'start': 5, 'end': 20, 'name': 'underlined', 'value': 'True'}, annotations[6])
        # alignment
        self.assertIn({'start': 0, 'end': 10, 'name': 'alignment', 'value': 'left'}, annotations[8])
        self.assertIn({'start': 0, 'end': 14, 'name': 'alignment', 'value': 'center'}, annotations[9])
        self.assertIn({'start': 0, 'end': 11, 'name': 'alignment', 'value': 'right'}, annotations[10])
        self.assertIn({'start': 0, 'end': 29, 'name': 'alignment', 'value': 'both'}, annotations[11])
        # indent
        self.assertIn({'start': 0, 'end': 12, 'name': 'indentation', 'value': '0'}, annotations[12])
        self.assertIn({'start': 0, 'end': 11, 'name': 'indentation', 'value': '720'}, annotations[13])
        self.assertIn({'start': 0, 'end': 12, 'name': 'indentation', 'value': '1440'}, annotations[14])
        # strike
        self.assertIn({'start': 0, 'end': 11, 'name': 'strike', 'value': 'True'}, annotations[15])

    def test_example_2(self) -> None:
        result = self._send_request("annotation_docx/example_2.docx", data={"structure_type": "linear"})
        subparagraphs = result['content']['structure']['subparagraphs']
        annotations = [subparagraph['annotations'] for subparagraph in subparagraphs]

        # heading, italic, bold, underlined
        self.assertIn({'start': 0, 'end': 31, 'name': 'italic', 'value': 'True'}, annotations[3])
        self.assertIn({'start': 0, 'end': 31, 'name': 'style', 'value': 'heading 4'}, annotations[3])
        self.assertIn({'start': 0, 'end': 29, 'name': 'italic', 'value': 'True'}, annotations[8])
        self.assertIn({'start': 0, 'end': 29, 'name': 'style', 'value': 'heading 9'}, annotations[8])
        self.assertIn({'start': 66, 'end': 73, 'name': 'italic', 'value': 'True'}, annotations[35])
        self.assertIn({'start': 75, 'end': 89, 'name': 'bold', 'value': 'True'}, annotations[35])
        self.assertIn({'start': 91, 'end': 111, 'name': 'underlined', 'value': 'True'}, annotations[35])
        self.assertIn({'start': 0, 'end': 153, 'name': 'size', 'value': '14.0'}, annotations[35])
        self.assertIn({'start': 153, 'end': 175, 'name': 'size', 'value': '20.0'}, annotations[35])
        self.assertIn({'start': 183, 'end': 199, 'name': 'size', 'value': '11.0'}, annotations[35])
        # alignment
        self.assertIn({'start': 0, 'end': 46, 'name': 'alignment', 'value': 'right'}, annotations[43])
        self.assertIn({'start': 0, 'end': 40, 'name': 'alignment', 'value': 'center'}, annotations[44])
        self.assertIn({'start': 0, 'end': 160, 'name': 'alignment', 'value': 'both'}, annotations[45])
        # bold, italic, underlined
        self.assertIn({'start': 0, 'end': 26, 'name': 'bold', 'value': 'True'}, annotations[47])
        self.assertIn({'start': 0, 'end': 29, 'name': 'italic', 'value': 'True'}, annotations[48])
        self.assertIn({'start': 0, 'end': 32, 'name': 'underlined', 'value': 'True'}, annotations[49])
        self.assertIn({'start': 0, 'end': 35, 'name': 'bold', 'value': 'True'}, annotations[50])
        self.assertIn({'start': 0, 'end': 35, 'name': 'italic', 'value': 'True'}, annotations[50])
        self.assertIn({'start': 0, 'end': 51, 'name': 'bold', 'value': 'True'}, annotations[51])
        self.assertIn({'start': 0, 'end': 51, 'name': 'underlined', 'value': 'True'}, annotations[51])
        self.assertIn({'start': 0, 'end': 51, 'name': 'italic', 'value': 'True'}, annotations[51])

    def test_spacing_1(self) -> None:
        result = self._send_request("annotation_docx/spacing_libreoffice.docx", data={"structure_type": "linear"})
        subparagraphs = result['content']['structure']['subparagraphs']
        annotations = [subparagraph['annotations'] for subparagraph in subparagraphs]

        self.assertIn({'start': 0, 'end': 10, 'name': 'spacing', 'value': '0'}, annotations[0])
        self.assertIn({'start': 0, 'end': 10, 'name': 'spacing', 'value': '0'}, annotations[1])
        self.assertIn({'start': 0, 'end': 10, 'name': 'spacing', 'value': '57'}, annotations[2])
        self.assertIn({'start': 0, 'end': 10, 'name': 'spacing', 'value': '114'}, annotations[3])
        self.assertIn({'start': 0, 'end': 10, 'name': 'spacing', 'value': '114'}, annotations[4])
        self.assertIn({'start': 0, 'end': 10, 'name': 'spacing', 'value': '114'}, annotations[5])
        self.assertIn({'start': 0, 'end': 10, 'name': 'spacing', 'value': '114'}, annotations[6])
        self.assertIn({'start': 0, 'end': 9, 'name': 'spacing', 'value': '0'}, annotations[7])

    def test_spacing_2(self) -> None:
        result = self._send_request("annotation_docx/spacing_microsoft_word.docx", data={"structure_type": "linear"})
        subparagraphs = result['content']['structure']['subparagraphs']
        annotations = [subparagraph['annotations'] for subparagraph in subparagraphs]

        self.assertIn({'start': 0, 'end': 10, 'name': 'spacing', 'value': '0'}, annotations[0])
        self.assertIn({'start': 0, 'end': 10, 'name': 'spacing', 'value': '0'}, annotations[1])
        self.assertIn({'start': 0, 'end': 31, 'name': 'spacing', 'value': '200'}, annotations[2])
        self.assertIn({'start': 0, 'end': 31, 'name': 'spacing', 'value': '200'}, annotations[3])
        self.assertIn({'start': 0, 'end': 32, 'name': 'spacing', 'value': '400'}, annotations[4])
        self.assertIn({'start': 0, 'end': 31, 'name': 'spacing', 'value': '400'}, annotations[5])
        self.assertIn({'start': 0, 'end': 31, 'name': 'spacing', 'value': '600'}, annotations[6])
        self.assertIn({'start': 0, 'end': 10, 'name': 'spacing', 'value': '400'}, annotations[7])
        self.assertIn({'start': 0, 'end': 10, 'name': 'spacing', 'value': '0'}, annotations[8])

    def test_identation(self) -> None:
        result = self._send_request("annotation_docx/indentation_libreoffice.docx", data={"structure_type": "linear"})
        subparagraphs = result['content']['structure']['subparagraphs']
        annotations = [subparagraph['annotations'] for subparagraph in subparagraphs]
        self.assertIn({'start': 0, 'end': 188, 'name': 'indentation', 'value': '360'}, annotations[5])
        self.assertIn({'start': 0, 'end': 152, 'name': 'indentation', 'value': '708'}, annotations[10])
        self.assertIn({'start': 0, 'end': 0, 'name': 'indentation', 'value': '1429'}, annotations[12])
        self.assertIn({'start': 0, 'end': 21, 'name': 'indentation', 'value': '709'}, annotations[16])
        self.assertIn({'start': 0, 'end': 65, 'name': 'indentation', 'value': '786'}, annotations[20])

    def test_table_refs(self) -> None:
        result = self._send_request("annotation_docx/table_refs.docx", data={"structure_type": "linear"})
        subparagraphs = result['content']['structure']['subparagraphs']
        for i in [0, 2, 4, 6, 9]:
            annotations = subparagraphs[i]['annotations']
            found = False
            for annotation in annotations:
                if annotation["name"] == "table":
                    found = True
                    break
            self.assertTrue(found)

    def test_subscript_docx(self) -> None:
        file_name = "example_superscript.docx"
        self._check_superscript(file_name)

    def test_subscript_odt(self) -> None:
        file_name = "example_superscript.odt"
        self._check_superscript(file_name)

    def test_subscript_doc(self) -> None:
        file_name = "example_superscript.doc"
        self._check_superscript(file_name)

    def _check_superscript(self, file_name: str) -> None:
        result = self._send_request(os.path.join("docx", file_name), data={"structure_type": "tree"})
        content = result["content"]["structure"]
        subparagraph = content["subparagraphs"][0]
        annotations = subparagraph["annotations"]
        self.assertIn({"start": 5, "end": 6, "name": "superscript", "value": "True"}, annotations)
        self.assertIn({"start": 9, "end": 10, "name": "subscript", "value": "True"}, annotations)
