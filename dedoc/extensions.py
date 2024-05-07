from collections import namedtuple
from typing import List

from dedoc.utils.utils import get_extensions_by_mimes

Extensions = namedtuple("Parts", [
    "excel_like_format",
    "docx_like_format",
    "pptx_like_format",
    "archive_like_format",
    "image_like_format",
    "pdf_like_format",
    "csv_like_format",
    "txt_like_format"
])


converted_extensions = Extensions(
    excel_like_format=[".ods", "xls"],
    docx_like_format=[".odt", ".doc", ".rtf"],
    pptx_like_format=[".odp", ".ppt"],
    archive_like_format=[],
    image_like_format=[
        ".bmp", ".dib", ".eps", ".gif", ".hdr", ".j2k", ".jfif", ".jp2", ".jpe", ".jpeg", ".jpg", ".pbm", ".pcx", ".pgm", ".pic", ".pnm", ".ppm", ".ras",
        ".sgi", ".sr", ".tiff", ".webp"
    ],
    pdf_like_format=[".djvu"],
    csv_like_format=[],
    txt_like_format=[".xml"]
)
# .sgi, .hdr, .sr, .ras - не зарегистрованы в mime
converted_mimes = Extensions(
    excel_like_format=["application/vnd.oasis.opendocument.spreadsheet", "application/vnd.ms-excel"],
    docx_like_format=["application/msword", "application/vnd.oasis.opendocument.text", "application/rtf"],
    pptx_like_format=["application/vnd.ms-powerpoint", "application/vnd.oasis.opendocument.presentation"],
    archive_like_format=[],
    image_like_format=[
        "image/bmp", "image/x-ms-bmp", "image/dib", "image/x-eps", "application/postscript", "image/gif", "image/jpeg", "image/x-jp2", "image/jpg",
        "image/x-portable-pixmap", "image/x-portable-anymap", "image/x-portable-graymap", "image/x-portable-bitmap", "image/x-pcx", "image/x-pict",
        "image/ras", "image/sgi", "image/x-sgi", "image/tiff", "image/webp", "image/x-cmu-raster"
    ],
    pdf_like_format=["image/vnd.djvu"],
    csv_like_format=[],
    txt_like_format=["application/xml", "text/xml"]
)

recognized_extensions = Extensions(
    excel_like_format=[".xlsx"],
    docx_like_format=[".docx"],
    pptx_like_format=[".pptx"],
    archive_like_format=[".zip", ".tar", ".tar.gz", ".rar", ".7z"],
    image_like_format=[".png"],
    pdf_like_format=[".pdf"],
    csv_like_format=[".csv", ".tsv"],
    txt_like_format=[".txt", ".txt.gz"]
)

recognized_mimes = Extensions(
    excel_like_format=["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
    docx_like_format=["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    pptx_like_format=["application/vnd.openxmlformats-officedocument.presentationml.presentation"],
    archive_like_format=["application/zip", "application/x-tar", "application/x-rar-compressed", "application/rar", "application/x-7z-compressed"],
    image_like_format=["image/png"],
    pdf_like_format=["application/pdf"],
    csv_like_format=["text/csv", "text/tab-separated-values"],
    txt_like_format=["text/plain"]
)


def get_image_extensions() -> List[str]:
    image_extensions = get_extensions_by_mimes(converted_mimes.image_like_format)
    image_extensions.extend(get_extensions_by_mimes(recognized_mimes.image_like_format))
    image_extensions.extend(converted_extensions.image_like_format)
    image_extensions.extend(recognized_extensions.image_like_format)

    return image_extensions
