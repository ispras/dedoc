import enum
from functools import cached_property

char_pool = dict(
    rus_eng=["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u",
             "v", "w", "x", "y", "z", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P",
             "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "а", "б", "в", "г", "д", "е", "ж", "з", "и", "й", "к",
             "л", "м", "н", "о", "п", "р", "с", "т", "у", "ф", "х", "ц", "ч", "ш", "щ", "ъ", "ы", "ь", "э", "ю", "я",
             "А", "Б", "В", "Г", "Д", "Е", "Ж", "З", "И", "Й", "К", "Л", "М", "Н", "О", "П", "Р", "С", "Т", "У", "Ф",
             "Х", "Ц", "Ч", "Ш", "Щ", "Ъ", "Ы", "Ь", "Э", "Ю", "Я", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
             "!", """, "#", "$", "%", "&", """, "(", ")", "*", "+", "-", ".", ",", "/", ":", ";", "<", "=", ">", "?",
             "@", "[", "\\", "]", "^", "_", "`", "{", "|", "}", "~", "©", "™"],
    rus_eng_no_reg_diff=["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s",
                         "t", "u", "v", "w", "x", "y", "z", "а", "б", "в", "г", "д", "е", "ж", "з", "и", "й", "к",
                         "л", "м", "н", "о", "п", "р", "с", "т", "у", "ф", "х", "ц", "ч", "ш", "щ", "ъ", "ы", "ь", "э",
                         "ю", "я", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "!", """, "#", "$", "%", "&", """,
                         "(", ")", "*", "+", "-", ".", ",", "/", ":", ";", "<", "=", ">", "?", "@", "[", "\\", "]", "^",
                         "_", "`", "{", "|", "}", "~", "©", "™"],
    rus=["а", "б", "в", "г", "д", "е", "ж", "з", "и", "й", "к", "л", "м", "н", "о", "п", "р", "с", "т", "у", "ф",
         "х", "ц", "ч", "ш", "щ", "ъ", "ы", "ь", "э", "ю", "я", "А", "Б", "В", "Г", "Д", "Е", "Ж", "З", "И", "Й",
         "К", "Л", "М", "Н", "О", "П", "Р", "С", "Т", "У", "Ф", "Х", "Ц", "Ч", "Ш", "Щ", "Ъ", "Ы", "Ь", "Э", "Ю",
         "Я", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "!", """, "#", "$", "%", "&", """, "(", ")", "*",
         "+", "-", ",", ".", "/", ":", ";", "<", "=", ">", "?", "@", "[", "\\", "]", "^", "_", "`", "{", "|",
         "}", "~", "©", "™"],
    rus_no_reg_diff=["а", "б", "в", "г", "д", "е", "ж", "з", "и", "й", "к", "л", "м", "н", "о", "п", "р", "с", "т", "у",
                     "ф", "х", "ц", "ч", "ш", "щ", "ъ", "ы", "ь", "э", "ю", "я", "0", "1", "2", "3", "4", "5", "6", "7",
                     "8", "9", "!", """, "#", "$", "%", "&", """, "(", ")", "*", "+", "-", ",", ".", "/", ":", ";", "<",
                     "=", ">", "?", "@", "[", "\\", "]", "^", "_", "`", "{", "|", "}", "~", "©", "™"],
    eng=["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u",
         "v", "w", "x", "y", "z", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P",
         "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "!",
         """, "#", "$", "%", "&", """, "(", ")", "*", "+", "-", ",", ".", "/", ":", ";", "<", "=", ">", "?", "@",
         "[", "\\", "]", "^", "_", "`", "{", "|", "}", "~", "©", "™"],
    eng_no_reg_diff=["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
                     "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "!", """, "#", "$",
                     "%", "&", """, "(", ")", "*", "+", "-", ",", ".", "/", ":", ";", "<", "=", ">", "?", "@", "[",
                     "\\", "]", "^", "_", "`", "{", "|", "}", "~", "©", "™"]
)

other = dict(
    bottom_align=[",", ".", "_"],
    dont_aug=[",", "dot", "\\", "`", "_", "-", "=", ";", ":", "quotedbl", "colon", "backslash", ")", "(", "[", "]" "<",
              ">", "~", "+", "'"]
)
convert = dict(
    convert_chars_to_rus={"a": "а", "b": "в", "c": "с", "d": "д", "e": "е", "h": "н", "k": "к", "m": "м", "o": "о",
                          "p": "р", "r": "г", "y": "у", "t": "т", "u": "и", "x": "х", },
)


class FolderPaths:
    @cached_property
    def paths(self):
        from pathlib import Path
        from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding_reader.functions import get_project_root
        ROOT_DIR = get_project_root()
        return dict(
            fonts_folders=Path(ROOT_DIR, "data", "fonts_folders"),
            images_folder=Path(ROOT_DIR, "data/datasets/test2"),
            output_train=Path(ROOT_DIR, "data/datasets/images/output"),
            last_prepared_data=Path(ROOT_DIR, "data/datasets/last_prepared"),
            extracted_data_folder=Path(ROOT_DIR, "data/pdfdata"),
            extracted_fonts_folder=Path(ROOT_DIR, "data/pdfdata/extracted_fonts"),
            extracted_glyphs_folder=Path(ROOT_DIR, "data/pdfdata/glyph_images"),
            default_models_folder=Path(ROOT_DIR, "data/models/default_models"),
            custom_models_folder=Path(ROOT_DIR, "data/models/custom_models"),
            datasets_folder=Path(ROOT_DIR, "data", "datasets"),
            ffwraper_folder=Path(ROOT_DIR, "ffwrapper", "fontforge_wrapper.py")
        )


folders = FolderPaths().paths


def get_default_models():
    from pathlib import Path

    models_folder = Path(folders.get("default_models_folder"))
    return [f.stem for f in models_folder.glob("*.h5")]


default_models = get_default_models()


def chars_to_code(char_list: list):
    return [ord(i) for i in char_list]


class Language(enum.Enum):
    Russian_and_English_no_reg_diff = char_pool["rus_eng_no_reg_diff"]
    Russian_no_reg_diff = char_pool["rus_no_reg_diff"]
    English_no_reg_diff = char_pool["eng_no_reg_diff"]
    Russian_and_English = char_pool["rus_eng"]
    Russian = char_pool["rus"]
    English = char_pool["eng"]

    @classmethod
    def from_string(cls, model_name: str):
        mapping = {
            "ruseng": cls.Russian_and_English,
            "rus": cls.Russian,
            "eng": cls.English
        }
        try:
            return mapping[model_name.lower()]
        except KeyError:
            raise ValueError(f"Incorrect model_name (rus, eng, ruseng)")
