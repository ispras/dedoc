from collections import defaultdict
from typing import List

import numpy as np
import pandas as pd


class TxtlayerFeatureExtractor:

    def __init__(self) -> None:
        self.eng = "".join(list(map(chr, range(ord("a"), ord("z") + 1))))
        self.rus = "".join([chr(i) for i in range(ord("а"), ord("а") + 32)] + ["ё"])
        self.lower_letters = self.eng + self.rus
        self.upper_letters = self.lower_letters.upper()
        self.letters = self.upper_letters + self.lower_letters
        self.digits = "".join([str(i) for i in range(10)])
        self.special_symbols = "<>~!@#$%^&*_+-/\"|?.,:;'`= "
        self.brackets = "{}[]()"
        self.symbols = self.letters + self.digits + self.brackets + self.special_symbols

        self.prohibited_symbols = {s: i for i, s in enumerate("[]<")}

    def transform(self, texts: List[str]) -> pd.DataFrame:
        features = defaultdict(list)

        for text in texts:
            num_letters = self.__count_symbols(text, self.letters)
            num_digits = self.__count_symbols(text, self.digits)
            num_special_symbols = self.__count_symbols(text, self.special_symbols)
            num_brackets = self.__count_symbols(text, self.brackets)
            num_rus = self.__count_symbols(text, self.rus + self.rus.upper())
            num_eng = self.__count_symbols(text, self.eng + self.eng.upper())

            features["letters_proportion"].append(num_letters / len(text))
            features["digits_proportion"].append(num_digits / len(text))
            features["special_symbols_proportion"].append(num_special_symbols / len(text))
            features["brackets_proportion"].append(num_brackets / len(text))
            features["rus_proportion"].append(num_rus / len(text))
            features["eng_proportion"].append(num_eng / len(text))

            for symbol in self.letters + self.digits:
                n = num_letters + num_digits
                # proportion of occurring english and russian letters
                features[f"{symbol}_proportion"].append(text.count(symbol) / n if n != 0 else 0.0)

            for symbol in self.special_symbols + self.brackets:
                # number of symbols
                symbol_name = symbol if symbol not in self.prohibited_symbols else f"symbol{self.prohibited_symbols[symbol]}"
                features[f"{symbol_name}_number"].append(text.count(symbol))

            # proportion of letters with symbols
            features["all_proportion"].append((num_letters + num_digits + num_brackets + num_special_symbols) / len(text) if len(text) != 0 else 0)

            case_changes = sum(1 for s1, s2 in zip(text[:-1], text[1:]) if (s1 in self.lower_letters) and (s2 in self.upper_letters))
            features["case_changes"].append(case_changes / len(text))
            symbol_changes = sum(1 for s1, s2 in zip(text[:-1], text[1:]) if (s1 in self.symbols) != (s2 in self.symbols))
            features["symbol_changes"].append(symbol_changes / len(text))
            letter_changes = sum(1 for s1, s2 in zip(text[:-1], text[1:]) if (s1 in self.letters) and (s2 not in self.symbols))
            features["letter_changes"].append(letter_changes / len(text))

            features["mean_word_length"].append(np.mean([len(word) for word in text.split()]))
            features["median_word_length"].append(np.median([len(word) for word in text.split()]))

            all_characters_ord = [ord(character) for character in text]
            trash_chars = sum(1 for s in all_characters_ord if s <= 32 or 160 <= s <= 879)
            features["trash_chars_proportion"].append(trash_chars / len(text))
            features["trash_chars_number"].append(trash_chars)
            features["std_char_ord"].append(np.std(all_characters_ord))
            features["mean_char_ord"].append(np.mean(all_characters_ord))
            features["median_char_ord"].append(np.median(all_characters_ord))
        features = pd.DataFrame(features)
        return features[sorted(features.columns)].astype(float)

    def __count_symbols(self, text: str, symbol_list: str) -> int:
        return sum(1 for symbol in text if symbol in symbol_list)
