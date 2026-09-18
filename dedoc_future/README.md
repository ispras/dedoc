# New interfaces of the dedoc library

## Config

### System config

Config for configuring processing modules (configured by modules labels)

| Dedoc parameter             | Description            | Option type  | Usage time       | Dedoc future modules                                          |
|-----------------------------|------------------------|--------------|------------------|---------------------------------------------------------------|
| -                           | converter formats      | enum_auto    | Deploy           | `DocxConverter`, `ExcelConverter`, ...                        |
| -                           | parser formats         | enum_auto    | Deploy           | `ArchiveParser`, `CsvParser`, ...                             |
| pdf_with_text_layer         | type of pdf parser     | enum         | Deploy, runtime  | `PdfminerParser`, `ImageParser`, ...                          |
| -                           | type of pages render   | enum         | Deploy, runtime  | `PopplerRender`, `PdfiumRender`                               |
| -                           | type of ocr engine     | enum         | Deploy, runtime  | `TesseractOcr`, `EasyOcr`, ...                                |
| need_binarization           | use binarizer or not   | bool (enum?) | Runtime          | `Binarizer`                                                   |
| is_one_column_document      | may be delete that?    |              |                  |                                                               |
| document_orientation        | fix orientation or not | bool (enum?) | Runtime          | `OrientationClassification`                                   |
| -                           | fix skew or not        | bool (enum?) | Runtime          | `SkewCorrection`                                              |
| need_pdf_table_analysis     | may be delete that?    |              |                  | `TableDetectorRecognizer`                                     |
| need_gost_frame_analysis    | analyze gost frame     | bool         | Deploy?, runtime | `GostFrameAnalyzer`, `GostFramePostprocessor`                 |
| need_header_footer_analysis | analyze header/footer  | bool         | Runtime          | `HeaderFooterAnalyzer`                                        |
| extract_notes               | extract notes from pdf | bool         | Runtime          | `PdfNotesExractor`                                            |
| document_type               | type of structure      | enum         | Deploy, runtime  | `DefaultStructureExtractor`, `DiplomaStructureExtractor`, ... |
| return_format               | output type            | enum         | Deploy, runtime  | `JsonOutputConverter`, `HtmlOutputConverter`, ...             |

* `enum_auto` - choose set of modules during deploy; in runtime one processor will be chosen automatically
* `enum` - choose set of modules during deploy (at least one for each parameter); in runtime choose one option from this set
* `bool` - include / not include module in pipeline (maybe also configure during deploy?)



### Runtime config

Config of modules `process` method

| Dedoc parameter                   | Option type | Dedoc future modules             |
|-----------------------------------|-------------|----------------------------------|
| patterns                          | object      | `DefaultStructureExtractor`      |
| with_attachments                  | bool        | `DocxParser`, `TabbyParser`, ... |
| need_content_analysis             | bool        | pipeline (attachments recursion) |
| recursion_deep_attachments        | int         | pipeline (attachments recursion) |
| textual_layer_classifier          | enum        | `TextLayerDetector`              |
| each_page_textual_layer_detection | bool        | `TextLayerDetector`              |
| language                          | list[enum]  | `TesseractOcr`, `EasyOcr`, ...   |
| pages                             | [int, int]  | `PagesCreator`                   |
| table_type                        | enum        | `TableDetectorRecognizer`        |
| delimiter                         | str         | `CsvParser`                      |
| encoding                          | str         | `CsvParser`, `TxtParser`         |
| handle_invisible_table            | bool        | `HtmlParser`                     | 

Each module defines its config.

Pipeline config is made from configs of its modules.

User-friendly config ????


## Pipeline

1. Preprocessing
2. Parsing
3. Postprocessing
4. Converting

3 types of processing modules:

1. `document` - document processors `TalismanDocument` -> `TalismanDocument`
2. `node` - nodes processors: `Sequence[AbstractNode]` -> `changed nodes`, `new_nodes`, `delete_nodes`
3. `configurator` - configurators: without code, sequence of processors

3 types of actions:
1. `choose` - choose one of the modules
2. `opt` - we can skip module
3. `process` - Run module.process() or submodules (if module is configurator)


### Preprocessing

