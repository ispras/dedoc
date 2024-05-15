import logging
import os.path
import shutil
import tempfile
from typing import Dict, Optional, Tuple

from dedoc.api.api_args import QueryParameters
from dedoc.common.exceptions.bad_file_error import BadFileFormatError
from dedoc.common.exceptions.conversion_error import ConversionError
from dedoc.common.exceptions.dedoc_error import DedocError
from dedoc.config import get_config
from dedoc.data_structures import ParsedDocument, UnstructuredDocument
from dedoc.extensions import mime2extension
from dedoc.manager_config import get_manager_config
from dedoc.metadata_extractors import BaseMetadataExtractor
from dedoc.utils.train_dataset_utils import get_path_original_documents, save_line_with_meta
from dedoc.utils.utils import get_file_mime_by_content, get_mime_extension, get_unique_name


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
            - converter (optional) (:class:`~dedoc.converters.ConverterComposition`)
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
        :param parameters: any parameters, specify how to parse file, see :ref:`parameters_description` for more details
        :return: parsed document
        """
        parameters = self.__init_parameters(file_path, parameters)
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
            raise FileNotFoundError(file_path)
        self.logger.info(f"Start handle {file_path}")
        file_dir, file_name = os.path.split(file_path)
        unique_filename = get_unique_name(file_name)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_file_path = os.path.join(tmp_dir, unique_filename)
            shutil.copy(file_path, tmp_file_path)

            # Steps 1-3 - Converting, Reading content and Adding meta-information
            converted_file_path, unstructured_document = self.__read_with_mime_auto_detection(
                file_name=file_name, parameters=parameters, file_path=tmp_file_path
            )
            self.logger.info(f"Extract content from file {file_name}")

            # Step 4 - Extract structure
            unstructured_document = self.structure_extractor.extract(unstructured_document, parameters)
            self.logger.info(f"Extract structure from file {file_name}")

            if self.config.get("labeling_mode", False):
                self.__save(converted_file_path, unstructured_document)

            # Step 5 - Form the output structure
            parsed_document = self.structure_constructor.construct(document=unstructured_document, parameters=parameters)
            self.logger.info(f"Get structured document {file_name}")

            # Step 6 - Get attachments
            attachments = self.attachments_handler.handle_attachments(document_parser=self, document=unstructured_document, parameters=parameters)
            parsed_document.add_attachments(attachments)
            self.logger.info(f"Get attachments {file_name}")

            self.logger.info(f"Finish handle {file_name}")
        return parsed_document

    def __init_parameters(self, file_path: str, parameters: Optional[dict]) -> dict:
        parameters = {} if parameters is None else parameters
        result_parameters = {}

        for parameter_name, parameter_value in self.default_parameters.items():
            result_parameters[parameter_name] = parameters.get(parameter_name, parameter_value)

        attachments_dir = parameters.get("attachments_dir", None)
        result_parameters["attachments_dir"] = os.path.dirname(file_path) if attachments_dir is None else attachments_dir

        return result_parameters

    def __read_with_mime_auto_detection(self, file_path: str, file_name: str, parameters: Optional[dict]) -> Tuple[str, UnstructuredDocument]:
        # firstly, try to read file using its original extension
        mime, extension = get_mime_extension(file_path=file_path)
        try:
            converted_file_path, document = self.__parse_file(file_path=file_path, file_name=file_name, parameters=parameters, mime=mime, extension=extension)
        except (ConversionError, BadFileFormatError) as e:
            # secondly, try to read file using mime obtained by file's content
            detected_mime = get_file_mime_by_content(file_path)
            detected_extension = mime2extension.get(detected_mime, "")
            self.logger.warning(f'Could not read file {file_name} with mime = "{mime}", extension = "{extension}" ({e}). '
                                f'Detected file mime = "{detected_mime}", extension = "{detected_extension}"')
            fixed_file_path = f"{file_path}{detected_extension}"
            os.rename(file_path, fixed_file_path)
            converted_file_path, document = self.__parse_file(
                file_path=fixed_file_path, file_name=file_name, parameters=parameters, mime=detected_mime, extension=detected_extension
            )
            document.warnings.append(f'Incorrect extension "{extension}". Detected mime = "{detected_mime}", extension = "{detected_extension}"')

        return converted_file_path, document

    def __parse_file(self, file_path: str, file_name: str, parameters: Optional[dict], extension: str, mime: str) -> Tuple[str, UnstructuredDocument]:
        converted_file_path = self.converter.convert(file_path, parameters=parameters, mime=mime, extension=extension)
        if converted_file_path != file_path:
            mime, extension = get_mime_extension(file_path=converted_file_path)

        unstructured_document = self.reader.read(file_path=converted_file_path, parameters=parameters, mime=mime, extension=extension)
        metadata = self.document_metadata_extractor.extract(file_path=file_path, converted_filename=os.path.basename(converted_file_path),
                                                            original_filename=file_name, parameters=parameters, mime=mime, extension=extension)

        unstructured_document.metadata = {**unstructured_document.metadata, **metadata}
        return converted_file_path, unstructured_document

    def __save(self, file_path: str, classified_document: UnstructuredDocument) -> None:
        self.logger.info(f'Save document lines to {self.config["intermediate_data_path"]}')
        save_line_with_meta(lines=classified_document.lines, config=self.config, original_document=os.path.basename(file_path))
        shutil.copy(file_path, os.path.join(get_path_original_documents(self.config), os.path.basename(file_path)))
