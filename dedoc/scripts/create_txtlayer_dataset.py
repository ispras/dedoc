import argparse
import os
import random
import re
import tempfile
from abc import ABC, abstractmethod
from typing import List, Tuple

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
from tqdm import tqdm

from dedoc.readers import PdfImageReader


class CorrectTextGenerator:
    def __init__(self) -> None:
        self.citation = re.compile(r'\[\d+]')
        self.meta = re.compile(r'\[править \| править код]')
        self.symbols = re.compile(r'[→←↑]')

        self.title_url = "https://{lang}.wikipedia.org/w/api.php?origin=*&action=query&format=json&list=random&rnlimit=1&rnnamespace=0"
        self.article_url = "https://{lang}.wikipedia.org/w/api.php?origin=*&action=parse&format=json&page={title}&prop=text"

    def get_random_text(self, lang: str) -> str:
        article_text_fixed = ""

        while len(article_text_fixed) == 0:
            try:
                # 1 - Get random title of the article in Wikipedia
                title_result = requests.post(self.title_url.format(lang=lang))
                title_result_dict = title_result.json()
                title = title_result_dict["query"]["random"][0]["title"]

                # 2 - Get text the article
                article_result = requests.post(self.article_url.format(lang=lang, title=title))
                article_result_dict = article_result.json()
                article = article_result_dict["parse"]["text"]['*']
                bs = BeautifulSoup(article, 'html.parser')
                article_text = bs.get_text()

                # 3 - Clear text of the article from unused symbols
                article_text_fixed = re.sub(self.citation, '', article_text)
                article_text_fixed = re.sub(self.meta, "", article_text_fixed)
                article_text_fixed = re.sub(self.symbols, "", article_text_fixed)
                article_text_fixed = re.sub(r'\n+', "\n", article_text_fixed)
            except:  # noqa
                article_text_fixed = ""

        return article_text_fixed


class Corruptor(ABC):
    @abstractmethod
    def corrupt(self, text: str, lang: str) -> str:
        pass


class EncodingCorruptor(Corruptor):
    def __init__(self) -> None:
        self.encodings = {
            "en": {
                "input": ['cp1026'],
                "output": ['cp1256', 'cp437', 'cp775', 'cp852', 'cp855', 'cp857', 'cp860', 'cp861', 'cp862', 'cp863', 'cp866', 'gb18030', 'hp_roman8',
                           'iso8859_10', 'iso8859_11', 'iso8859_13', 'iso8859_14', 'iso8859_16', 'iso8859_2', 'iso8859_4', 'iso8859_5', 'koi8_r',
                           'mac_cyrillic', 'mac_greek', 'mac_latin2', 'mac_roman']

            },
            "ru": {
                "input": ['cp855', 'cp866', 'gb18030', 'iso8859_5', 'koi8_r', 'mac_cyrillic', 'utf_8'],
                "output": ['cp1026', 'cp1256', 'cp437', 'cp775', 'cp850', 'cp852', 'cp863', 'cp866', 'hp_roman8', 'iso8859_10', 'iso8859_11',
                           'iso8859_13', 'iso8859_14', 'iso8859_15', 'iso8859_16', 'iso8859_2', 'iso8859_4', 'iso8859_5', 'iso8859_9', 'koi8_r',
                           'mac_cyrillic', 'mac_greek', 'mac_latin2', 'mac_roman', 'cp1140', 'cp273', 'cp855', 'cp860', 'cp861', 'cp857', 'cp500',
                           'cp862', 'gb18030']

            }
        }

    def corrupt(self, text: str, lang: str) -> str:
        input_encoding, output_encoding = "", ""
        while input_encoding == output_encoding:
            input_encoding = random.choice(self.encodings[lang]["input"])
            output_encoding = random.choice(self.encodings[lang]["output"])

        encoded, decoded = "", ""
        while encoded == "" and text != "":
            try:
                encoded = text.encode(encoding=input_encoding)
            except UnicodeEncodeError as e:
                text = text[:int(e.args[2])] + text[int(e.args[3]):]
                encoded = ""

        while decoded == "" and encoded != "":
            try:
                decoded = encoded.decode(encoding=output_encoding)
            except UnicodeDecodeError as e:
                encoded = encoded[:int(e.args[2])] + encoded[int(e.args[3]):]
                decoded = ""

        return decoded


