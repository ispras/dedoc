from typing import List, Callable

from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.toc_feature_extractor import TOCFeatureExtractor
from dedoc.train_dataset.taskers.concrete_taskers.line_label_tasker import LineLabelTasker
from dedoc.train_dataset.taskers.images_creators.concrete_creators.docx_images_creator import DocxImagesCreator
from dedoc.train_dataset.taskers.images_creators.concrete_creators.scanned_images_creator import ScannedImagesCreator
from dedoc.train_dataset.taskers.images_creators.image_creator_composition import ImageCreatorComposition


class FilteredLineLabelTasker(LineLabelTasker):

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
        # we can use page numbers only in pdf
        self.images_creators = ImageCreatorComposition(creators=[
            ScannedImagesCreator(path2docs=self.path2docs),
            DocxImagesCreator(path2docs=self.path2docs, config=config)
        ])
        self.toc_extractor = TOCFeatureExtractor()

    def _get_pages(self) -> List[List[dict]]:
        pages = super()._get_pages()
        filtered_pages = []
        # one page - list of lines for one document
        for page in pages:
            doc_lines = [self._make_line_with_meta(line) for line in page]
            doc_toc = self.toc_extractor.get_toc(doc_lines)
            # acual_page_num - 1 = page_id
            page_numbers = [0, 1] + [int(item["page"]) - 1 for item in doc_toc] + [int(item["page"]) for item in
                                                                                   doc_toc]
            doc_line_dicts = [line for line in page if int(line["_metadata"]["page_id"]) in page_numbers]
            filtered_pages.append(doc_line_dicts)
        return filtered_pages

    def _make_line_with_meta(self, line: dict) -> LineWithMeta:
        line_metadata = LineMetadata(page_id=line["_metadata"]["page_id"], line_id=line["_metadata"]["page_id"])
        return LineWithMeta(line=line["_line"], metadata=line_metadata, annotations=[], uid=line["_uid"])
