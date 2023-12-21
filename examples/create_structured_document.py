# noqa
from create_unstructured_document import unstructured_document
from dedoc.structure_constructors import TreeConstructor

# to create structured document you can use TreeConstructor and apply it to unstructured document
# in this example we'll use unstructured_document from create_unstructured_document.py
structure_constructor = TreeConstructor()
parsed_document = structure_constructor.construct(document=unstructured_document)

print(parsed_document.to_api_schema().model_dump())
