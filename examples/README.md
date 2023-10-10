# Examples of document parsing with Dedoc 

This directory contains files with examples of using Dedoc to process different types of documents.

It's worth starting with the `example_manager_input.py` file. It describes examples of document processing using the `DedocManager` class. 
This is the easiest way, since this class automatically determines the format of the file being processed and calls the necessary readers.

As shown in corresponding examples, you can create this manager with following lines:
```python
from dedoc import DedocManager

manager = DedocManager()
```
And after that you can get parsed document with one simple line, just replace `"your_file_name"` with the path to your chosen file:
```python
parsed_document = manager.parse(file_path="your_file_name")
```
To get more information, look at [Dedoc usage tutorial](https://dedoc.readthedocs.io/en/latest/getting_started/usage.html).

If you want to call a specific parser, you can look at some examples in this directory. File `example_doc_parser.py` shows how to use `DocxReader`,
`example_pdf_parser.py` shows examples with PDF file parsing. In order to parse image-like file you can call `PdfImageReader` like it's shown in
`example_img_parser.py`. 

You can check an example like this:
```shell
cd examples
python3 create_structured_document.py
```

## Running API examples in a docker container

You can look at the example of using a post-request to parse documents while Dedoc container is working. 
This example is written in `example_post.py`.


### Work with a docker container

You may use your own container with Dedoc, if there is one, otherwise it may be downloaded with the following command:

```shell
export VERSION_TAG=v0.1
docker pull dedocproject/dedoc:VERSION_TAG
```

`VERSION_TAG` - tag of the library release, e.g. `v0.1`.


Run the Dedoc container:

```shell
docker run dedocproject/dedoc:VERSION_TAG
```

If you want to use Dedoc outside the container (locally), the option for ports should be added:

```shell
docker run -p 1231:1231 dedocproject/dedoc:VERSION_TAG
```

For running example inside Dedoc container one should do the following:

1. Open a new terminal window. Get a list of available containers:
    ```shell
    docker ps -a
    ```
   The Dedoc container has `IMAGE` field equal `dedocproject/dedoc:VERSION_TAG` (or a custom name if you have another container).
   Copy its `CONTAINER_ID` for the future commands.

2. Start the container if it isn't running:
    ```shell
    docker start CONTAINER_ID
    ```
   In this case a new terminal window in needed for the next steps.

3. Run a command line of the Dedoc container:
    ```shell
    docker exec -it CONTAINER_ID bash
    ```
   
4. Get examples from `https://github.com` (use `VERSION_TAG` described before) if you don't have them:
    ```shell
    git clone https://github.com/ispras/dedoc
    git checkout VERSION_TAG
    cd dedoc/examples
    ```
5. Run the example with API usage:
    ```shell
    python3 example_post.py
    ```
   
6. Exit from the Dedoc container using `exit` command.
