import os
import zipfile
from io import BytesIO
from typing import Callable, List

from train_dataset.data_structures.images_archive import ImagesArchive
from train_dataset.data_structures.task_item import TaskItem
from train_dataset.taskers.concrete_taskers.abstract_line_label_tasker import AbstractLineLabelTasker
from train_dataset.taskers.images_creators.concrete_creators.docx_images_creator import DocxImagesCreator
from train_dataset.taskers.images_creators.concrete_creators.scanned_images_creator import ScannedImagesCreator
from train_dataset.taskers.images_creators.concrete_creators.txt_images_creator import TxtImagesCreator
from train_dataset.taskers.images_creators.image_creator_composition import ImageCreatorComposition


class LineLabelTasker(AbstractLineLabelTasker):

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
        super().__init__(path2lines, path2docs, manifest_path, config_path, tmp_dir, progress_bar, item2label, config=config)
        self.images_creators = ImageCreatorComposition(creators=[
            ScannedImagesCreator(path2docs=self.path2docs),
            DocxImagesCreator(path2docs=self.path2docs, config=config),
            TxtImagesCreator(path2docs=self.path2docs, config=config)
        ])

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