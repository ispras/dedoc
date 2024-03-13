import json
import os
import re
import tempfile
import time
import unittest
import zipfile

import requests


class TestApiTaskers(unittest.TestCase):
    data_directory_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
    host = os.environ.get("HOST", "localhost")
    port = int(os.environ.get("PORT", "1232"))
    uid_reg = re.compile(r"\?uid=(.*)\"")
    result_archive_reg = re.compile(r"<a href=\"/return-file/(.*)\" target=\"blank\">")

    def tearDown(self) -> None:
        requests.get(f"http://{self.host}:{self.port}/clear")

    def test_info(self) -> None:
        r = requests.get(f"http://{self.host}:{self.port}/")
        self.assertEqual(200, r.status_code)

    def test_line_label_tasker(self) -> None:
        archive_name = "archive.zip"
        self.__test_any_tasker(data=dict(type_of_task="law_classifier", document_type="law"), archive_name=archive_name)
        self.__test_any_tasker(data=dict(type_of_task="tz_classifier", document_type="tz"), archive_name=archive_name)
        self.__test_any_tasker(data=dict(type_of_task="paragraph_classifier"), archive_name=archive_name)

    def test_filtered_line_label_tasker(self) -> None:
        self.__test_any_tasker(data=dict(type_of_task="diploma_classifier", document_type="diploma"), archive_name="diploma_archive.zip")

    def test_header_footer_tasker(self) -> None:
        self.__test_any_tasker(data=dict(type_of_task="header_classifier"), archive_name="archive.zip")

    def test_table_tasker(self) -> None:
        self.__test_any_tasker(data=dict(type_of_task="tables_classifier"), archive_name="tables_archive.zip", test_original_documents=False)

    def __test_any_tasker(self, data: dict, archive_name: str, test_original_documents: bool = True) -> None:
        task_uid = self._send_archive(archive_name, data=data)
        with tempfile.TemporaryDirectory() as tmp_dir:
            result_archive_path = self._get_result_archive(uid=task_uid, tmp_dir=tmp_dir)

            with zipfile.ZipFile(result_archive_path) as archive:
                name_list = archive.namelist()
                for file_name in ["original_documents.zip", "formInput.html", "formResult.html", "task_manager.py", "parameters.json"]:
                    self.assertIn(file_name, name_list)
                archive.extractall(tmp_dir)

            if test_original_documents:
                with zipfile.ZipFile(os.path.join(tmp_dir, "original_documents.zip")) as output_archive:
                    output_archive_extensions = sorted([os.path.splitext(file_name)[-1] for file_name in output_archive.namelist()])
                with zipfile.ZipFile(os.path.join(self.data_directory_path, archive_name)) as input_archive:
                    input_archive_extensions = sorted([os.path.splitext(file_name)[-1] for file_name in input_archive.namelist()])
                self.assertListEqual(output_archive_extensions, input_archive_extensions, "Documents of the task should contain all input documents")

            task_archive_name = [file_name for file_name in name_list if file_name.startswith("task_") and file_name.endswith(".zip")][0]
            with zipfile.ZipFile(os.path.join(tmp_dir, task_archive_name)) as task_archive:
                task_name_list = [os.path.basename(file_name) for file_name in task_archive.namelist()]
                for file_name in ["config.json", "Dockerfile", "manifest.pdf", "README.md", "run.sh", "tasks.json"]:
                    self.assertIn(file_name, task_name_list)
                task_archive.extractall(tmp_dir)

            task_dir_path = os.path.join(tmp_dir, os.path.splitext(task_archive_name)[0])
            with open(os.path.join(task_dir_path, "tasks.json")) as tasks_file:
                tasks_dict = json.load(tasks_file)
            for task in tasks_dict.values():
                self.assertTrue(os.path.exists(os.path.join(task_dir_path, task["task_path"])), f'{task["task_path"]} does not exist')

    def _send_archive(self, file_name: str, data: dict = None) -> str:
        data = {} if data is None else data
        abs_path = os.path.join(self.data_directory_path, file_name)

        with open(abs_path, "rb") as file:
            r = requests.post(f"http://{self.host}:{self.port}/upload_archive", files={"file": (file_name, file)}, data=data)
        self.assertEqual(201, r.status_code)

        uid_match = self.uid_reg.findall(r.content.decode())
        self.assertEqual(1, len(uid_match))
        return uid_match[0]

    def _get_result_archive(self, uid: str, tmp_dir: str) -> str:
        r = requests.get(f"http://{self.host}:{self.port}/get_result_archive?uid={uid}")
        self.assertIn(r.status_code, (200, 202))

        while r.status_code == 202:
            r = requests.get(f"http://{self.host}:{self.port}/get_result_archive?uid={uid}")
            time.sleep(10)
        self.assertEqual(200, r.status_code)

        result_archive_match = self.result_archive_reg.findall(r.content.decode())
        self.assertEqual(1, len(result_archive_match))
        archive_name = result_archive_match[0]
        r = requests.get(f"http://{self.host}:{self.port}/return-file/{archive_name}")
        self.assertEqual(200, r.status_code)

        archive_out_path = os.path.join(tmp_dir, archive_name)
        with open(archive_out_path, "wb") as f:
            f.write(r.content)
        return archive_out_path
