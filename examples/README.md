# Examples of document parsing with Dedoc 

This directory contains files with examples of using Dedoc to process different types of documents.

It's worth starting with the `example_manager_input.py` file. It describes examples of document processing using the `DedocManager` class. 
This is the easiest way, since this class automatically determines the format of the file being processed and calls the necessary readers.

As shown in corresponding examples, you can create this manager with following lines:
```
from dedoc import DedocManager

manager = DedocManager()
```
And after that you can get parsed document with one simple line, just replace `"your_file_name"` with the path to your chosen file:
```
parsed_document = manager.parse(file_path="your_file_name")
```
To get more information, look at [Dedoc usage tutorial](https://dedoc.readthedocs.io/en/latest/getting_started/usage.html).

If you want to call a specific parser, you can look at some examples in this directory. File `example_doc_parser.py` shows how you can use `DocxReader`,
`example_pdf_parser.py` shows examples with PDF file parsing. In order to parse img-like file you can call `PdfImageReader` like it's shown in
`example_img_parser.py`. 

Also you can look at the example of using a post-request to parse documents while Dedoc container is working. This example is written in `example_post.py`.

You can check an example like this:
```bash
cd examples
python3 create_structured_document.py
```