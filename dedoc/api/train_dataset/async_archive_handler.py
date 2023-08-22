import logging
import os
import shutil
import time
import uuid
import zipfile
from queue import Queue
from tempfile import TemporaryDirectory
from threading import Thread

from fastapi import UploadFile

from dedoc.common.exceptions.bad_file_error import BadFileFormatError
from dedoc.dedoc_manager import DedocManager
from dedoc.train_dataset.taskers.tasker import Tasker


class _ArchiveHandler(Thread):

    def __init__(self, queue: Queue, results: dict, progress: dict, tasker: Tasker, manager: DedocManager, *, config: dict) -> None:
        Thread.__init__(self)
        self.progress = progress
        self.config = config
        self.queue = queue
        self.tasker = tasker
        self.tasker.progress_bar = self.progress
        self.manager = manager
        self.results = results
        self.logger = config.get("config", logging.getLogger())

    def run(self) -> None:
        while True:
            if self.queue.empty():
                time.sleep(1)
            else:
                uid, parameters, file = self.queue.get()
                self.results[uid] = self._handle_archive(path=file, parameters=parameters, uid=uid)
                self.logger.info(f"FINISH {uid}")

    def _handle_archive(self, uid: str, path: str, parameters: dict) -> str:
        try:
            with zipfile.ZipFile(path, "r") as archive:
                for i, file in enumerate(archive.namelist()):
                    self.progress[uid] = f"files done\t= {i} \n files_in_progress\t= {1}\n total\t= {len(archive.namelist())}"
                    self.__handle_one_file(archive, file, parameters)
                    self.progress[uid] = f"files done\t= {i + 1} \n files_in_progress\t= {0}\n total\t= {len(archive.namelist())}"

            task, _ = self.tasker.create_tasks(
                type_of_task=parameters["type_of_task"],
                task_size=int(parameters["task_size"]),
                task_uid=uid
            )
            return task
        except Exception as e:
            self.progress[uid] = f"Fail with\n{e}"
            raise e

    def __handle_one_file(self, archive: zipfile.ZipFile, file: str, parameters: dict) -> None:
        self.logger.info(f"Start handle {file}")
        with TemporaryDirectory() as tmpdir:
            try:
                with archive.open(file) as item:
                    uid = str(uuid.uuid1()) + "." + file.split(".")[-1]
                    path_out = os.path.join(tmpdir, uid)
                    os.makedirs(os.path.dirname(path_out), exist_ok=True)
                    if not path_out.endswith("/"):
                        with open(path_out, "wb") as file_out:
                            file_out.write(item.read())
                        self.manager.parse(file_path=path_out, parameters=parameters)
            except BadFileFormatError as e:
                self.logger.warning(f"Can't handle file {file}, exception {str(e)}")
        self.logger.info(f"Finish handle {file}")


class AsyncHandler:

    def __init__(self, tasker: Tasker, manager: DedocManager, *, config: dict) -> None:
        super().__init__()
        self.queue = Queue()
        self.__results = {}
        self._progress = tasker.progress_bar
        self._handler = _ArchiveHandler(
            queue=self.queue,
            progress=self._progress,
            manager=manager,
            tasker=tasker,
            config=config,
            results=self.__results)
        self._handler.start()
        self.tmp_dir = TemporaryDirectory()

    def handle(self, file: UploadFile, parameters: dict) -> str:
        assert file.filename.lower().endswith(".zip")
        uid = str(uuid.uuid1())
        path = os.path.join(self.tmp_dir.name, uid + ".zip")
        with open(path, "wb") as df:
            shutil.copyfileobj(file.file, df)
        self.queue.put((uid, parameters, path))
        return str(uid)

    def is_ready(self, uid: str) -> bool:
        return uid in self.__results

    def get_progress(self, uid: str) -> str:
        return self._progress.get(uid, "")

    def get_results(self, uid: str) -> str:
        assert self.is_ready(uid)
        return self.__results[uid]
