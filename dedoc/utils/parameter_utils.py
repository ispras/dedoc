from typing import Optional, Dict, Any, Tuple


def get_param_language(parameters: Optional[dict]) -> str:
    if parameters is None:
        return "rus+eng"
    language = parameters.get("language", "rus+eng")
    if language == "ru" or language == "rus":
        language = "rus"
    elif language == "en" or language == "eng":
        language = "eng"
    elif language == "ru+en" or language == "rus+eng":
        language = "rus+eng"
    return language


def get_param_orient_analysis_cells(parameters: Optional[dict]) -> bool:
    if parameters is None:
        return False
    orient_analysis_cells = parameters.get("orient_analysis_cells", "False").lower() == "true"
    return orient_analysis_cells


def get_param_need_header_footers_analysis(parameters: Optional[dict]) -> bool:
    if parameters is None:
        return False
    need_header_footers_analysis = parameters.get("need_header_footer_analysis", "False").lower() == "true"
    return need_header_footers_analysis


def get_param_need_pdf_table_analysis(parameters: Optional[dict]) -> bool:
    if parameters is None:
        return False
    need_pdf_table_analysis = parameters.get("need_pdf_table_analysis", "True").lower() == "true"
    return need_pdf_table_analysis


def get_param_need_binarization(parameters: Optional[dict]) -> bool:
    if parameters is None:
        return False
    need_binarization = parameters.get("need_binarization", "False").lower() == "true"
    return need_binarization


def get_param_orient_cell_angle(parameters: Optional[dict]) -> int:
    if parameters is None:
        return 90

    orient_cell_angle = parameters.get("orient_cell_angle", "90")
    if orient_cell_angle == "":
        orient_cell_angle = "90"
    return int(orient_cell_angle)


def get_param_is_one_column_document(parameters: Optional[dict]) -> Optional[bool]:
    if parameters is None:
        return None

    is_one_column_document = str(parameters.get("is_one_column_document", "auto"))
    if is_one_column_document.lower() == "auto":
        return None
    else:
        return is_one_column_document.lower() == "true"


def get_param_document_orientation(parameters: Optional[dict]) -> Optional[bool]:
    if parameters is None:
        return None
    document_orientation = str(parameters.get("document_orientation", "auto"))
    if document_orientation.lower() == "no_change":
        return False
    else:
        return None


def get_param_project(parameters: Optional[dict]) -> str:
    if parameters is None:
        return "docreader_project"
    project = str(parameters.get("project", "docreader_project")).lower()
    return project


def get_param_pdf_with_txt_layer(parameters: Optional[dict]) -> str:
    if parameters is None:
        return "false"
    pdf_with_txt_layer = str(parameters.get("pdf_with_text_layer", "false")).lower()
    return pdf_with_txt_layer


def get_param_image_document_page(parameters: Optional[dict]) -> str:
    if parameters is None:
        return ""

    image_document_page = str(parameters.get("image_document_page", ""))
    return image_document_page


def get_param_table_type(parameters: Optional[dict]) -> str:

    if parameters is None:
        return ""

    return str(parameters.get("table_type", ""))


def get_is_one_column_document_list(parameters: Optional[dict]) -> Optional[bool]:
    return None if parameters is None else parameters.get("is_one_column_document_list")


def get_param_page_slice(parameters: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse parameter pages = ["page_number:page_number" | "" | "page_number:" | ":page_number" : ":"]
    Page numeration starts with 1
    """
    pages = parameters.get("pages", "")
    if pages is None or pages.strip() == "":
        return None, None
    try:
        first_page, last_page = pages.split(":")
        first_page = None if first_page == "" else int(first_page) - 1
        last_page = None if last_page == "" else int(last_page)

        return first_page, last_page
    except Exception:
        raise ValueError("Error input parameter 'pages'. Bad page limit {}".format(pages))
