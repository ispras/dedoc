# noqa
import json

from dedoc import DedocManager

manager = DedocManager()

filename_docx = "example.docx"
parsed_docx_document = manager.parse(file_path=filename_docx, parameters={})

# save the result
with open("result_docx.json", "w") as outfile:
    outfile.write(json.dumps(parsed_docx_document.to_dict()))

filename_jpg = "example.jpg"
parsed_jpg_document = manager.parse(file_path=filename_jpg, parameters={})

# save the result
with open("result_jpg.json", "w") as outfile:
    outfile.write(json.dumps(parsed_jpg_document.to_dict()))

filename_pdf_no_text_layer = "example_without_text_layer.pdf"
parsed_pdf_no_text_layer_document = manager.parse(file_path=filename_pdf_no_text_layer, parameters={"pdf_with_text_layer": "false"})

# save the result
with open("result_pdf_no_text_layer.json", "w") as outfile:
    outfile.write(json.dumps(parsed_pdf_no_text_layer_document.to_dict()))

filename_pdf_with_text_layer = "example_with_text_layer.pdf"
parsed_pdf_with_text_layer_document = manager.parse(file_path=filename_pdf_with_text_layer, parameters={"pdf_with_text_layer": "true"})

# save the result
with open("result_pdf_with_text_layer.json", "w") as outfile:
    outfile.write(json.dumps(parsed_pdf_with_text_layer_document.to_dict()))
