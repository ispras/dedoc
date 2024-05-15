from collections import namedtuple
from typing import List

from dedoc.utils.utils import get_extensions_by_mimes

Extensions = namedtuple("Parts", [
    "excel_like_format",
    "docx_like_format",
    "pptx_like_format",
    "html_like_format",
    "eml_like_format",
    "mhtml_like_format",
    "archive_like_format",
    "image_like_format",
    "pdf_like_format",
    "csv_like_format",
    "txt_like_format",
    "json_like_format"
])


converted_extensions = Extensions(
    excel_like_format={".ods", "xls"},
    docx_like_format={".odt", ".doc", ".rtf"},
    pptx_like_format={".odp", ".ppt"},
    html_like_format={},
    eml_like_format={},
    mhtml_like_format={},
    archive_like_format={},
    image_like_format={
        ".bmp", ".dib", ".eps", ".gif", ".hdr", ".j2k", ".jfif", ".jp2", ".jpe", ".jpeg", ".jpg", ".pbm", ".pcx", ".pgm", ".pic", ".pnm", ".ppm", ".ras",
        ".sgi", ".sr", ".tiff", ".webp"
    },
    pdf_like_format={".djvu"},
    csv_like_format={},
    txt_like_format={".xml"},
    json_like_format={}
)
# .sgi, .hdr, .sr, .ras - не зарегистрованы в mime
converted_mimes = Extensions(
    excel_like_format={"application/vnd.oasis.opendocument.spreadsheet", "application/vnd.ms-excel"},
    docx_like_format={"application/msword", "application/vnd.oasis.opendocument.text", "text/rtf", "application/rtf"},
    pptx_like_format={"application/vnd.ms-powerpoint", "application/vnd.oasis.opendocument.presentation"},
    html_like_format={},
    eml_like_format={},
    mhtml_like_format={},
    archive_like_format={},
    image_like_format={
        "image/bmp", "image/x-ms-bmp", "image/dib", "image/x-eps", "application/postscript", "image/gif", "image/jpeg", "image/jp2", "image/x-jp2", "image/jpg",
        "image/x-portable-pixmap", "image/x-portable-anymap", "image/x-portable-graymap", "image/x-portable-bitmap", "image/x-pcx", "image/x-pict",
        "image/ras", "image/x-sun-raster", "image/sgi", "image/x-sgi", "image/tiff", "image/webp", "image/x-cmu-raster", "image/x-jp2-codestream"
    },
    pdf_like_format={"image/vnd.djvu"},
    csv_like_format={},
    txt_like_format={"application/xml", "text/xml"},
    json_like_format={}
)

recognized_extensions = Extensions(
    excel_like_format={".xlsx"},
    docx_like_format={".docx"},
    pptx_like_format={".pptx"},
    html_like_format={".htm", ".html", ".shtml"},
    eml_like_format={".eml"},
    mhtml_like_format={".mhtml", ".mht", ".mhtml.gz", ".mht.gz"},
    archive_like_format={".zip", ".tar", ".tar.gz", ".rar", ".7z"},
    image_like_format={".png"},
    pdf_like_format={".pdf"},
    csv_like_format={".csv", ".tsv"},
    txt_like_format={".txt", ".txt.gz"},
    json_like_format={".json"}
)

recognized_mimes = Extensions(
    excel_like_format={"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    docx_like_format={"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    pptx_like_format={"application/vnd.openxmlformats-officedocument.presentationml.presentation"},
    html_like_format={"text/html"},
    eml_like_format={"message/rfc822"},
    mhtml_like_format={"message/rfc822"},
    archive_like_format={
        "application/zip", "application/x-gzip", "application/gzip", "application/x-tar", "application/x-rar-compressed", "application/rar",
        "application/x-rar", "application/x-7z-compressed"
    },
    image_like_format={"image/png"},
    pdf_like_format={"application/pdf"},
    csv_like_format={"text/csv", "application/csv", "text/tab-separated-values"},
    txt_like_format={"text/plain"},
    json_like_format={"application/json"}
)


mime2extension = {
    # excel
    "application/vnd.ms-excel": ".xls", "application/vnd.oasis.opendocument.spreadsheet": ".ods",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    # docx
    "application/rtf": ".rtf", "application/vnd.oasis.opendocument.text": ".odt",
    "text/rtf": ".rtf", "application/msword": ".doc", "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    # pptx
    "application/vnd.ms-powerpoint": ".ppt", "application/vnd.oasis.opendocument.presentation": ".odp",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    # html
    "text/html": ".html",
    # eml
    "message/rfc822": ".eml",
    # archive
    "application/x-gzip": ".gz", "application/gzip": ".gz", "application/x-rar-compressed": ".rar", "application/rar": ".rar", "application/x-tar": ".tar",
    "application/x-rar": ".rar", "application/x-7z-compressed": ".7z", "application/zip": ".zip",
    # image
    "image/x-ms-bmp": ".bmp", "image/sgi": ".sgi", "image/jpeg": ".jpg", "image/x-jp2": ".jp2", "image/x-portable-graymap": ".pgm", "image/x-pict": ".pic",
    "image/gif": ".gif", "image/x-sgi": ".sgi", "image/x-sun-raster": ".ras", "image/x-eps": ".eps", "image/bmp": ".bmp", "image/x-portable-bitmap": ".pbm",
    "image/webp": ".webp", "application/postscript": ".eps", "image/jpg": ".jpg", "image/x-jp2-codestream": "jp2", "image/x-portable-pixmap": ".ppm",
    "image/jp2": ".jp2", "image/dib": ".dib", "image/x-pcx": ".pcx", "image/tiff": ".tiff", "image/x-cmu-raster": ".ras", "image/ras": ".ras",
    "image/x-portable-anymap": ".pnm", "image/png": ".png",
    # pdf
    "image/vnd.djvu": ".djvu", "application/pdf": ".pdf",
    # csv
    "text/tab-separated-values": ".tsv", "application/csv": ".csv", "text/csv": ".csv",
    # txt
    "application/xml": ".xml", "text/xml": ".xml", "text/plain": ".txt",
    # json
    "application/json": ".json"
}


def get_image_extensions() -> List[str]:
    image_extensions = get_extensions_by_mimes(converted_mimes.image_like_format)
    image_extensions.extend(get_extensions_by_mimes(recognized_mimes.image_like_format))
    image_extensions.extend(converted_extensions.image_like_format)
    image_extensions.extend(recognized_extensions.image_like_format)

    return image_extensions
