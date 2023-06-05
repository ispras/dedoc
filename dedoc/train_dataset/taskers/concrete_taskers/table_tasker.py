import json
import os
import tempfile
from typing import Iterable, List, Optional
from zipfile import ZipFile

from PIL import Image

from dedoc.data_structures.bbox import BBox
from dedoc.train_dataset.data_path_config import table_path
from dedoc.train_dataset.data_structures.task_item import TaskItem
from dedoc.train_dataset.taskers.concrete_taskers.abstract_tasker import AbstractTasker
from dedoc.utils.utils import get_batch
from dedoc.utils.image_utils import draw_rectangle


class File:
    def __init__(self, image_path: str, json_path: str) -> None:
        assert os.path.isfile(image_path)
        assert os.path.isfile(json_path)
        self.image_path = image_path
        self.json_path = json_path

    @property
    def name(self) -> str:
        return os.path.basename(self.image_path).split(".")[0]

    @property
    def data(self) -> dict:
        with open(self.json_path) as file_in:
            return json.load(file_in)


class TableTasker(AbstractTasker):

    def create_tasks(self, task_size: int, tasks_uid: str) -> Iterable[str]:
        files = self._get_files()
        with tempfile.TemporaryDirectory() as tmp_dir:
            for i, batch in enumerate(get_batch(task_size, files)):
                task_directory = "task_{:03d}".format(i)
                archive_path = "/tmp/{}.zip".format(task_directory)
                image_directory = "{}/images".format(task_directory)
                with ZipFile(archive_path, "a") as task_archive:
                    self.__add_task(archive=task_archive, files=batch, task_directory=task_directory)
                    dockerfile_directory = os.path.join(self.resources_path, "train_dataset/img_classifier_dockerfile")
                    self._add_docker_files(archive=task_archive,
                                           task_directory=task_directory,
                                           dockerfile_directory=dockerfile_directory)
                    self._add_config(task_archive=task_archive,
                                     task_name=task_directory,
                                     task_directory=task_directory,
                                     config_path=os.path.join(self.resources_path, "train_dataset/tables/config.json"),
                                     tmp_dir=tmp_dir)
                    self.__add_images(files=files, archive=task_archive, image_directory=image_directory)
                yield archive_path

    def __add_task(self, archive: ZipFile, files: List[File], task_directory: str) -> None:
        task_items = {}
        for task_id, file in enumerate(files):
            data = file.data
            data["original_document"] = "{}.png".format(file.name)
            task_items[task_id] = TaskItem(task_id=task_id,
                                           task_path="images/{}".format(os.path.basename(file.image_path)),
                                           labeled=None,
                                           data=data,
                                           additional_info="",
                                           default_label="table").to_dict()
        archive.writestr("{}/tasks.json".format(task_directory),
                         json.dumps(task_items, ensure_ascii=False, indent=4).encode("utf-8"))

    def get_original_documents(self) -> str:
        archive_path = "/tmp/original_documents.zip"
        files = [file.image_path for file in self._get_files()]
        return self._add_files_to_archive(files=files, archive_path=archive_path)

    def _get_files(self) -> List[File]:
        files = {file.split(".")[0] for file in os.listdir(table_path)}
        result = []
        for file_name in sorted(files):
            image_path = os.path.join(table_path, "{}.png".format(file_name))
            json_path = os.path.join(table_path, "{}.json".format(file_name))
            file = File(image_path=image_path, json_path=json_path)
            result.append(file)
        return result

    def _add_files_to_archive(self, files: List[str], archive_path: str, directory: Optional[str] = None) -> str:
        with ZipFile(archive_path, "w") as out:
            for file in files:
                file_name = os.path.basename(file)
                if directory:
                    file_name = os.path.join(directory, file_name)
                out.write(file, file_name)
        return archive_path

    def __add_images(self, files: List[File], archive: ZipFile, image_directory: str) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            for file in files:
                image = Image.open(file.image_path)
                bbox = BBox.from_dict(file.data["locations"][0]["bbox"])
                image_rectangle = draw_rectangle(image=image,
                                                 x_top_left=bbox.x_top_left,
                                                 y_top_left=bbox.y_top_left,
                                                 width=bbox.width,
                                                 height=bbox.height,
                                                 color=(255, 0, 0))
                image_rectangle = Image.fromarray(image_rectangle)
                image_path = os.path.join(tmpdir, "{}.png".format(file.name))
                image_rectangle.save(image_path)
                archive.write(image_path, "{}/{}.png".format(image_directory, file.name))
