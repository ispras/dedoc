import os
import unittest

from dedoc.metadata_extractor.concreat_metadata_extractors.note_metadata_extarctor import NoteMetadataExtractor
from dedoc.metadata_extractor.metadata_extractor_composition import MetadataExtractorComposition
from dedoc.readers.note_reader.note_reader import NoteReader
from dedoc.readers.reader_composition import ReaderComposition
from dedoc.structure_constructor.concreat_structure_constructors.linear_constructor import LinearConstructor
from dedoc.structure_constructor.structure_constructor_composition import StructureConstructorComposition


class TestNote(unittest.TestCase):
    reader = ReaderComposition(readers=[NoteReader()])
    structure_constructor = StructureConstructorComposition(extractors={"linear": LinearConstructor()},
                                                            default_extractor=LinearConstructor())
    document_metadata_extractor = MetadataExtractorComposition(extractors=[NoteMetadataExtractor()])

    def test_note(self):
        parameters = {'structure_type': 'linear', 'with_attachments': 'true', 'document_type': ''}

        tmp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        filename = "1612522226_339.note.pickle"
        unstructured_document, _ = self.reader.parse_file(
            tmp_dir=tmp_dir,
            filename=filename,
            parameters=parameters
        )

        document_content = self.structure_constructor.structure_document(document=unstructured_document,
                                                                         structure_type=parameters.get(
                                                                             "structure_type")
                                                                         )

        parsed_document = self.document_metadata_extractor.add_metadata(doc=document_content,
                                                                        directory=tmp_dir,
                                                                        filename=filename,
                                                                        converted_filename="",
                                                                        original_filename="",
                                                                        parameters=parameters)

        self.assertEqual(parsed_document.content.structure.subparagraphs[0].text, 'hello')
        self.assertEqual(parsed_document.metadata.access_time, 1111)
        self.assertEqual(parsed_document.metadata.created_time, 1111)
        self.assertEqual(parsed_document.metadata.modified_time, 1111)
        self.assertEqual(parsed_document.metadata.file_type, "note")
        self.assertEqual(parsed_document.metadata.file_name, "")
        self.assertEqual(parsed_document.metadata.other_fields["author"], "user1")
        self.assertEqual(parsed_document.metadata.size, 5)
