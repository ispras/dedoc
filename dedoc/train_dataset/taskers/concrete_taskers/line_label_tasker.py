import os
import zipfile
from io import BytesIO
from typing import List, Callable

from dedoc.train_dataset.data_structures.images_archive import ImagesArchive
from dedoc.train_dataset.data_structures.task_item import TaskItem
from dedoc.train_dataset.taskers.concrete_taskers.abstract_line_label_tasker import AbstractLineLabelTasker
from dedoc.train_dataset.taskers.images_creators.concrete_creators.docx_images_creator import DocxImagesCreator
from dedoc.train_dataset.taskers.images_creators.concrete_creators.scanned_images_creator import ScannedImagesCreator
from dedoc.train_dataset.taskers.images_creators.concrete_creators.txt_images_creator import TxtImagesCreator
from dedoc.train_dataset.taskers.images_creators.image_creator_composition import ImageCreatorComposition


class LineLabelTasker(AbstractLineLabelTasker):

    def __init__(self,
                 path2bboxes: str,
                 path2lines: str,
                 path2docs: str,
                 manifest_path: str,
                 config_path: str,
                 tmp_dir: str,
                 progress_bar: dict = None,
                 item2label: Callable = None,
                 *,
                 config: dict) -> None:
        super().__init__(path2bboxes, path2lines, path2docs, manifest_path, config_path, tmp_dir, progress_bar,
                         item2label, config=config)
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

    def _one_scanned_page(self,
                          page: List[dict],
                          task_archive: zipfile.ZipFile,
                          task_directory: str, *,
                          images: ImagesArchive) -> List[TaskItem]:
        self._page_counter += 1
        task_items = []

        for i, line in enumerate(page):
            uid = line['_uid']
            image_bbox_name = "images/{:0>6d}_{:0>6d}_img_bbox_{}.jpg".format(self._page_counter, i, uid)
            image_bbox = images.get_page_by_uid("{}.jpg".format(uid))
            if image_bbox is None:
                if not uid.endswith("_split"):
                    self.logger.warn("uid {} not found".format(uid))
                continue
            with BytesIO() as buffer:
                image_bbox.convert('RGB').save(fp=buffer, format="jpeg")
                task_archive.writestr(zinfo_or_arcname=os.path.join(task_directory, image_bbox_name),
                                      data=buffer.getvalue())

            line_id = line["_metadata"]["line_id"]
            page_id = line["_metadata"]["page_id"]
            text = line["_line"]
            task_item = TaskItem(
                task_id=len(task_items),
                task_path=image_bbox_name,
                data=line,
                labeled=[line["_metadata"]['hierarchy_level']['line_type']],
                additional_info="<p><em>page_id</em> {} </p><p><em>line_id</em> {} </p><p><em> text</em> {}</p>".format(
                    page_id, line_id, text),
                default_label=self.item2label(line)
            )
            task_items.append(task_item)
        return task_items
