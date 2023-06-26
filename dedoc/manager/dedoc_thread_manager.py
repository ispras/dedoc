import logging
import os
import shutil
import tempfile
import uuid
from queue import Queue
from threading import Thread
from time import sleep
from typing import Optional, Dict

from fastapi import UploadFile

from dedoc.configuration_manager import get_manager_config
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.manager.dedoc_manager import DedocManager
from dedoc.utils.utils import get_unique_name


class ThreadManager(Thread):

    def __init__(self,
                 manager_config: dict,
                 queue: Queue,
                 result: dict,
                 logger: logging.Logger,
                 version: str,
                 *,
                 config: dict) -> None:
        Thread.__init__(self)
        self.version = version
        self.converter = manager_config["converter"]
        self.reader = manager_config["reader"]
        self.structure_constructor = manager_config["structure_constructor"]
        self.document_metadata_extractor = manager_config["document_metadata_extractor"]
        self.attachments_extractor = manager_config["attachments_extractor"]
        self.queue = queue
        self.result = result
        self.logger = logger

        self.manager = DedocManager.from_config(version=version, manager_config=manager_config, config=config)

    def run(self) -> None:
        sleep_time = 0.01
        while True:
            if self.queue.empty():
                sleep(sleep_time)
                sleep_time = min(sleep_time * 2, 1)
            else:
                sleep_time = 0.01
                self.logger.info("{} files to handle".format(self.queue.qsize()))
                uid, directory, filename, parameters, original_file_name = self.queue.get()
                self.logger.info("Start handle file {}".format(filename))
                with tempfile.TemporaryDirectory() as tmp_dir:
                    file_original = os.path.join(directory, filename)
                    file_new_location = os.path.join(tmp_dir, filename)
                    self.logger.debug("Move file from {} to {}".format(file_original, file_new_location))
                    shutil.move(file_original, file_new_location)
                    try:
                        result = self.manager.parse_file(file_path=file_new_location,
                                                         parameters=parameters,
                                                         original_file_name=original_file_name)
                        self.logger.info("Finish handle file {}".format(original_file_name))
                        self.result[uid] = result
                    except Exception as e:
                        self.result[uid] = e


class DedocThreadedManager(object):

    @staticmethod
    def from_config(version: str, tmp_dir: Optional[str] = None, *, config: dict) -> "DedocThreadedManager":
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
                                       version=version,
                                       config=config)
        thread_manager.start()
        return DedocThreadedManager(tmp_dir=tmp_dir,
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
                 config: dict) -> None:
        self.version = version
        self.tmp_dir = tmp_dir
        self.queue = queue
        self.result = result
        self.thread_manager = thread_manager
        self.logger = logger
        self.config = config

    def parse_file(self, file: UploadFile, parameters: Dict[str, str]) -> ParsedDocument:
        original_filename = file.filename.split("/")[-1]
        self.logger.info("Get file {}".format(original_filename))
        filename = get_unique_name(original_filename)
        self.logger.info("Rename file {} to {}".format(original_filename, filename))

        if self.tmp_dir is None:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = os.path.join(tmp_dir, filename)
                with open(tmp_path, "wb") as df:
                    shutil.copyfileobj(file.file, df)

                return self.__parse_file(
                    tmp_dir=tmp_dir,
                    filename=filename,
                    parameters=parameters,
                    original_file_name=original_filename
                )

        tmp_path = os.path.join(self.tmp_dir, filename)
        with open(tmp_path, "wb") as df:
            shutil.copyfileobj(file.file, df)
        return self.__parse_file(
            tmp_dir=self.tmp_dir,
            filename=filename,
            parameters=parameters,
            original_file_name=original_filename
        )

    def parse_existing_file(self, path: str, parameters: Dict[str, str]) -> ParsedDocument:
        self.logger.info("Parse existing file {}".format(path))
        with open(path, 'rb') as fp:
            file = UploadFile(file=fp, filename=path)
            return self.parse_file(file=file, parameters=parameters)

    def __parse_file(self, tmp_dir: str, filename: str, parameters: dict, original_file_name: str) -> ParsedDocument:
        sleep_time = 0.01
        uid = str(uuid.uuid1())
        self.logger.info("Put file in queue {}".format(filename))
        self.queue.put((uid, tmp_dir, filename, parameters, original_file_name))
        while uid not in self.result:
            sleep(sleep_time)
            sleep_time = min(0.3, sleep_time * 2)
        result = self.result.pop(uid)
        if isinstance(result, Exception):
            raise result
        return result
