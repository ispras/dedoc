import logging
import os.path
import shutil
import tempfile
from typing import Dict, Optional

from dedoc.api.api_args import QueryParameters
from dedoc.common.exceptions.dedoc_error import DedocError
from dedoc.config import get_config
from dedoc.data_structures import ParsedDocument, UnstructuredDocument
from dedoc.manager_config import get_manager_config
from dedoc.metadata_extractors import BaseMetadataExtractor
from dedoc.train_dataset.train_dataset_utils import get_path_original_documents, save_line_with_meta
from dedoc.utils.utils import get_unique_name


class DedocManager:
    """
    This class allows to run the whole pipeline of the document processing:

        1. Converting
        2. Reading
        3. Metadata extraction
        4. Structure extraction
        5. Output structure construction
        6. Attachments handling
    """

    def __init__(self, config: Optional[dict] = None, manager_config: Optional[dict] = None) -> None:
        """
        :param config: config for document processing
        :param manager_config: dictionary with different stage document processors.

        The following keys should be in the `manager_config` dictionary:
            - converter (optional) (:class:`~dedoc.converters.FileConverterComposition`)
            - reader (:class:`~dedoc.readers.ReaderComposition`)
            - structure_extractor (:class:`~dedoc.structure_extractors.StructureExtractorComposition`)
            - structure_constructor (:class:`~dedoc.structure_constructors.StructureConstructorComposition`)
            - document_metadata_extractor (:class:`~dedoc.metadata_extractors.MetadataExtractorComposition`)
            - attachments_handler (:class:`~dedoc.attachments_handler.AttachmentsHandler`)
        """
        self.config = get_config() if config is None else config
        self.logger = self.config.get("logger", logging.getLogger())
        manager_config = get_manager_config(self.config) if manager_config is None else manager_config

        self.converter = manager_config.get("converter", None)
        self.reader = manager_config.get("reader", None)
        assert self.reader is not None, "Reader shouldn't be None"
        self.structure_extractor = manager_config.get("structure_extractor", None)
        assert self.structure_extractor is not None, "Structure extractor shouldn't be None"
        self.structure_constructor = manager_config.get("structure_constructor", None)
        assert self.structure_constructor is not None, "Structure constructor shouldn't be None"
        self.document_metadata_extractor = manager_config.get("document_metadata_extractor", None)
        assert self.document_metadata_extractor is not None, "Document metadata extractor shouldn't be None"
        self.attachments_handler = manager_config.get("attachments_handler", None)
        assert self.attachments_handler is not None, "Attachments handler shouldn't be None"

        self.default_parameters = QueryParameters().to_dict()

    def parse(self, file_path: str, parameters: Optional[Dict[str, str]] = None) -> ParsedDocument:
        """
        Run the whole pipeline of the document processing.
        If some error occurred, file metadata are stored in the exception's metadata field.

        :param file_path: full path where the file is located
        :param parameters: any parameters, specify how to parse file (see API parameters documentation for more details)
        :return: parsed document
        """
        parameters = self.__init_parameters(parameters)
        self.logger.info(f"Get file {os.path.basename(file_path)} with parameters {parameters}")

        try:
            return self.__parse_no_error_handling(file_path=file_path, parameters=parameters)
        except DedocError as e:
            file_dir, file_name = os.path.split(file_path)
            e.filename = file_name
            e.metadata = BaseMetadataExtractor._get_base_meta_information(directory=file_dir, filename=file_name, name_actual=file_name)
            raise e

    def __parse_no_error_handling(self, file_path: str, parameters: Dict[str, str]) -> ParsedDocument:
        """
        Function of complete document parsing without errors handling.

        :param file_path: full path where the file is located
        :param parameters: any parameters, specify how to parse file
        :return: parsed document
        """
        if not os.path.isfile(path=file_path):
            raise FileNotFoundError()
        self.logger.info(f"Start handle {file_path}")
        file_dir, file_name = os.path.split(file_path)
        unique_filename = get_unique_name(file_name)

        with tempfile.TemporaryDirectory() as tmp_dir:
            shutil.copy(file_path, os.path.join(tmp_dir, unique_filename))

            # Step 1 - Converting
            converted_filename = self.converter.do_converting(tmp_dir, unique_filename, parameters=parameters)
            self.logger.info(f"Finish conversion {file_name} -> {converted_filename}")

            # Step 2 - Reading content
            unstructured_document = self.reader.parse_file(tmp_dir=tmp_dir, filename=converted_filename, parameters=parameters)
            self.logger.info(f"Finish parse file {file_name}")

            # Step 3 - Adding meta-information
            unstructured_document = self.document_metadata_extractor.add_metadata(document=unstructured_document,
                                                                                  directory=tmp_dir,
                                                                                  filename=unique_filename,
                                                                                  converted_filename=converted_filename,
                                                                                  original_filename=file_name,
                                                                                  parameters=parameters,
                                                                                  other_fields=unstructured_document.metadata)
            self.logger.info(f"Add metadata of file {file_name}")

            # Step 4 - Extract structure
            unstructured_document = self.structure_extractor.extract_structure(unstructured_document, parameters)
            self.logger.info(f"Extract structure from file {file_name}")

            if self.config.get("labeling_mode", False):
                self.__save(os.path.join(tmp_dir, unique_filename), unstructured_document)

            # Step 5 - Form the output structure
            parsed_document = self.structure_constructor.structure_document(document=unstructured_document,
                                                                            structure_type=parameters.get("structure_type"),
                                                                            parameters=parameters)
            self.logger.info(f"Get structured document {file_name}")

            # Step 6 - Get attachments
            attachments = self.attachments_handler.handle_attachments(document_parser=self, document=unstructured_document, parameters=parameters)
            parsed_document.add_attachments(attachments)
            self.logger.info(f"Get attachments {file_name}")

            self.logger.info(f"Finish handle {file_name}")
        return parsed_document

    def __init_parameters(self, parameters: Optional[dict]) -> dict:
        parameters = {} if parameters is None else parameters
        result_parameters = {}

        for parameter_name, parameter_value in self.default_parameters.items():
            result_parameters[parameter_name] = parameters.get(parameter_name, parameter_value)

        return result_parameters

    def __save(self, file_path: str, classified_document: UnstructuredDocument) -> None:
        save_line_with_meta(lines=classified_document.lines, config=self.config, original_document=os.path.basename(file_path))
        shutil.copy(file_path, os.path.join(get_path_original_documents(self.config), os.path.basename(file_path)))
