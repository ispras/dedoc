import copy
import logging
import os
import shutil
import tempfile
from typing import Optional, List, Dict

from dedoc.attachments_extractors.attachments_extractor_composition import AttachmentsExtractorComposition
from dedoc.converters.file_converter import FileConverterComposition
from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.metadata_extractor.metadata_extractor_composition import MetadataExtractorComposition
from dedoc.readers.reader_composition import ReaderComposition
from dedoc.structure_constructor.structure_constructor_composition import StructureConstructorComposition
from dedoc.utils import get_unique_name


class DedocManager:

    def __init__(self,
                 converter: FileConverterComposition,
                 attachments_extractor: AttachmentsExtractorComposition,
                 reader: ReaderComposition,
                 structure_constructor: StructureConstructorComposition,
                 document_metadata_extractor: MetadataExtractorComposition,
                 logger: logging.Logger,
                 version: str):
        self.version = version
        self.converter = converter
        self.attachments_extractor = attachments_extractor
        self.reader = reader
        self.structure_constructor = structure_constructor
        self.document_metadata_extractor = document_metadata_extractor
        self.logger = logger

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
            attachments_extractor=manager_config["attachments_extractor"],
            reader=manager_config["reader"],
            structure_constructor=manager_config["structure_constructor"],
            document_metadata_extractor=manager_config["document_metadata_extractor"],
            logger=logger,
            version=version
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
        :param original_file_name: name of original file (None if file was not ranamed)
        :return:
        """
        if not os.path.isfile(path=file_path):
            raise FileNotFoundError()
        self.logger.info("start handle {}".format(file_path))
        if original_file_name is None:
            original_file_name = os.path.basename(file_path)
        filename = get_unique_name(file_path)
        with tempfile.TemporaryDirectory() as tmp_dir:
            shutil.copy(file_path, os.path.join(tmp_dir, filename))

            # Step 1 - Converting
            filename_convert = self.converter.do_converting(tmp_dir, filename, parameters=parameters)
            self.logger.info("finish conversion {} -> {}".format(filename, filename_convert))
            # Step 2 - Parsing content of converted file
            unstructured_document, contains_attachments = self.reader.parse_file(
                tmp_dir=tmp_dir,
                filename=filename_convert,
                parameters=parameters
            )
            self.logger.info("parse file {}".format(filename_convert))
            document_content = self.structure_constructor.structure_document(document=unstructured_document,
                                                                             structure_type=parameters.get(
                                                                                 "structure_type")
                                                                             )
            self.logger.info("get document content {}".format(filename_convert))
            # Step 3 - Adding meta-information
            parsed_document = self.__parse_file_meta(document_content=document_content,
                                                     directory=tmp_dir,
                                                     filename=filename,
                                                     converted_filename=filename_convert,
                                                     original_file_name=original_file_name,
                                                     parameters=parameters)
            self.logger.info("get structure and metadata {}".format(filename_convert))

            with_attachments = str(parameters.get("with_attachments", "False")).lower() == "true"

            if with_attachments:
                self.logger.info("start handle attachments")
                parsed_attachment_files = self.__get_attachments(filename=filename_convert,
                                                                 need_analyze_attachments=contains_attachments,
                                                                 parameters=parameters,
                                                                 tmp_dir=tmp_dir)
                self.logger.info("get attachments {}".format(filename_convert))
                parsed_document.add_attachments(parsed_attachment_files)
            parsed_document.version = self.version
            self.logger.info("finish handle {}".format(filename))
        return parsed_document

    def __parse_file_meta(self,
                          document_content: Optional[DocumentContent],
                          directory: str,
                          filename: str,
                          converted_filename: str,
                          original_file_name: str,
                          parameters: dict) -> ParsedDocument:
        """
        Decorator with metainformation
        document_content - None for unsupported document in attachments
        """
        parsed_document = self.document_metadata_extractor.add_metadata(doc=document_content,
                                                                        directory=directory,
                                                                        filename=filename,
                                                                        converted_filename=converted_filename,
                                                                        original_filename=original_file_name,
                                                                        parameters=parameters)
        return parsed_document

    def __get_attachments(self,
                          filename: str,
                          need_analyze_attachments: bool,
                          parameters: dict,
                          tmp_dir: str) -> List[ParsedDocument]:
        parsed_attachment_files = []
        if need_analyze_attachments:
            attachment_files = self.attachments_extractor.get_attachments(tmp_dir=tmp_dir,
                                                                          filename=filename,
                                                                          parameters=parameters)
            for attachment in attachment_files:
                parameters_copy = copy.deepcopy(parameters)
                parameters_copy["is_attached"] = True
                parameters_copy["attachment"] = attachment
                try:
                    file_path = os.path.join(tmp_dir, attachment.get_filename_in_path())
                    parsed_attachment_files.append(self.parse_file(file_path,
                                                                   parameters=parameters_copy,
                                                                   original_file_name=attachment.get_original_filename()
                                                                   ))
                except BadFileFormatException:
                    # return empty ParsedDocument with Meta information
                    parsed_attachment_files.append(
                        self.__parse_file_meta(document_content=None,
                                               directory=tmp_dir,
                                               filename=attachment.get_filename_in_path(),
                                               converted_filename=attachment.get_filename_in_path(),
                                               original_file_name=attachment.get_original_filename(),
                                               parameters=parameters_copy))

        return parsed_attachment_files
