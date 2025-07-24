from pathlib import Path

junk_string = "_junkstring"


def correctly_resize(image_path: str, size: tuple = (28, 28)) -> None:
    import PIL.ImageOps
    from PIL import Image
    im = Image.open(image_path)
    im.thumbnail((28, 28), Image.LANCZOS)
    new_image = Image.new("L", size, color=255)
    x_offset = (new_image.size[0] - im.size[0]) // 2
    y_offset = (new_image.size[1] - im.size[1]) // 2
    new_image.paste(im, (x_offset, y_offset))
    new_image = PIL.ImageOps.invert(new_image)
    new_image.save(image_path)


def is_empty(image_path: str) -> bool:
    from PIL import Image
    if not image_path.lower().endswith(".png"):
        raise Exception("problems with extracted glyphs png path")
    img = Image.open(image_path)
    extrema = img.convert("L").getextrema()
    empty_bool = False
    if extrema == (0, 0) or extrema == (255, 255):
        return True
    return empty_bool


def get_project_root() -> Path:
    return Path(__file__).parent


def collapse_text(text: str) -> str:
    text = " ".join(text.splitlines())
    text = " ".join(text.split())
    return text


def remove_hyphenations(text: str) -> str:
    return text.replace("- ", "")


def extract_pdf_text2json(pdf_path: Path, pages: tuple = None) -> None:
    import os
    import json

    from pdfminer.high_level import extract_text
    pages = (0, 1) if pages is None else pages
    assert len(pages) == 2, "pages should be of len 2"
    assert pages[0] == pages[1] == 0 or pages[0] < pages[1], "wrong range"
    pages_range = list(range(pages[0], pages[1]))
    pdf_path = os.path.normpath(pdf_path)
    pdf_name = pdf_path.split("\\")[-1].split(".")[0]
    json_path = os.path.normpath(f"{get_project_root()}/data/jsons/{pdf_name}.json")

    text = extract_text(pdf_path, page_numbers=pages_range)
    text = collapse_text(text)
    text = remove_hyphenations(text)
    json_dict = {"pages": pages, "text": text}
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(json_dict, file, indent=4, ensure_ascii=False)