| Module                | Module type | Action type | Input/output |
|-----------------------|-------------|-------------|--------------|
| `MetadataExtractor`   | node        | process     | `FileNode`   |
| `ContentMimeDetector` | node        | skip        | `FileNode`   |
| `DocxConverter`, ...  | node        | choose      | `FileNode`   |

- `ContentMimeDetector` is run if first processing fails
- Converting (choose):
    - `DocxConverter`, `ExcelConverter`, `PptxConverter` or `OfficeConverter`
    - `PdfConverter`
    - `PngConverter`
    - `TxtConverter`

### Parsing

| Module                                                  | Module type  | Action type | Input/output                                     |
|---------------------------------------------------------|--------------|-------------|--------------------------------------------------|
| `ArchiveParser`, `CsvParser`, `JsonParser`, `TxtParser` | document     | choose      | `TalismanDocument`                               |
| `DocxParser`, `PptxParser`, `ExcelParser`               | document     | choose      | `TalismanDocument`                               |
| `EmlParser`, `HtmlParser`, `MhtmlParser`                | document     | choose      | `TalismanDocument`                               |
| `DedocImageParserConfigurator`                          | configurator | choose      |                                                  |
| `ImageParserConfigurator`                               | configurator | choose      |                                                  |
| `PdfConfigurator`                                       | configurator | choose      |                                                  |
| `PdfAutoConfigurator`                                   | configurator | choose      |                                                  |
| `GostFrameConfigurator`                                 | configurator | choose      |                                                  |
|                                                         |              |             |                                                  |
| `DedocTableConfigurator`, `TableConfigurator`           | configurator | opt         |                                                  |
| `CompositeOcr`                                          | configurator | choose      |                                                  |
|                                                         |              |             |                                                  |
| `PdfMetadataExtractor` / `ImageMetadataExtractor`       | node         | choose      | `FileNode`                                       |
| `PagesCreator`                                          | node         | process     | `FileNode` -> `list[PageNode]`                   |
| `PopplerRender` / `PdfiumRender`                        | node         | choose      | `PageNode`                                       |
| `Binarizer`                                             | node         | opt         | `PageNode`                                       |
| `OrientationClassification`                             | node         | opt         | `PageNode`                                       |
| `SkewCorrection`                                        | node         | opt         | `PageNode`                                       |
| `TableDetectorRecognizer`                               | node         | process     | `PageNode` -> `list[TableNode]` + structure      |
| `TesseractOcr`, `EasyOcr`, ...                          | node         | choose      | `TextNode`/`PageNode` -> `TextNode`              |
| `LayoutAnalysis`                                        | node         | ?           | `PageNode` -> `TextNode`/`TableNode`/`ImageNode` |
| `ImageClearer`                                          | node         | ?           | `PageNode`                                       |
| `LineMetadataExtractor`                                 | node         | opt         | `TextNode`                                       |
| `HeaderFooterAnalyzer`                                  | document     | opt         |                                                  |
| `PdfNotesExractor`                                      | document     | opt         |                                                  |
| `PdfTableMerger`                                        | document     | process     |                                                  |
| `PdfObjectsLinker`                                      | document     | process     |                                                  |
| `DoclingTableRecognition`                               | node         | process     | `TableNode` -> table structure                   |
| `TabbyParser`, `PdfminerParser`, ...                    | document     | process     |                                                  |
| `PdfAttachmentsExtractor`                               | document     | opt         |                                                  |
| `TextLayerDetector`                                     | document     | process     |                                                  |
| `GostFrameAnalyzer`, `GostFramePostprocessor`           | document     | process     |                                                  |
|                                                         |              |             |                                                  |


- `DocxParser`, `PptxParser`, `ExcelParser`  + metadata extraction + attachments extraction (common office utils)
- `DedocImageParserConfigurator` - existing pipeline in dedoc
    - `PdfMetadataExtractor` / `ImageMetadataExtractor`
    - `PagesCreator`
    - `PopplerRender`
    - `Binarizer`
    - `OrientationClassification`
    - `SkewCorrection`
    - `DedocTableConfigurator`
        - `TableDetectorRecognizer`
        - `TesseractOcr`
    - `LayoutAnalysis`
    - `ImageClearer`
    - `TesseractOcr`
    - `LineMetadataExtractor`
    - `HeaderFooterAnalyzer`
    - `PdfNotesExractor`
    - `PdfTableMerger`
    - `PdfObjectsLinker`
