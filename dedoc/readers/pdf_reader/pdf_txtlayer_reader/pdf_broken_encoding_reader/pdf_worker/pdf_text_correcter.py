import re
from typing import List

import numpy as np
from Levenshtein import distance

from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding_reader import config

convertdictrus = config.convert.get("convert_chars_to_rus")
convertdicteng = dict((v, k) for k, v in convertdictrus.items())

rus = ['а', 'б', 'в', 'г', 'д', 'е', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х',
       'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь', 'э', 'ю', 'я', 'o', 'a', 'c', 'e', 'x', 'k']
eng = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
       'w', 'x', 'y', 'z', 'о', "а", "с"]
onlyRus = ['я', 'й', 'ц', 'б', 'ж', 'з', 'д', 'л', 'ф', 'ш', 'щ', "ч", "ъ", "ь", "э", "ю", 'г']
onlyEng = ['q', 'w', 'f', 'i', 'j', 'l', 'z', 's', 'v', 'g']


from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding_reader.functions import get_project_root


def get_russian_and_english_words():
    from nltk.corpus import words

    english_words = set(words.words())

    ROOT_DIR = get_project_root()
    with open(f'{ROOT_DIR}/data/russian.txt', encoding='utf8') as f:
        russian_words = set(f.read().splitlines())

    rus_and_eng_names = list(english_words | russian_words)

    max_length = max(len(s) for s in rus_and_eng_names)
    result = [[] for _ in range(max_length + 1)]

    for string in rus_and_eng_names:
        length = len(string)
        result[length].append(string)
    return result


def correct_string_incorrect_chars(input_string: str):
    strings = input_string.split(' ')
    ans = []
    for word in strings:
        analized = correct_word_incorrect_chars(word)
        if analized is not None:
            ans.append(analized)
    return " ".join(ans)


def correct_word_incorrect_chars(input_string: str):
    list_of_strings = list(input_string)
    letters = {x: input_string.count(x) for x in input_string}
    latin = sum([val for val, key in zip(letters.values(), letters.keys()) if key in eng])
    cyrrilic = sum([val for val, key in zip(letters.values(), letters.keys()) if key in rus])

    converted = input_string
    if any(char in input_string.lower() for char in onlyRus):
        converted = substitute_chars_by_dict(convertdictrus, list_of_strings)
    elif any(char in input_string.lower() for char in onlyEng):
        converted = substitute_chars_by_dict(convertdicteng, list_of_strings)
    elif cyrrilic >= latin and latin + cyrrilic > 0:
        converted = substitute_chars_by_dict(convertdictrus, list_of_strings)
    elif latin > cyrrilic:
        converted = substitute_chars_by_dict(convertdicteng, list_of_strings)
    return converted


def substitute_chars_by_dict(substitutions_dict, word):
    return "".join([(substitutions_dict[item] if item.islower() else substitutions_dict[item.lower()].upper())
                    if item.lower() in substitutions_dict else item for item in word])


def correct_text(text: List[str]):
    corrected_text = []
    for page in text:
        if not page.isspace():
            res = correct_string_incorrect_chars(page)
            res = correct_case(res)
            corrected_text.append(res)
    return corrected_text


def correct_case(input_string: str):
    new_string = ''
    for i in range(len(input_string)):
        if i == 0:
            new_string += input_string[i]
        elif input_string[i - 1].isalpha() and input_string[i - 1].islower() and i + 1 < len(input_string) and \
                input_string[i + 1].isalpha() and \
                input_string[i + 1].islower():
            new_string += input_string[i].lower()
        elif input_string[i - 1].isalpha() and input_string[i - 1].isupper() and i + 1 < len(input_string) and \
                input_string[i + 1].isalpha() and \
                input_string[i + 1].isupper():
            new_string += input_string[i].upper()
        else:
            new_string += input_string[i]
    return new_string


def t9_text(text):
    words = re.findall(r'(?:\S+(?=[,\.]\s)|(?:\S+(?=\s|$))|(?:\s))', text)
    new_words = []
    for i in words:
        if len(i) == 1:
            new_words.append(i)
            continue
        corrected_word = find_closest_word(i)
        new_words.append(corrected_word)

    new_text = ''.join(new_words)
    return new_text


def find_closest_word(word):
    rus_and_eng_names = get_russian_and_english_words()
    lower_word = word.lower()
    distances = np.array(
        [distance(lower_word, i.lower(), weights=(1000, 1000, 1)) for i in rus_and_eng_names[len(lower_word)]])
    if distances.size == 0:
        return word
    if 1 - np.min(distances) / len(lower_word) < 0.8:
        russian_chars_word = substitute_chars_by_dict(convertdictrus, lower_word)
        english_chars_word = substitute_chars_by_dict(convertdicteng, lower_word)
        russian_dict = np.array([distance(russian_chars_word, i.lower(), weights=(1000, 1000, 1)) for i in
                                 rus_and_eng_names[len(lower_word)]])
        english_dict = np.array([distance(english_chars_word, i.lower(), weights=(1000, 1000, 1)) for i in
                                 rus_and_eng_names[len(lower_word)]])
        actual_word_dict = russian_dict if np.min(russian_dict) < np.min(english_dict) else english_dict
        if actual_word_dict.size == 0 or 1 - (np.min(actual_word_dict) / len(lower_word)) < 0.8:
            return word
        distances = actual_word_dict
    min_index = int(np.argmin(distances))
    correct_word = rus_and_eng_names[len(word)][min_index]
    if word.isupper():
        correct_word = correct_word.upper()
    elif word[0].isupper():
        correct_word = correct_word.capitalize()
    return correct_word


def correct_collapsed_text(text):
    text = correct_string_incorrect_chars(text)
    text = correct_case(text)
    return text


def correct_text_str(text):
    return correct_string_incorrect_chars(text)


def remove_redundant_whitespaces(text):
    return ' '.join(text.split())
