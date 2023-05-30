import copy
import logging
import os
import shutil
import tempfile
import time
from typing import Optional, List, Dict

from dedoc.attachments_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor
from dedoc.attachments_handler.attachments_handler import AttachmentsHandler
from dedoc.common.exceptions.dedoc_exception import DedocException
from dedoc.converters.file_converter import FileConverterComposition
from dedoc.data_structures.document_metadata import DocumentMetadata
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
from dedoc.metadata_extractors.metadata_extractor_composition import MetadataExtractorComposition
from dedoc.readers.reader_composition import ReaderComposition
from dedoc.structure_constructors.structure_constructor_composition import StructureConstructorComposition
from dedoc.structure_extractors.structure_extractor_composition import StructureExtractorComposition
from dedoc.train_dataset.train_dataset_utils import save_line_with_meta, get_path_original_documents
from dedoc.utils.utils import get_unique_name, get_empty_content


class DedocManager:

    def __init__(self,
                 converter: FileConverterComposition,
                 attachments_handler: AttachmentsHandler,
                 reader: ReaderComposition,
                 structure_extractor: StructureExtractorComposition,
                 structure_constructor: StructureConstructorComposition,
                 document_metadata_extractor: MetadataExtractorComposition,
                 logger: logging.Logger,
                 version: str,
                 *,
                 config: dict) -> None:
        self.version = version
        self.converter = converter
        self.attachments_handler = attachments_handler
        self.reader = reader
        self.structure_extractor = structure_extractor
        self.structure_constructor = structure_constructor
        self.document_metadata_extractor = document_metadata_extractor
        self.logger = logger
        self.config = config

    @staticmethod
    def from_config(version: str, manager_config: dict, *, config: dict) -> "DedocManager":
        """
        this method helps to construct dedoc manager from config
        :param version: str, actual version of dedoc (or your lib, based on dedoc) Lay in file VERSION
        :param manager_config: dict, you may get example of managers config dict in manager_config.py
        :param config: any additional parameters for dedoc lay in config, see config.py
        :return: DedocManager
        """

        logger = config.get("logger")
        logger = logger if logger is not None else logging.getLogger(__name__)
        manager = DedocManager(
            converter=manager_config["converter"],
            attachments_handler=manager_config["attachments_extractor"],
            reader=manager_config["reader"],
            structure_extractor=manager_config["structure_extractor"],
            structure_constructor=manager_config["structure_constructor"],
            document_metadata_extractor=manager_config["document_metadata_extractor"],
            logger=logger,
            version=version,
            config=config
        )

        return manager

    def parse_file(self,
                   file_path: str,
                   parameters: Dict[str, str],
                   original_file_name: Optional[str] = None) -> ParsedDocument:
        """
        Function of complete parsing document with 'filename' with attachment files analyze
        :param file_path: full path where file lay
        :param parameters: any parameters, specify how we want to parse file
        :param original_file_name: name of original file (None if file was not renamed)
        :return:
        """
        try:
            return self._parse_file_no_error_handling(file_path=file_path,
                                                      parameters=parameters,
                                                      original_file_name=original_file_name)
        except DedocException as e:
            e.version = self.version
            e.filename = original_file_name
            file_dir, file_name = os.path.split(file_path)
            e.metadata = BaseMetadataExtractor._get_base_meta_information(directory=file_dir,
                                                                          filename=file_name,
                                                                          name_actual=file_name,
                                                                          parameters={})
            raise e

    def _parse_file_no_error_handling(self,
                                      file_path: str,
                                      parameters: Dict[str, str],
                                      original_file_name: Optional[str] = None) -> ParsedDocument:
        """
        Function of complete parsing document with 'filename' with attachment files analyze
        :param file_path: full path where file lay
        :param parameters: any parameters, specify how we want to parse file
        :param original_file_name: name of original file (None if file was not ranamed)
        :return:
        """
        warnings = []
        if not os.path.isfile(path=file_path):
            raise FileNotFoundError()
        self.logger.info("Start handle {}".format(file_path))
        if original_file_name is None:
            original_file_name = os.path.basename(file_path)
        filename = get_unique_name(file_path)
        with tempfile.TemporaryDirectory() as tmp_dir:
            shutil.copy(file_path, os.path.join(tmp_dir, filename))

            # Step 1 - Converting
            filename_convert = self.converter.do_converting(tmp_dir, filename, parameters=parameters)
            self.logger.info("Finish conversion {} -> {}".format(filename, filename_convert))
            # Step 2 - Parsing content of converted file
            unstructured_document = self.reader.parse_file(tmp_dir=tmp_dir, filename=filename_convert, parameters=parameters)
            self.logger.info("Finish parse file {}".format(filename_convert))
            # Step 3 - Adding meta-information
            unstructured_document = self.document_metadata_extractor.add_metadata(document=unstructured_document,
                                                                                  directory=tmp_dir,
                                                                                  filename=filename,
                                                                                  converted_filename=filename_convert,
                                                                                  original_filename=original_file_name,
                                                                                  parameters=parameters,
                                                                                  version=self.version,
                                                                                  other_fields=unstructured_document.metadata)
            self.logger.info("Add metadata of file {}".format(filename_convert))
            # Step 4 - Extract structure
            unstructured_document = self.structure_extractor.extract_structure(unstructured_document, parameters)
            warnings.extend(unstructured_document.warnings)
            self.logger.info("Extract structure from file {}".format(filename_convert))

            if self.config.get("labeling_mode", False):
                self.__save(os.path.join(tmp_dir, filename), unstructured_document)

            # Step 5 - Form the output structure
            structure_type = parameters.get("structure_type")
            parsed_document = self.structure_constructor.structure_document(document=unstructured_document,
                                                                            version=self.version,
                                                                            structure_type=structure_type,
                                                                            parameters=parameters)
            warnings.extend(parsed_document.warnings)
            self.logger.info("Get structured document {}".format(filename_convert))

            if AbstractAttachmentsExtractor.with_attachments(parameters):
                self.logger.info("Start handle attachments")
                parsed_attachment_files = self.__handle_attachments(document=unstructured_document, parameters=parameters, tmp_dir=tmp_dir)
                self.logger.info("Get attachments {}".format(filename_convert))
                parsed_document.add_attachments(parsed_attachment_files)
            else:
                parsed_document.attachments = None
            parsed_document.version = self.version
            parsed_document.warnings.extend(warnings)
            self.logger.info("Finish handle {}".format(filename))
        return parsed_document

    def __save(self, path: str, classified_document: UnstructuredDocument) -> None:
        save_line_with_meta(lines=classified_document.lines, config=self.config,
                            original_document=os.path.basename(path))
        shutil.copy(path, os.path.join(get_path_original_documents(self.config), os.path.basename(path)))

    def __handle_attachments(self,
                             document: UnstructuredDocument,
                             parameters: dict,
                             tmp_dir: str) -> List[ParsedDocument]:
        parsed_attachment_files = []
        self.attachments_handler.handle_attachments(document=document, parameters=parameters)
        previous_log_time = time.time()
        for i, attachment in enumerate(document.attachments):
            current_time = time.time()
            if current_time - previous_log_time > 3:
                previous_log_time = current_time  # not log too often
                self.logger.info("Handle attachment {} of {}".format(i, len(document.attachments)))
            parameters_copy = copy.deepcopy(parameters)
            parameters_copy["is_attached"] = True
            parameters_copy["attachment"] = attachment
            try:
                # TODO handle nested attachments according to recursion_deep_attachments (https://jira.ispras.ru/browse/TLDR-300)
                if attachment.need_content_analysis:
                    file_path = os.path.join(tmp_dir, attachment.get_filename_in_path())
                    parsed_file = self.parse_file(file_path,
                                                  parameters=parameters_copy,
                                                  original_file_name=attachment.get_original_filename())
                else:
                    parsed_file = self.__get_empty_document(directory=tmp_dir,
                                                            filename=attachment.get_filename_in_path(),
                                                            converted_filename=attachment.get_filename_in_path(),
                                                            original_file_name=attachment.get_original_filename(),
                                                            parameters=parameters_copy)
            except DedocException:
                # return empty ParsedDocument with Meta information
                parsed_file = self.__get_empty_document(directory=tmp_dir,
                                                        filename=attachment.get_filename_in_path(),
                                                        converted_filename=attachment.get_filename_in_path(),
                                                        original_file_name=attachment.get_original_filename(),
                                                        parameters=parameters_copy)
            parsed_file.metadata.set_uid(attachment.uid)
            parsed_attachment_files.append(parsed_file)
        return parsed_attachment_files

    def __get_empty_document(self, directory: str, filename: str, converted_filename: str, original_file_name: str,
                             parameters: dict) -> ParsedDocument:
        unstructured_document = UnstructuredDocument(lines=[], tables=[], attachments=[])
        unstructured_document = self.document_metadata_extractor.add_metadata(document=unstructured_document,
                                                                              directory=directory,
                                                                              filename=filename,
                                                                              converted_filename=converted_filename,
                                                                              original_filename=original_file_name,
                                                                              parameters=parameters,
                                                                              version=self.version)
        metadata = DocumentMetadata(**unstructured_document.metadata)
        return ParsedDocument(content=get_empty_content(), metadata=metadata, version=self.version)
