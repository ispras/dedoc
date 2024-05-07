import json
import logging
import os
import random
import uuid
import zipfile
from collections import OrderedDict, defaultdict
from io import BytesIO
from tempfile import TemporaryDirectory
from typing import Callable, Iterable, List

from dedoc.utils.train_dataset_utils import get_original_document_path
from train_dataset.data_structures.images_archive import ImagesArchive
from train_dataset.data_structures.task_item import TaskItem
from train_dataset.taskers.concrete_taskers.abstract_tasker import AbstractTasker
from train_dataset.taskers.images_creators.concrete_creators.docx_images_creator import DocxImagesCreator
from train_dataset.taskers.images_creators.concrete_creators.scanned_images_creator import ScannedImagesCreator
from train_dataset.taskers.images_creators.concrete_creators.txt_images_creator import TxtImagesCreator
from train_dataset.taskers.images_creators.image_creator_composition import ImageCreatorComposition


class LineLabelTasker(AbstractTasker):

    def __init__(self,
                 path2lines: str,
                 path2docs: str,
                 manifest_path: str,
                 config_path: str,
                 tmp_dir: str,
                 progress_bar: dict = None,
                 item2label: Callable = None,
                 *,
                 config: dict) -> None:
        """
        @param path2lines: path to file with line with meta information
        @param path2docs: path to images (or original document)
        @param manifest_path: path to manifest file (instruction for annotator)
        @param config_path: path to the config for labeling tools
        """
        if not os.path.isdir(tmp_dir):
            os.makedirs(tmp_dir)
        self.progress_bar = {} if progress_bar is None else progress_bar
        self.tmp_dir = tmp_dir
        self.config_path = config_path
        self.manifest_path = manifest_path
        self.path2docs = path2docs
        self.path2lines = path2lines
        self.item2label = item2label if item2label is not None else (lambda t: None)
        self.config = config
        self.logger = config.get("logger", logging.getLogger())
        self._page_counter = 0
        with open(self.config_path) as file:
            self.labels2color = {d["label"]: d["color"] for d in json.load(file)["labels"]}

        self._symbols = "23456789ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz"

        self.images_creators = ImageCreatorComposition(creators=[
            ScannedImagesCreator(path2docs=self.path2docs),
            DocxImagesCreator(path2docs=self.path2docs, config=config),
            TxtImagesCreator(path2docs=self.path2docs, config=config)
        ])

    def create_tasks(self, task_size: int, tasks_uid: str = None) -> Iterable[str]:
        with TemporaryDirectory() as tmpdir:
            if tasks_uid is None:
                tasks_uid = uuid.uuid1()
            pages = self._get_pages()
            images = self._create_images(pages, tmpdir=tmpdir)
            random.shuffle(pages)
            batches = list(enumerate(self._task_batch(pages=pages, size=task_size)))
            for task_id, task in batches:
                self.progress_bar[tasks_uid] = f"done = {task_id};  total = {len(batches)}  in progress = 1"
                path = self._create_one_task(task=task, task_id=task_id, job_uid=tasks_uid, images=images)
                yield path
                os.remove(path)

    def get_original_documents(self) -> str:
        pages = self._get_pages()
        path = os.path.join(self.tmp_dir, "original_documents.zip")
        with zipfile.ZipFile(path, "w") as task_archive:
            for page in pages:
                image_name = get_original_document_path(self.path2docs, page)
                task_archive.write(image_name, os.path.basename(image_name))
        return path

    def _task_batch(self, pages: Iterable[List[dict]], size: int) -> Iterable[List[List[dict]]]:
        task = []
        current_size = 0
        for page in pages:
            new_page = []
            for item in page:
                new_page.append(item)
                current_size += 1
                if current_size >= size:
                    task.append(new_page)
                    yield task
                    new_page = []
                    task = []
                    current_size = 0
            if len(new_page) > 0:
                task.append(new_page)
        if len(task) > 0:
            yield task

    def _create_one_task(self, task: List[List[dict]], task_id: int, job_uid: str, *, images: ImagesArchive) -> str:
        task_name = f"{task_id:06d}_{''.join(random.sample(self._symbols, 3))}"
        task_directory = f"task_{task_name}"
        path = os.path.join(self.tmp_dir, f"{task_directory}.zip")
        task_items = OrderedDict()
        item_id = 0
        with zipfile.ZipFile(path, "w") as task_archive:
            for page in task:
                # add original files
                document_name = get_original_document_path(self.path2docs, page)
                archive_name = os.path.join(task_directory, "original_document", os.path.basename(document_name))
                task_archive.write(document_name, archive_name)

                page = [line for line in page if line["_line"].strip() != ""]
                if len(page) == 0:
                    continue
                items = self._one_scanned_page(page=page, task_archive=task_archive, task_directory=task_directory, images=images)
                for item in items:
                    item.task_id = item_id
                    item_id += 1
                    task_items[item.task_id] = item.to_dict()
            task_archive.writestr(f"{task_directory}/tasks.json", json.dumps(task_items, ensure_ascii=False, indent=4).encode("utf-8"))
            task_archive.write(self.manifest_path, os.path.join(task_directory, os.path.basename(self.manifest_path)))
            self._add_config(task_archive, task_name=task_name, task_directory=task_directory, config_path=self.config_path, tmp_dir=self.tmp_dir)
            self._add_docker_files(archive=task_archive, task_directory=task_directory, dockerfile_directory="img_classifier_dockerfile")
        return path

    def _get_pages(self) -> List[List[dict]]:
        lines = self._read_json(self.path2lines, required=True)
        pages = defaultdict(list)
        for line in lines:
            if "original_document" in line:
                document_name = line["original_document"]
                if os.path.isfile(os.path.join(self.path2docs, document_name)):
                    pages[document_name].append(line)
        for value in pages.values():
            value.sort(key=lambda line: (line["_metadata"]["page_id"], line["_metadata"]["line_id"]))
        return list(pages.values())

    def _create_images(self, pages: List[List[dict]], tmpdir: str) -> ImagesArchive:
        for page in pages:
            for line in page:
                labels = self.item2label(line)
                color = self.labels2color.get(labels, "black") if labels else "black"
                line["color"] = color
        return self.images_creators.create_images(pages=pages, tmpdir=tmpdir)

    def _one_scanned_page(self, page: List[dict], task_archive: zipfile.ZipFile, task_directory: str, *, images: ImagesArchive) -> List[TaskItem]:
        self._page_counter += 1
        task_items = []

        for i, line in enumerate(page):
            uid = line["_uid"]
            image_bbox_name = f"images/{self._page_counter:0>6d}_{i:0>6d}_img_bbox_{uid}.jpg"
            image_bbox = images.get_page_by_uid(f"{uid}.jpg")
            if image_bbox is None:
                if not uid.endswith("_split"):
                    self.logger.warn(f"uid {uid} not found")
                continue
            with BytesIO() as buffer:
                image_bbox.convert("RGB").save(fp=buffer, format="jpeg")
                task_archive.writestr(zinfo_or_arcname=os.path.join(task_directory, image_bbox_name), data=buffer.getvalue())

            line_id = line["_metadata"]["line_id"]
            page_id = line["_metadata"]["page_id"]
            text = line["_line"]
            task_item = TaskItem(
                task_id=len(task_items),
                task_path=image_bbox_name,
                data=line,
                labeled=[line["_metadata"]["hierarchy_level"]["line_type"]],
                additional_info=f"<p><em>page_id</em> {page_id} </p><p><em>line_id</em> {line_id} </p><p><em> text</em> {text}</p>",
                default_label=self.item2label(line)
            )
            task_items.append(task_item)
        return task_items
