import enum
from typing import List, Union
from typing import Type

junk_string = "_junkstring"

char_pool = dict(
    rus_eng=[
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u",
        "v", "w", "x", "y", "z", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P",
        "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "а", "б", "в", "г", "д", "е", "ж", "з", "и", "й", "к",
        "л", "м", "н", "о", "п", "р", "с", "т", "у", "ф", "х", "ц", "ч", "ш", "щ", "ъ", "ы", "ь", "э", "ю", "я",
        "А", "Б", "В", "Г", "Д", "Е", "Ж", "З", "И", "Й", "К", "Л", "М", "Н", "О", "П", "Р", "С", "Т", "У", "Ф",
        "Х", "Ц", "Ч", "Ш", "Щ", "Ъ", "Ы", "Ь", "Э", "Ю", "Я", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
        "!", '"', "#", "$", "%", "&", "'", "(", ")", "*", "+", "-", ".", ",", "/", ":", ";", "<", "=", ">", "?",
        "@", "[", "\\", "]", "^", "_", "`", "{", "|", "}", "~", "©", "™"
    ],
    rus_eng_no_reg_diff=[
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s",
        "t", "u", "v", "w", "x", "y", "z", "а", "б", "в", "г", "д", "е", "ж", "з", "и", "й", "к",
        "л", "м", "н", "о", "п", "р", "с", "т", "у", "ф", "х", "ц", "ч", "ш", "щ", "ъ", "ы", "ь", "э",
        "ю", "я", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "!", '"', "#", "$", "%", "&", "'",
        "(", ")", "*", "+", "-", ".", ",", "/", ":", ";", "<", "=", ">", "?", "@", "[", "\\", "]", "^",
        "_", "`", "{", "|", "}", "~", "©", "™"
    ],
    rus=[
        "а", "б", "в", "г", "д", "е", "ж", "з", "и", "й", "к", "л", "м", "н", "о", "п", "р", "с", "т", "у", "ф",
        "х", "ц", "ч", "ш", "щ", "ъ", "ы", "ь", "э", "ю", "я", "А", "Б", "В", "Г", "Д", "Е", "Ж", "З", "И", "Й",
        "К", "Л", "М", "Н", "О", "П", "Р", "С", "Т", "У", "Ф", "Х", "Ц", "Ч", "Ш", "Щ", "Ъ", "Ы", "Ь", "Э", "Ю",
        "Я", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "!", '"', "#", "$", "%", "&", "'", "(", ")", "*",
        "+", "-", ",", ".", "/", ":", ";", "<", "=", ">", "?", "@", "[", "\\", "]", "^", "_", "`", "{", "|",
        "}", "~", "©", "™"
    ],
    rus_no_reg_diff=[
        "а", "б", "в", "г", "д", "е", "ж", "з", "и", "й", "к", "л", "м", "н", "о", "п", "р", "с", "т", "у",
        "ф", "х", "ц", "ч", "ш", "щ", "ъ", "ы", "ь", "э", "ю", "я", "0", "1", "2", "3", "4", "5", "6", "7",
        "8", "9", "!", '"', "#", "$", "%", "&", "'", "(", ")", "*", "+", "-", ",", ".", "/", ":", ";", "<",
        "=", ">", "?", "@", "[", "\\", "]", "^", "_", "`", "{", "|", "}", "~", "©", "™"
    ],
    eng=[
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u",
        "v", "w", "x", "y", "z", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P",
        "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "!",
        '"', "#", "$", "%", "&", "'", "(", ")", "*", "+", "-", ",", ".", "/", ":", ";", "<", "=", ">", "?", "@",
        "[", "\\", "]", "^", "_", "`", "{", "|", "}", "~", "©", "™"
    ],
    eng_no_reg_diff=[
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
        "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "!", '"', "#", "$",
        "%", "&", "'", "(", ")", "*", "+", "-", ",", ".", "/", ":", ";", "<", "=", ">", "?", "@", "[",
        "\\", "]", "^", "_", "`", "{", "|", "}", "~", "©", "™"
    ]
)

other = dict(
    bottom_align=[",", ".", "_"],
    dont_aug=[
        ",", "dot", "\\", "`", "_", "-", "=", ";", ":", "quotedbl", "colon", "backslash", ")", "(", "[", "]", "<",
        ">", "~", "+", "'"
    ]
)

convert = dict(
    convert_chars_to_rus={
        "a": "а", "b": "в", "c": "с", "d": "д", "e": "е", "h": "н", "k": "к", "m": "м", "o": "о", "p": "р", "r": "г",
        "y": "у", "t": "т", "u": "и", "x": "х"
    }
)


class Language(enum.Enum):
    Russian_and_English_no_reg_diff = char_pool["rus_eng_no_reg_diff"]
    Russian_no_reg_diff = char_pool["rus_no_reg_diff"]
    English_no_reg_diff = char_pool["eng_no_reg_diff"]
    Russian_and_English = char_pool["rus_eng"]
    Russian = char_pool["rus"]
    English = char_pool["eng"]

    @classmethod
    def from_string(cls: Type["Language"], model_name: str) -> "Language":
        mapping = {
            "ruseng": cls.Russian_and_English,
            "rus": cls.Russian,
            "eng": cls.English
        }
        try:
            return mapping[model_name.lower()]
        except KeyError:
            raise ValueError("Incorrect model_name (rus, eng, ruseng)")


convertdictrus = convert.get("convert_chars_to_rus")
convertdicteng = dict((v, k) for k, v in convertdictrus.items())

rus = [
    "а", "б", "в", "г", "д", "е", "ж", "з", "и", "й", "к", "л", "м", "н", "о", "п", "р", "с", "т", "у", "ф", "х",
    "ц", "ч", "ш", "щ", "ъ", "ы", "ь", "э", "ю", "я", "o", "a", "c", "e", "x", "k"
]
eng = [
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v",
    "w", "x", "y", "z", "о", "а", "с"
]
only_rus = ["я", "й", "ц", "б", "ж", "з", "д", "л", "ф", "ш", "щ", "ч", "ъ", "ь", "э", "ю", "г"]
only_eng = ["q", "w", "f", "i", "j", "l", "z", "s", "v", "g"]


def correct_string_incorrect_chars(input_string: str) -> str:
    strings = input_string.split(" ")
    ans = []
    for word in strings:
        analyzed = correct_word_incorrect_chars(word)
        if analyzed is not None:
            ans.append(analyzed)
    return " ".join(ans)


def correct_word_incorrect_chars(input_string: str) -> str:
    list_of_strings = list(input_string)
    letters = {x: input_string.count(x) for x in input_string}
    latin = sum([val for val, key in zip(letters.values(), letters.keys()) if key in eng])
    cyrrilic = sum([val for val, key in zip(letters.values(), letters.keys()) if key in rus])

    converted = input_string
    if any(char in input_string.lower() for char in only_rus):
        converted = substitute_chars_by_dict(convertdictrus, list_of_strings)
    elif any(char in input_string.lower() for char in only_eng):
        converted = substitute_chars_by_dict(convertdicteng, list_of_strings)
    elif cyrrilic >= latin and latin + cyrrilic > 0:
        converted = substitute_chars_by_dict(convertdictrus, list_of_strings)
    elif latin > cyrrilic:
        converted = substitute_chars_by_dict(convertdicteng, list_of_strings)
    return converted


def substitute_chars_by_dict(substitutions_dict: dict, word: Union[str, List[str]]) -> str:
    return "".join([
        (substitutions_dict[item] if item.islower() else substitutions_dict[item.lower()].upper())
        if item.lower() in substitutions_dict
        else item
        for item in word
    ])


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
