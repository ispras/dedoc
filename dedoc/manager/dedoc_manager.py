import copy
import logging
import os
import shutil
import tempfile
import uuid
from queue import Queue
from threading import Thread
from time import sleep
from typing import Optional, List, Dict

from werkzeug.datastructures import FileStorage

from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.configuration_manager import get_manager_config
from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.utils import get_unique_name


class ThreadManager(Thread):

    def __init__(self, manager_config: dict, queue: Queue, result: dict, logger: logging.Logger, version: str):
        Thread.__init__(self)
        self.version = version
        self.converter = manager_config["converter"]
        self.attachments_extractor = manager_config["attachments_extractor"]
        self.reader = manager_config["reader"]
        self.structure_constructor = manager_config["structure_constructor"]
        self.document_metadata_extractor = manager_config["document_metadata_extractor"]
        self.queue = queue
        self.result = result
        self.logger = logger

    def run(self):
        while True:
            if self.queue.empty():
                sleep(0.3)
            else:
                self.logger.debug("{} files to handle".format(self.queue.qsize()))
                uid, directory, filename, parameters, original_file_name = self.queue.get()
                self.logger.info("start handle file {}".format(filename))
                with tempfile.TemporaryDirectory() as tmp_dir:
                    file_original = os.path.join(directory, filename)
                    file_new_location = os.path.join(tmp_dir, filename)
                    self.logger.debug("move file from {} to {}".format(file_original, file_new_location))
                    shutil.move(file_original, file_new_location)
                    try:
                        result = self.__parse_file(tmp_dir=tmp_dir,
                                                   filename=filename,
                                                   parameters=parameters,
                                                   original_file_name=original_file_name)
                        self.logger.info("finish handle file {}".format(original_file_name))
                        self.result[uid] = result
                    except Exception as e:
                        self.result[uid] = e

    def __parse_file(self,
                     tmp_dir: str,
                     filename: str,
                     parameters: Dict[str, str],
                     original_file_name: str) -> ParsedDocument:
        """
        Function of complete parsing document with 'filename' with attachment files analyze
        """
        self.logger.info("start handle {}".format(filename))
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

        with_attachments = parameters.get("with_attachments", "False").lower() == "true"

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
                    parsed_attachment_files.append(self.__parse_file(tmp_dir=tmp_dir,
                                                                     filename=attachment.get_filename_in_path(),
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


class DedocManager(object):

    @staticmethod
    def from_config(version: str, tmp_dir: Optional[str] = None, *, config: dict) -> "DedocManager":
        manager_config = get_manager_config(config=config)

        if tmp_dir is not None and not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)

        result = {}
        queue = Queue()
        logger = config.get("logger")
        logger = logger if logger is not None else logging.getLogger(__name__)
        thread_manager = ThreadManager(manager_config=manager_config,
                                       queue=queue,
                                       result=result,
                                       logger=logger,
                                       version=version)
        thread_manager.start()
        return DedocManager(tmp_dir=tmp_dir,
                            thread_manager=thread_manager,
                            queue=queue,
                            result=result,
                            logger=logger,
                            config=config,
                            version=version)

    def __init__(self,
                 tmp_dir: str,
                 thread_manager: ThreadManager,
                 queue: Queue,
                 result: dict,
                 logger: logging.Logger,
                 version: str,
                 *,
                 config: dict
                 ):
        self.version = version
        self.tmp_dir = tmp_dir
        self.queue = queue
        self.result = result
        self.thread_manager = thread_manager
        self.logger = logger
        self.config = config

    def parse_file(self, file: FileStorage, parameters: Dict[str, str]) -> ParsedDocument:
        original_filename = file.filename.split("/")[-1]
        self.logger.info("get file {}".format(original_filename))
        filename = get_unique_name(original_filename)
        self.logger.info("rename file {} to {}".format(original_filename, filename))

        if self.tmp_dir is None:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = os.path.join(tmp_dir, filename)
                file.save(tmp_path)
                return self.__parse_file(
                    tmp_dir=tmp_dir,
                    filename=filename,
                    parameters=parameters,
                    original_file_name=original_filename
                )

        tmp_path = os.path.join(self.tmp_dir, filename)
        file.save(tmp_path)
        return self.__parse_file(
            tmp_dir=self.tmp_dir,
            filename=filename,
            parameters=parameters,
            original_file_name=original_filename
        )

    def parse_existing_file(self, path: str, parameters: Dict[str, str]) -> ParsedDocument:
        self.logger.info("parse existing file {}".format(path))
        with open(path, 'rb') as fp:
            file = FileStorage(fp, filename=path)
            return self.parse_file(file=file, parameters=parameters)

    def __parse_file(self, tmp_dir: str, filename: str, parameters: dict, original_file_name: str) -> ParsedDocument:
        uid = str(uuid.uuid1())
        self.logger.info("put file in queue {}".format(filename))
        self.queue.put((uid, tmp_dir, filename, parameters, original_file_name))
        while uid not in self.result:
            sleep(0.3)
        result = self.result.pop(uid)
        if isinstance(result, Exception):
            raise result
        return result