class OCRCorruptor:
    def __init__(self) -> None:
        self.image_reader = PdfImageReader(config=dict(n_jobs=1))
        self.max_images = 10
        self.page_size = (2480, 3508)
        self.font_size = 50
        self.line_gap = 50
        self.horizontal_padding = 50
        self.vertical_padding = 50

        self.text_color = (0, 0, 0)
        self.background_color = (255, 255, 255)

        font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "Arial_Narrow.ttf"))
        self.font = ImageFont.truetype(font_path, self.font_size)

    def corrupt(self, text: str, lang: str) -> str:
        ocr_lang = "en" if lang == "ru" else "ru"

        with tempfile.TemporaryDirectory() as tmpdir:
            # 1 - save images with text
            images_path_list = self.__create_images(text, tmpdir)

            # 2 - read text from the image using OCR with another language
            lines = []
            for image_path in images_path_list:
                document = self.image_reader.read(image_path, parameters=dict(language=ocr_lang,
                                                                              need_pdf_table_analysis="false",
                                                                              document_orientation="no_change",
                                                                              is_one_column_document="true"))
                lines.extend(document.lines)

        return "".join([line.line for line in lines])

    def __create_images(self, text: str, out_dir: str) -> List[str]:
        image_paths = []
        img, draw = self.__create_page()
        lines = text.split("\n")
        x, y = self.horizontal_padding, self.vertical_padding

        for line in lines:
            words = line.split()

            for word in words:
                x_min, y_min, x_max, y_max = draw.textbbox((x, y), word, self.font)
                if x_max + self.horizontal_padding >= self.page_size[0]:
                    x = self.horizontal_padding
                    y += self.font_size + self.line_gap

                if y_max + self.vertical_padding >= self.page_size[1]:
                    img_path = os.path.join(out_dir, f"{len(image_paths)}.png")
                    img.save(img_path)
                    image_paths.append(img_path)
                    if len(image_paths) >= self.max_images:
                        return image_paths

                    img, draw = self.__create_page()
                    x, y = self.horizontal_padding, self.vertical_padding

                x_min, y_min, x_max, y_max = draw.textbbox((x, y), word, self.font)
                draw.text((x, y), word, self.text_color, font=self.font)
                x = x_max + self.font_size

            y += self.font_size + self.line_gap
            x = self.horizontal_padding

        return image_paths

    def __create_page(self) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        page_size = self.page_size
        img_arr = np.zeros((page_size[1], page_size[0], 3), dtype=np.uint8)
        img_arr[:, :] = self.background_color
        img = Image.fromarray(img_arr)
        draw = ImageDraw.Draw(img)
        return img, draw


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_size", type=int, help="Number of images in each text group (correct/incorrect) for each language (ru, en)."
                                                         "E.g. if dataset_size=1000, 4000 images will be generated overall", default=1000)
    parser.add_argument("--start_number", type=int, help="Number from which to start images numbering", default=0)
    parser.add_argument("--out_dir", help="Path to the directory to save the data", default="generated_data")
    parser.add_argument("--correct_dir", help="Name of the directory with correct texts", default="correct")
    parser.add_argument("--incorrect_dir", help="Name of the directory with incorrect texts", default="incorrect")
    args = parser.parse_args()

    text_generator = CorrectTextGenerator()
    corruptor_list = [OCRCorruptor(), EncodingCorruptor()]

    os.makedirs(os.path.join(args.out_dir, args.correct_dir), exist_ok=True)
    os.makedirs(os.path.join(args.out_dir, args.incorrect_dir), exist_ok=True)

    i = args.start_number
    print("Generating incorrect texts")
    for _ in tqdm(range(args.dataset_size)):
        for language in ("ru", "en"):
            text = ""

            while not text:
                try:
                    text = text_generator.get_random_text(lang=language)
                    corruptor = random.choice(corruptor_list)
                    text = corruptor.corrupt(text, lang=language)
                except Exception as e:
                    print(e)
                    text = ""

            with open(os.path.join(args.out_dir, args.incorrect_dir, f"{i:08d}_{language}.txt"), "w") as f:
                f.write(text)
            i += 1

    i = args.start_number
    print("Generating correct texts")
    for _ in tqdm(range(args.dataset_size)):
        for language in ("ru", "en"):

            text = text_generator.get_random_text(lang=language)

            with open(os.path.join(args.out_dir, args.correct_dir, f"{i:08d}_{language}.txt"), "w") as f:
                f.write(text)
            i += 1
