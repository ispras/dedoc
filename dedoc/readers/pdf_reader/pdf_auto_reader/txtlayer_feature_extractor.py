from collections import defaultdict
from typing import List

import numpy as np
import pandas as pd


class TxtlayerFeatureExtractor:

    def transform(self, texts: List[str]) -> pd.DataFrame:
        from dedoc.structure_extractors.feature_extractors.char_features import letters, digits, special_symbols, brackets, rus, eng, prohibited_symbols, \
            lower_letters, upper_letters, symbols, count_symbols

        features = defaultdict(list)

        for text in texts:
            num_letters = count_symbols(text, letters)
            num_digits = count_symbols(text, digits)
            num_special_symbols = count_symbols(text, special_symbols)
            num_brackets = count_symbols(text, brackets)
            num_rus = count_symbols(text, rus + rus.upper())
            num_eng = count_symbols(text, eng + eng.upper())

            features["letters_proportion"].append(num_letters / len(text))
            features["digits_proportion"].append(num_digits / len(text))
            features["special_symbols_proportion"].append(num_special_symbols / len(text))
            features["brackets_proportion"].append(num_brackets / len(text))
            features["rus_proportion"].append(num_rus / len(text))
            features["eng_proportion"].append(num_eng / len(text))

            for symbol in letters + digits:
                n = num_letters + num_digits
                # proportion of occurring english and russian letters
                features[f"{symbol}_proportion"].append(text.count(symbol) / n if n != 0 else 0.0)

            for symbol in special_symbols + brackets:
                # number of symbols
                symbol_name = symbol if symbol not in prohibited_symbols else f"symbol{prohibited_symbols[symbol]}"
                features[f"{symbol_name}_number"].append(text.count(symbol))

            # proportion of letters with symbols
            features["all_proportion"].append((num_letters + num_digits + num_brackets + num_special_symbols) / len(text) if len(text) != 0 else 0)

            case_changes = sum(1 for s1, s2 in zip(text[:-1], text[1:]) if (s1 in lower_letters) and (s2 in upper_letters))
            features["case_changes"].append(case_changes / len(text))
            symbol_changes = sum(1 for s1, s2 in zip(text[:-1], text[1:]) if (s1 in symbols) != (s2 in symbols))
            features["symbol_changes"].append(symbol_changes / len(text))
            letter_changes = sum(1 for s1, s2 in zip(text[:-1], text[1:]) if (s1 in letters) and (s2 not in symbols))
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
