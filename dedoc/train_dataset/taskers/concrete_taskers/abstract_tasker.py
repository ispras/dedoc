import json
import os
import zipfile
from typing import Iterable, List
from abc import ABC, abstractmethod


class AbstractTasker(ABC):

    resources_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "resources"))

    @abstractmethod
    def create_tasks(self, task_size: int, tasks_uid: str) -> Iterable[str]:
        """
        create tasks one by one, put them into zip archive and return path to this archive.
        warning it will remove archive with previous task before starts to form new task.
        Every task archive should be self contained: it mast include images, task config, manifest and so on
        @param task_size: size of one task, task should not be large than this. For example number of page.
        @param tasks_uid: uid of task
        @return: path to the zip archive with task.
        """
        pass

    @abstractmethod
    def get_original_documents(self) -> str:
        """
        return path to archive with original files
        @return:
        """
        pass

    def _read_json(self, path: str, required: bool = False) -> List[dict]:
        if os.path.exists(path):
            with open(path) as file:
                return [json.loads(line) for line in file]
        elif not required:
            return []
        else:
            raise Exception("file not found {}".format(path))

    def _add_docker_files(self,
                          archive: zipfile.ZipFile,
                          task_directory: str,
                          dockerfile_directory: str) -> zipfile.ZipFile:
        """
        add some common files to task archive (in place)
        @param archive: task archive
        @param task_directory: name of directory with task
        @param dockerfile_directory: name of directory with dockerfile
        @return: archive with docker file
        """

        docker_path = os.path.join(self.resources_path, "train_dataset", dockerfile_directory, "Dockerfile")
        archive.write(filename=docker_path, arcname="{}/Dockerfile".format(task_directory))
        readme_path = os.path.join(self.resources_path, "train_dataset", dockerfile_directory, "README.md")
        archive.write(filename=readme_path, arcname="{}/README.md".format(task_directory))
        run_path = os.path.join(self.resources_path, "train_dataset", dockerfile_directory, "run.sh")
        archive.write(filename=run_path, arcname="{}/run.sh".format(task_directory))
        return archive

    def _add_config(self,
                    task_archive: zipfile.ZipFile,
                    task_name: str,
                    task_directory: str,
                    config_path: str,
                    tmp_dir: str) -> None:
        config = json.load(open(config_path))
        config["output_path"] = config.get("output_path", "labeled.json").replace("TASK_ID", task_name)
        new_config_path = os.path.join(tmp_dir, os.path.basename(config_path))
        with open(new_config_path, "w") as file:
            json.dump(obj=config, fp=file, ensure_ascii=False, indent=4)
        task_archive.write(new_config_path, os.path.join(task_directory, os.path.basename(config_path)))
        os.remove(new_config_path)
