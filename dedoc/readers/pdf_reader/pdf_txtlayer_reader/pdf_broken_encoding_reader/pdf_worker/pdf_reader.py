import ast
import os
import re
import shutil
import subprocess
from pathlib import Path, PurePath
from sys import platform
from typing import Any, Iterable
from typing import Union
from itertools import zip_longest

import fitz
from fontTools.ttLib import TTFont
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTChar, LTTextLineHorizontal
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdftypes import resolve1
from pdfminer.psparser import PSLiteral

import dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding_reader.config as config
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding_reader import functions
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding_reader.functions import junk_string, \
    correctly_resize
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding_reader.model import Model
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding_reader.pdf_worker import pdf_text_correcter
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding_reader.pdf_worker.pdf_text_correcter import \
    correct_string_incorrect_chars


class PDFReader:
    def __init__(self, model: Model):
        self.extract_path = config.folders.get('extracted_data_folder')
        self.model = model
        self.text = None
        self.match_dict = {}
        self.__cached_fonts = None
        self.__fontname2basefont = {}
        self.__unicodemaps = {}
        self.__need2correct = False
        self.__name2code = {}
        self.__fonts_path = config.folders.get('extracted_fonts_folder')
        self.__glyphs_path = config.folders.get('extracted_glyphs_folder')

        assert len(self.model.labels) > 0

        rus = False
        eng = False
        for i in self.model.labels:
            if ord('a') <= i <= ord('z'):
                eng = True

            elif ord('а') <= i <= ord('я'):
                rus = True

            if rus and eng:
                self.__need2correct = True
                break

    @classmethod
    def load_default_model(cls, default_model: Union[config.DefaultModel, str] = config.DefaultModel.Russian_and_English):
        if type(default_model) == config.DefaultModel:
            new_model = Model.load_default_model(default_model=default_model)
        else:
            new_model = config.DefaultModel.from_string(default_model)
        new_model = Model.load_default_model(new_model)
        reader = cls(model=new_model)
        return reader

    @classmethod
    def load_model(cls, model_and_labels_path: Path):
        """
        h5/keras and json with model's labels should be in folder
        """
        assert len([name for name in model_and_labels_path.iterdir() if model_and_labels_path.joinpath(name).is_file()]) == 2,\
            "should be two files in folder: h5, json"

        new_model = Model.load_by_model_and_labels_folder(model_and_labels_path)
        return cls(new_model)

    def restore_text(self, pdf_path: Path, start_page: int = 0, end_page: int = 0) -> str:
        assert end_page > start_page or start_page == end_page == 0, "wrong pages range"
        self.text = ''
        self.match_dict = {}
        self.__read_pdf(pdf_path)
        self.__match_glyphs_and_encoding_for_all()
        fonts_match_dict = self.match_dict
        text = self.__restore_text(pdf_path, start=start_page, end=end_page)
        if self.__need2correct:
            text = pdf_text_correcter.correct_collapsed_text(text)
        return text

    def __read_pdf(self, pdf_path: Path):
        self.__extract_fonts(pdf_path)
        self.__extract_glyphs()

    def __extract_fonts(self, pdf_path: Path):
        if os.path.isdir(self.__fonts_path):
            shutil.rmtree(self.__fonts_path)
        os.makedirs(self.__fonts_path)
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
                if font['ext'] != 'n/a':
                    font_path = self.__fonts_path.joinpath(f"{font['name']}{junk_string}{str(junk)}.{font['ext']}")
                    ofile = open(font_path, 'wb')
                    ofile.write(font['content'])
                    ofile.close()
        doc.close()

    def __extract_glyphs(self):
        if os.path.isdir(self.__glyphs_path):
            shutil.rmtree(self.__glyphs_path)
        os.makedirs(self.__glyphs_path)
        font_files = os.listdir(os.fsencode(self.__fonts_path))
        white_spaces = {}
        for font_file in font_files:
            font_white_spaces = {}
            font_name = os.fsdecode(font_file)
            font_name = font_name.split('.')[0]
            font_name = re.split(junk_string, font_name)[0]
            save_path = self.__glyphs_path.joinpath(font_name)
            if not os.path.isdir(save_path):
                os.makedirs(save_path)
            font_path = self.__fonts_path.joinpath(os.fsdecode(font_file))

            save_path = str(save_path)
            font_path = str(font_path)
            ff_path = config.folders.get('ffwraper_folder')

            devnull = open(os.devnull, 'wb')
            if platform == 'linux' or platform == 'linux2':
                result = subprocess.check_output(f"fontforge -script {str(ff_path)} False {save_path} {font_path}", shell=True, stderr=devnull)
            else:
                console_command = f"ffpython {str(ff_path)} False {save_path} {font_path}"
                try:
                    result = subprocess.check_output(console_command, stderr=devnull)
                except:
                    if Path(font_file.decode()).suffix not in ['.ttf', '.otf']:
                        continue
                    font = TTFont(font_path)
                    name_table = font['name']
                    for record in name_table.names:
                        record.string = 'undef'.encode('utf-16-be')
                    font.save(font_path)

                    result = subprocess.check_output(console_command, stderr=devnull)

            result = result.decode('utf-8')
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
                if functions.is_empty(img) and "png" in img:
                    uni_whitespace = (PurePath(img).parts[-1]).split('.')[0]
                    name_whitespace = ''
                    try:
                        name_whitespace = chr(int(uni_whitespace))
                    except:
                        name_whitespace = uni_whitespace
                    finally:
                        font_white_spaces[name_whitespace] = ' '
                        os.remove(img)
                else:
                    correctly_resize(img)
            white_spaces[font_name] = empty_glyphs
        self.white_spaces = white_spaces

    def __match_glyphs_and_encoding_for_all(self):
        extracted_fonts_folder = config.folders.get("extracted_fonts_folder")
        fonts = extracted_fonts_folder.glob("*")
        dicts = {}
        dicts = self.white_spaces
        for font_file in fonts:
            fontname_with_ext = PurePath(font_file).parts[-1]
            fontname = fontname_with_ext.split('.')[0]
            fontname = fontname.split(junk_string)[0]
            matching_res = self.__match_glyphs_and_encoding(self.__glyphs_path.joinpath(fontname))
            font_name_without_prefix = fontname.split('+')[1] if '+' in fontname else fontname
            if fontname in dicts:
                dicts[fontname].update(matching_res)
            else:
                dicts[fontname] = matching_res
        self.match_dict = dicts


    def __match_glyphs_and_encoding(self, images_path: Path):
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
                key = img.parts[-1].split('.')
                key = ''.join(key[:-1])
                char = chr(int(pred))
                try:
                    dictionary[chr(int(key))] = chr(int(pred))
                    k = chr(int(key))
                except:
                    dictionary[key] = chr(int(pred))
                    k = key
                if char.isalpha():
                    alphas.setdefault(char.lower(), []).append((img, k))

        return dictionary

    def __restore_text(self, pdf_path, start=0, end=0):
        self.__cached_fonts = None
        self.__fontname2basefont = {}
        self.__unicodemaps = {}
        with open(pdf_path, 'rb') as fp:
            parser = PDFParser(fp)
            document = PDFDocument(parser)
            pages_count = resolve1(document.catalog['Pages'])['Count']
            end = pages_count if end == 0 else end

            rsrcmgr = PDFResourceManager()
            laparams = LAParams()

            # Create a PDF device object
            device = PDFPageAggregator(rsrcmgr, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            full_text = ""
            # Iterate through each page of the PDF
            for page_num, page in enumerate(PDFPage.create_pages(document)):
                if page_num < start:
                    continue
                elif page_num >= end:
                    break
                interpreter.process_page(page)
                layout = device.get_result()
                cached_fonts = {}
                fonts = page.resources.get('Font')

                if not isinstance(fonts, dict):
                    Exception('fonts should be dictionary, ti nepravilno napisal kod(')
                for font_key, font_obj in fonts.items():
                    font_dict = resolve1(font_obj)
                    encoding = resolve1(font_dict.get("Encoding"))
                    f = rsrcmgr.get_font(objid=font_obj.objid, spec={'name': resolve1(font_obj)['BaseFont'].name})
                    self.__fontname2basefont[f.fontname] = f.basefont if hasattr(f, 'basefont') else f.fontname

                    if hasattr(f, 'unicode_map') and hasattr(f.unicode_map, 'cid2unichr'):
                        basefont_else_fontname = self.__fontname2basefont[f.fontname]
                        self.__unicodemaps[basefont_else_fontname] = f.unicode_map.cid2unichr
                    if not (isinstance(encoding, dict) and ('/Differences' in encoding or 'Differences' in encoding)):
                        cached_fonts[f.fontname] = []
                        continue
                    char_set_arr = [q.name if isinstance(q, PSLiteral) else '' for q in encoding['Differences']]
                    cached_fonts[f.fontname] = char_set_arr


                self.__cached_fonts = rsrcmgr._cached_fonts
                page_text = []

                self.__extract_text_str(layout, cached_fonts, page_text)
                full_text += ''.join(page_text)

        self.text = functions.remove_hyphenations(self.text)

        self.text = re.sub(r'\s+', ' ', self.text)

        return full_text

    def __extract_text_str(self, o: Any, cached_fonts: dict, page_text: list):
        if isinstance(o, LTChar):
            char = o.get_text()
            match_dict_key = o.fontname
            if cached_fonts.get(o.fontname) is None or not cached_fonts[o.fontname]:
                try:
                    o._text = self.match_dict[match_dict_key][char]
                except:
                    o._text = char
                    return
                return
            index = -1
            if 'cid' in char:
                index = int(char[1:-1].split(':')[-1])
            elif 'glyph' in char:
                glyph_unicode = int(char[5:])
                index = ord(self.__unicodemaps[glyph_unicode])
            else:
                try:
                    index = ord(char)
                    if ord(char) > len(cached_fonts[o.fontname]) and char == '’':
                        char = "'"
                        index = ord(char)
                    elif ord(char) > len(cached_fonts[o.fontname]):
                        o._text = self.match_dict[match_dict_key][char]
                        return
                except:
                    o._text = char
                    return
            try:
                glyph_name = cached_fonts[o.fontname][index]
                o._text = self.match_dict[match_dict_key][glyph_name]
            except:
                o._text = char
        elif isinstance(o, Iterable):
            for i in o:
                self.__extract_text_str(i, cached_fonts, page_text)

        if isinstance(o, LTTextLineHorizontal):
            text = o.get_text()
            text = text.replace('\n', ' ')
            text = text.replace('\r', '')
            text = text.replace('\t', ' ')
            page_text.append(text)

    def __correct_pages_text(self, o: Any, cached_fonts: dict, fulltext: list):
        if isinstance(o, LTChar):
            char = o.get_text()
            match_dict_key = o.fontname
            if cached_fonts.get(o.fontname) is None or not cached_fonts[o.fontname]:
                try:
                    o._text = self.match_dict[match_dict_key][char]
                except:
                    o._text = char
                    return
                return
            index = -1
            if 'cid' in char:
                index = int(char[1:-1].split(':')[-1])
            elif 'glyph' in char:
                glyph_unicode = int(char[5:])
                index = ord(self.__unicodemaps[glyph_unicode])
            else:
                try:
                    index = ord(char)
                    if ord(char) > len(cached_fonts[o.fontname]) and char == '’':
                        char = "'"
                        index = ord(char)
                    elif ord(char) > len(cached_fonts[o.fontname]):
                        o._text = self.match_dict[match_dict_key][char]
                        return
                except:
                    o._text = char
                    return
            try:
                glyph_name = cached_fonts[o.fontname][index]
                actual_code = self.__name2code[match_dict_key][glyph_name]
                o._text = self.match_dict[match_dict_key][chr(actual_code)]

            except:
                o._text = ' '
        elif isinstance(o, Iterable):
            for i in o:
                self.__correct_pages_text(i, cached_fonts, fulltext)

        if isinstance(o, LTTextLineHorizontal):
            text = o.get_text()
            o._text = correct_string_incorrect_chars(text)
            fulltext.append(o.get_text())

    def get_correct_layout(self, pdf_path):

        self.text = ''
        self.match_dict = {}
        self.__read_pdf(pdf_path)
        self.__match_glyphs_and_encoding_for_all()
        layouts = self.__restore_layout(pdf_path)

        return layouts

    def __restore_layout(self, pdf_path, start=0, end=0):
        self.__cached_fonts = None
        self.__fontname2basefont = {}
        self.__unicodemaps = {}
        with open(pdf_path, 'rb') as fp:
            parser = PDFParser(fp)
            document = PDFDocument(parser)
            pages_count = resolve1(document.catalog['Pages'])['Count']
            end = pages_count if end == 0 else end

            rsrcmgr = PDFResourceManager()
            laparams = LAParams()

            # Create a PDF device object
            device = PDFPageAggregator(rsrcmgr, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            pages_text = []
            fixed_layouts = []
            pages = []
            # Iterate through each page of the PDF
            for page_num, page in enumerate(PDFPage.create_pages(document)):
                if page_num < start:
                    continue
                elif page_num >= end:
                    break
                interpreter.process_page(page)
                layout = device.get_result()
                cached_fonts = {}
                fonts = page.resources.get('Font')

                if not isinstance(fonts, dict):
                    Exception('fonts should be dictionary, ti nepravilno napisal kod(')
                for font_key, font_obj in fonts.items():
                    font_dict = resolve1(font_obj)
                    encoding = resolve1(font_dict.get("Encoding"))
                    f = rsrcmgr.get_font(objid=font_obj.objid, spec=font_obj.objid)
                    self.__fontname2basefont[f.fontname] = f.basefont if hasattr(f, 'basefont') else f.fontname

                    if hasattr(f, 'unicode_map') and hasattr(f.unicode_map, 'cid2unichr'):
                        basefont_else_fontname = self.__fontname2basefont[f.fontname]
                        self.__unicodemaps[basefont_else_fontname] = f.unicode_map.cid2unichr
                    if not (isinstance(encoding, dict) and ('/Differences' in encoding or 'Differences' in encoding)):
                        cached_fonts[f.fontname] = []
                        continue
                    char_set_arr = [q.name if isinstance(q, PSLiteral) else '' for q in encoding['Differences']]
                    cached_fonts[f.fontname] = char_set_arr

                fulltext = []
                self.__cached_fonts = rsrcmgr._cached_fonts
                self.rsr = rsrcmgr
                self.__correct_pages_text(layout, cached_fonts, fulltext)
                fixed_layouts.append(layout)
                pages.append(page)

        return [pages, fixed_layouts]
