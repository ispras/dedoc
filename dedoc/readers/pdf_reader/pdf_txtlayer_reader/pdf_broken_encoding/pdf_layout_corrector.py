import ast
import os
import re
import subprocess
import tempfile
from itertools import zip_longest
from pathlib import Path, PurePath
from sys import platform
from typing import Dict, Iterable, List, Optional, Tuple, Union

import fitz
from fontTools.ttLib import TTFont
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTChar, LTPage, LTTextLineHorizontal
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdftypes import resolve1
from pdfminer.psparser import PSLiteral

from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding.model import GlyphRecognitionModel
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding.utils import correct_string_incorrect_chars, correctly_resize, is_empty, junk_string


class PDFLayoutCorrector:
    def __init__(self) -> None:
        self.model = GlyphRecognitionModel()
        self.text = None
        self.match_dict = {}
        self.__cached_fonts = None
        self.__fontname2basefont = {}
        self.__unicodemaps = {}
        self.__name2code = {}

    def get_correct_layout(self, pdf_path: Path) -> Tuple[List[PDFPage], List[LTPage]]:
        self.text = ""
        self.match_dict = {}
        with tempfile.TemporaryDirectory() as fonts_temp_dir, tempfile.TemporaryDirectory() as glyphs_temp_dir:
            fonts_temp_path = Path(fonts_temp_dir)
            glyphs_temp_path = Path(glyphs_temp_dir)
            self.__read_pdf(pdf_path, fonts_temp_path, glyphs_temp_path)
            self.__match_glyphs_and_encoding_for_all(fonts_temp_path, glyphs_temp_path)
        layouts = self.__restore_layout(pdf_path)

        return layouts

    def __read_pdf(self, pdf_path: Path, fonts_path: Path, glyphs_path: Path) -> None:
        self.__extract_fonts(pdf_path, fonts_path)
        self.__extract_glyphs(fonts_path, glyphs_path)

    def __extract_fonts(self, pdf_path: Path, fonts_path: Path) -> None:
        doc = fitz.open(pdf_path)
        xref_visited = []

        junk = 0
        for page_num in range(doc.page_count):
            page = doc.get_page_fonts(page_num)
            for fontinfo in page:
                junk += 1
                xref = fontinfo[0]
                if xref in xref_visited:
                    continue
                xref_visited.append(xref)
                font = doc.extract_font(xref, named=True)
                if font["ext"] != "n/a":
                    font_path = fonts_path.joinpath(f"{font['name']}{junk_string}{str(junk)}.{font['ext']}")
                    ofile = open(font_path, "wb")
                    ofile.write(font["content"])
                    ofile.close()
        doc.close()

    def __extract_glyphs(self, fonts_path: Path, glyphs_path: Path) -> None:
        font_files = list(fonts_path.iterdir())
        white_spaces = {}
        for font_file in font_files:
            font_white_spaces = {}
            font_name = Path(font_file).parts[-1].split(".")[0]
            font_name = re.split(junk_string, font_name)[0]
            save_path = glyphs_path.joinpath(font_name)
            font_path = fonts_path.joinpath(os.fsdecode(font_file))

            save_path.mkdir()
            save_path = str(save_path)
            font_path = str(font_path)
            ff_path = Path(__file__).parent / "fontforge_wrapper.py"

            devnull = open(os.devnull, "wb")
            if platform in ("linux", "linux2", "darwin"):
                result = subprocess.check_output(f"fontforge -script {str(ff_path)} generate_all_images {save_path} {font_path}", shell=True, stderr=devnull)
            else:
                console_command = f"ffpython {str(ff_path)} generate_all_images {save_path} {font_path}"
                try:
                    result = subprocess.check_output(console_command, stderr=devnull)
                except Exception:
                    if font_file.suffix.lower() not in [".ttf", ".otf"]:
                        continue
                    font = TTFont(font_path)
                    name_table = font["name"]
                    for record in name_table.names:
                        record.string = "undef".encode("utf-16-be")
                    font.save(font_path)

                    result = subprocess.check_output(console_command, stderr=devnull)
            devnull.close()
            result = result.decode("utf-8")
            eval_list = list(ast.literal_eval(result))
            imgs_to_resize_set = set(eval_list[0])
            empty_glyphs = eval_list[1]
            names = eval_list[2]
            codes = eval_list[3]
            name2code = dict(zip_longest(names, codes))

            if font_name not in self.__name2code:
                self.__name2code[font_name] = name2code
            else:
                self.__name2code[font_name].update(name2code)

            for img in imgs_to_resize_set:
                if is_empty(img) and "png" in img:
                    uni_whitespace = (PurePath(img).parts[-1]).split(".")[0]
                    name_whitespace = ""
                    try:
                        name_whitespace = chr(int(uni_whitespace))
                    except Exception:
                        name_whitespace = uni_whitespace
                    finally:
                        font_white_spaces[name_whitespace] = " "
                        os.remove(img)
                else:
                    correctly_resize(img)
            white_spaces[font_name] = empty_glyphs
        self.white_spaces = white_spaces

    def __match_glyphs_and_encoding_for_all(self, fonts_path: Path, glyphs_path: Path) -> None:
        fonts = fonts_path.iterdir()
        dicts = self.white_spaces
        for font_file in fonts:
            fontname_with_ext = PurePath(font_file).parts[-1]
            fontname = fontname_with_ext.split(".")[0]
            fontname = fontname.split(junk_string)[0]
            matching_res = self.__match_glyphs_and_encoding(glyphs_path.joinpath(fontname))
            if fontname in dicts:
                dicts[fontname].update(matching_res)
            else:
                dicts[fontname] = matching_res
        self.match_dict = dicts

    def __match_glyphs_and_encoding(self, images_path: Path) -> Dict[Union[str, int], str]:
        images = images_path.glob("*")
        dictionary = {}
        alphas = {}
        image_paths = [img for img in images]
        batch_size = 32
        num_batches = len(image_paths) // batch_size + (1 if len(image_paths) % batch_size != 0 else 0)
        for batch_idx in range(num_batches):
            batch_images = image_paths[batch_idx * batch_size:(batch_idx + 1) * batch_size]
            predictions = self.model.recognize_glyph(batch_images)
            for img, pred in zip(batch_images, predictions):
                key = img.parts[-1].split(".")
                key = "".join(key[:-1])
                char = chr(int(pred))
                try:
                    dictionary[chr(int(key))] = chr(int(pred))
                    k = chr(int(key))
                except Exception:
                    dictionary[key] = chr(int(pred))
                    k = key
                if char.isalpha():
                    alphas.setdefault(char.lower(), []).append((img, k))

        return dictionary

    def __extract_text_str(self, o: Union[LTChar, LTTextLineHorizontal, Iterable], cached_fonts: dict, page_text: list) -> None:
        if isinstance(o, LTChar):
            self.__process_char(o, cached_fonts)
        elif isinstance(o, LTTextLineHorizontal):
            self.__process_text_line(o, page_text)
        elif isinstance(o, Iterable):
            self.__process_iterable(o, cached_fonts, page_text)

    def __process_iterable(self, iterable_obj: Iterable, cached_fonts: dict, page_text: list) -> None:
        for item in iterable_obj:
            self.__extract_text_str(item, cached_fonts, page_text)

    def __process_text_line(self, text_line: LTTextLineHorizontal, page_text: list) -> None:
        # LTTextLineHorizontal
        text = text_line.get_text()
        text = text.replace("\n", " ").replace("\r", "").replace("\t", " ")
        page_text.append(text)

    def __process_char(self, char_obj: LTChar, cached_fonts: dict) -> None:
        # LTChar
        char = char_obj.get_text()
        match_dict_key = char_obj.fontname

        if not cached_fonts.get(char_obj.fontname):
            try:
                char_obj._text = self.match_dict[match_dict_key][char]
            except Exception:
                char_obj._text = char
            return

        if "cid" in char:
            index = int(char[1:-1].split(":")[-1])
        elif "glyph" in char:
            glyph_unicode = int(char[5:])
            index = ord(self.__unicodemaps[glyph_unicode])
        else:
            try:
                index = ord(char)
                if ord(char) > len(cached_fonts[char_obj.fontname]) and char == "’":
                    char = "'"
                    index = ord(char)
                elif ord(char) > len(cached_fonts[char_obj.fontname]):
                    char_obj._text = self.match_dict[match_dict_key][char]
                    return
            except Exception:
                char_obj._text = char
                return

        try:
            glyph_name = cached_fonts[char_obj.fontname][index]
            char_obj._text = self.match_dict[match_dict_key][glyph_name]
        except Exception:
            char_obj._text = char

    def __correct_pages_text(self, o: Union[LTChar, LTTextLineHorizontal, Iterable], cached_fonts: dict, fulltext: list) -> None:
        if isinstance(o, LTChar):
            self.__correct_char_text(o, cached_fonts)
        elif isinstance(o, Iterable):
            self.__correct_iterable_text(o, cached_fonts, fulltext)
        elif isinstance(o, LTTextLineHorizontal):
            self.__correct_line_text(o, fulltext)

    def __correct_char_text(self, char_obj: LTChar, cached_fonts: dict) -> None:
        char = char_obj.get_text()
        fontname = char_obj.fontname

        if not cached_fonts.get(fontname):
            self.__apply_match_dict(char_obj, fontname, char)
            return

        index = self.__get_char_index(char)
        if index is None:
            char_obj._text = char if char != "’" else "'"
            return

        self.__apply_correct_glyph(char_obj, fontname, index, cached_fonts)

    def __get_char_index(self, char: str) -> Optional[int]:
        if "cid" in char:
            return int(char[1:-1].split(":")[-1])
        elif "glyph" in char:
            glyph_unicode = int(char[5:])
            return ord(self.__unicodemaps[glyph_unicode])
        try:
            return ord(char)
        except Exception:
            return None

    def __apply_match_dict(self, char_obj: LTChar, fontname: str, char: str) -> None:
        try:
            char_obj._text = self.match_dict[fontname][char]
        except Exception:
            char_obj._text = char

    def __apply_correct_glyph(self, char_obj: LTChar, fontname: str, index: int, cached_fonts: dict) -> None:
        try:
            glyph_name = cached_fonts[fontname][index]
            actual_code = self.__name2code[fontname][glyph_name]
            char_obj._text = self.match_dict[fontname][chr(actual_code)]
        except Exception:
            char_obj._text = " "

    def __correct_iterable_text(self, iterable: Iterable, cached_fonts: dict, fulltext: list) -> None:
        for item in iterable:
            self.__correct_pages_text(item, cached_fonts, fulltext)

    def __correct_line_text(self, line: LTTextLineHorizontal, fulltext: list) -> None:
        text = line.get_text()
        line._text = correct_string_incorrect_chars(text)
        fulltext.append(line.get_text())

    def __restore_layout(self, pdf_path: Path, start: int = 0, end: int = 0) -> Tuple[List[PDFPage], List[LTPage]]:
        self.__cached_fonts = None
        self.__fontname2basefont = {}
        self.__unicodemaps = {}
        with open(pdf_path, "rb") as fp:
            parser = PDFParser(fp)
            document = PDFDocument(parser)
            pages_count = resolve1(document.catalog["Pages"])["Count"]
            end = pages_count if end == 0 else end

            rsrcmgr = PDFResourceManager()
            laparams = LAParams()

            device = PDFPageAggregator(rsrcmgr, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            fixed_layouts = []
            pages = []
            for page_num, page in enumerate(PDFPage.create_pages(document)):
                if page_num < start:
                    continue
                elif page_num >= end:
                    break
                interpreter.process_page(page)
                layout = device.get_result()
                cached_fonts = {}
                fonts = page.resources.get("Font")

                if not isinstance(fonts, dict):
                    Exception("fonts should be dictionary")
                for _, font_obj in fonts.items():
                    font_dict = resolve1(font_obj)
                    encoding = resolve1(font_dict.get("Encoding"))
                    f = rsrcmgr.get_font(objid=font_obj.objid, spec=font_obj.objid)
                    self.__fontname2basefont[f.fontname] = f.basefont if hasattr(f, "basefont") else f.fontname

                    if hasattr(f, "unicode_map") and hasattr(f.unicode_map, "cid2unichr"):
                        basefont_else_fontname = self.__fontname2basefont[f.fontname]
                        self.__unicodemaps[basefont_else_fontname] = f.unicode_map.cid2unichr
                    if not (isinstance(encoding, dict) and ("/Differences" in encoding or "Differences" in encoding)):
                        cached_fonts[f.fontname] = []
                        continue
                    char_set_arr = [q.name if isinstance(q, PSLiteral) else "" for q in encoding["Differences"]]
                    cached_fonts[f.fontname] = char_set_arr

                fulltext = []
                self.__cached_fonts = rsrcmgr._cached_fonts
                self.rsr = rsrcmgr
                self.__correct_pages_text(layout, cached_fonts, fulltext)
                fixed_layouts.append(layout)
                pages.append(page)

        return pages, fixed_layouts