- `ImageParserConfigurator` - new pipeline
    - `PdfMetadataExtractor` / `ImageMetadataExtractor`
    - `PagesCreator`
    - `PopplerRender`
    - `Binarizer`
    - `OrientationClassification`
    - `SkewCorrection`
    - `LayoutAnalysis`
    - `TableConfigurator`
        - `DoclingTableRecognition`
        - `TesseractOcr`
    - `TesseractOcr`
    - `LineMetadataExtractor`
    - ...
- `PdfConfigurator`
    - `PdfMetadataExtractor`
    - `TabbyParser` / `PdfminerParser`
    - `PdfAttachmentsExtractor`
    - `HeaderFooterAnalyzer`
    - `PdfNotesExractor`
    - `PdfTableMerger`
    - `PdfObjectsLinker`
- `PdfAutoParser`
    - `PdfMetadataExtractor`
    - `TabbyParser`
    - `TextLayerDetector`
    - `PopplerRender`
    - ...
- `GostFrameConfigurator`
    - `PopplerRender`
    - `GostFrameAnalyzer`
    - ...
    - `GostFramePostprocessor`

### Postprocessing

* module type: document
* option type: choose
* `TalismanDocument` -> `TalismanDocument`
* modules:
  - `DefaultStructureExtractor`
  - `DiplomaStructureExtractor`
  - `LawStructureExtractor`
  - `TzStructureExtractor`
  - `FintocStructureExtractor`

### Output converting

* option type: choose
* `TalismanDocument` -> Custom format
* modules:
  - `JsonOutputConverter`
  - `HtmlOutputConverter`
  - `MdOutputConverter`
  - `TxtOutputConverter`

## Code example

PDF without textual layer

```python
from tdm import DefaultDocumentFactory

from dedoc_future.abstract import AbstractDocumentProcessor, AbstractNodeProcessor, ImmutableBaseModel
from dedoc_future.datamodel.nodes.file import FileNode
from dedoc_future.processors.parsing.pdf.preprocessing.binarization import Binarizer
from dedoc_future.processors.parsing.pdf.preprocessing.orientation_classification import OrientationClassification
from dedoc_future.processors.parsing.pdf.preprocessing.skew_correction import SkewCorrection
from dedoc_future.processors.parsing.pdf.render.pages_creator import PagesCreator
from dedoc_future.processors.parsing.pdf.render.poppler_render import PopplerRender
from dedoc_future.processors.preprocessing.metadata_extractor import MetadataExtractor

file_path = "file.pdf"
document = DefaultDocumentFactory.create_document()
file_node = FileNode(file_path)
document = document.with_main_root(file_node, update=True)

config = ImmutableBaseModel()  # TODO
stages = [
    MetadataExtractor,
    PdfConverter,
    PdfMetadataExtractor,
    PagesCreator,
    PopplerRender,
    Binarizer,
    OrientationClassification,
    SkewCorrection,
    TableDetectorRecognizer,
    TesseractOcr,  # for text recognition in table cells
    LayoutAnalysis,  # TODO parallelism
    ImageClearer,
    TesseractOcr,  # for pages
    LineMetadataExtractor,
    HeaderFooterAnalyzer,
    PdfNotesExractor,
    PdfTableMerger,
    PdfObjectsLinker,
    DefaultStructureExtractor,
    JsonOutputConverter
]

for stage in stages:
    if isinstance(stage, AbstractNodeProcessor):
        # TODO batches
        for node in document.get_nodes(type_=stage.node_type(), filter_=lambda n: stage.can_process(n, config)):
            result = stage.process([node], config)
            document = document.with_nodes(result.changed_nodes).with_structure(result.new_nodes, update=True)
            document = document.without_nodes(result.delete_nodes, cascade=True)
    elif isinstance(stage, AbstractDocumentProcessor):
        if stage.can_process(document, config):
            document = stage.process([document], config)[0]
    else:  # custom processor
        ...
```
