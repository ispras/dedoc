import zipfile
from collections import defaultdict
from typing import List, Callable

from dedoc.train_dataset.data_structures.images_archive import ImagesArchive
from dedoc.train_dataset.data_structures.task_item import TaskItem
from dedoc.train_dataset.taskers.images_creators.concrete_creators.docx_images_creator import DocxImagesCreator
from dedoc.train_dataset.taskers.images_creators.concrete_creators.scanned_images_creator import ScannedImagesCreator
from dedoc.train_dataset.taskers.images_creators.concrete_creators.txt_images_creator import TxtImagesCreator
from dedoc.train_dataset.taskers.images_creators.image_creator_composition import ImageCreatorComposition
from dedoc.train_dataset.taskers.concrete_taskers.line_label_tasker import LineLabelTasker


class HeaderFooterTasker(LineLabelTasker):
    top_lines_count = 3
    bottom_lines_count = 3

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

    def _one_scanned_page(self,
                          page: List[dict],
                          task_archive: zipfile.ZipFile,
                          task_directory: str, *,
                          images: ImagesArchive) -> List[TaskItem]:
        group_by_page_num = defaultdict(list)
        for line in page:
            page_id = line["_metadata"]["page_id"]
            group_by_page_num[page_id].append(line)
        res = []
        for page in group_by_page_num.values():
            page.sort(key=self._get_line_rank)
            if len(page) > self.top_lines_count + self.bottom_lines_count:
                page = page[:self.top_lines_count] + page[-self.bottom_lines_count:]
            res.extend(page)
        return super(HeaderFooterTasker, self)._one_scanned_page(page=res,
                                                                 task_archive=task_archive,
                                                                 task_directory=task_directory,
                                                                 images=images)

    @staticmethod
    def _get_line_rank(line: dict) -> int:
        if "bbox" in line:
            bbox = line["bbox"]["bbox"]
            return bbox["y_top_left"]
        else:
            return line["_metadata"]["line_id"]
