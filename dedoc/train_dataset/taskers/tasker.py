import logging
import math
import os
import random
import uuid
from typing import Tuple, Dict, Optional
from zipfile import ZipFile

from dedoc.train_dataset.exceptions.unknown_task import UnknownTaskException
from dedoc.train_dataset.taskers.concrete_taskers.abstract_tasker import AbstractTasker
import warnings


class Tasker(object):

    def __init__(self,
                 boxes_label_path: str,
                 line_info_path: str,
                 images_path: str,
                 save_path: str,
                 concrete_taskers: Dict[str, AbstractTasker],
                 tmd_dir: str = "/tmp",
                 progress_bar: dict = None,
                 *,
                 config: dict) -> None:
        """
        :param boxes_label_path: abs path to boxes.jsonlines file
        :param line_info_path: abs path to lines.jsonlines
        :param images_path: abs path to folder of images
        :param save_path: abs path to save of result archive of tasks
        :param tmd_dir: path for intermediate files
        :param config: any other parameters
        """

        self.config = config if config is not None else {}
        self.boxes_label_path = boxes_label_path
        self.line_info_path = line_info_path
        self.images_path = images_path
        os.makedirs(save_path, exist_ok=True)
        self.save_path = save_path
        self.logger = config.get("logger", logging.getLogger())
        self.tmd_dir = tmd_dir
        self.concrete_taskers = concrete_taskers
        self.progress_bar = {} if progress_bar is None else progress_bar
        resources_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "resources", "train_dataset")
        self.resources = os.path.abspath(resources_path)

    def create_tasks(self,
                     type_of_task: str,
                     count_tasks: int = None,
                     task_size: int = None,
                     task_uid: Optional[str] = None) -> Tuple[str, int]:
        """
        creates subtasks with help of ConcreteTaskers and return common archive of tasks
        :param type_of_task: task type for calling concrete tasker (for example type_of_task='line_classifier')
        :param task_size: size of one task, task should not be large than this. For example number of page.
        :param count_tasks: number of tasks
        :param task_uid: unique id of task
        :return: archive of tasks, task size
        """
        task_uid = str(uuid.uuid1()) if task_uid is None else task_uid
        self.progress_bar[task_uid] = "Form task (in progress)"
        if task_size is None and count_tasks is None:
            raise Exception("Task size undefined")
        elif count_tasks is not None and task_size is None:
            warnings.warn("count_tasks is deprecated, use task_size")
            task_size = math.ceil(len(os.listdir(self.images_path)) / count_tasks)
        elif count_tasks is not None and task_size is not None:
            warnings.warn("count_tasks is deprecated, ignore its value and use task_size")

        if type_of_task not in self.concrete_taskers:
            raise UnknownTaskException(type_of_task)
        tasker = self.concrete_taskers[type_of_task]
        path_to_common_zip = os.path.join(self.save_path,
                                          "{}_{:06d}.zip".format(type_of_task, random.randint(0, 1000000)))

        with ZipFile(path_to_common_zip, "w") as tasks_archive:
            for task_path in tasker.create_tasks(task_size=task_size,
                                                 tasks_uid=task_uid):
                task_name = os.path.basename(task_path)
                tasks_archive.write(filename=task_path, arcname=task_name)
                self.logger.info(self.progress_bar)
            original_documents = tasker.get_original_documents()
            tasks_archive.write(original_documents, os.path.basename(original_documents))
            os.remove(original_documents)
            self._add_special(tasks_archive)

        self.progress_bar.pop(task_uid)
        return path_to_common_zip, task_size

    def _add_special(self, tasks_archive: ZipFile) -> None:
        task_manager = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "task_manager.py"))
        form_input = os.path.join(self.resources, "formInput.html")
        form_result = os.path.join(self.resources, "formResult.html")

        for path in (task_manager, form_input, form_result):
            tasks_archive.write(path, os.path.basename(path))
