import os
import pickle
import re

from nltk.lm import MLE
from nltk.lm.preprocessing import padded_everygram_pipeline
from nltk.util import ngrams


def tokenize_doc(text_layer: str) -> str:
    """
    Tokenize text layer
    param: text_layer: text layer
    return: tokenized document text
    """
    # converting to lowercase
    text_layer = text_layer.lower()
    # remove all the special characters
    document = re.sub(r"\W", " ", text_layer)
    # remove all single characters
    document = re.sub(r"\^[a-zA-Z]\s+", " ", document)
    # substituting multiple spaces with single space
    document = re.sub(r"\s+", " ", document, flags=re.I)
    return document


def create_ngramm_list(text_layer: str, ngram_num: int) -> list:
    ngrams_iterator = list(ngrams(text_layer, ngram_num))
    ngrams_list_text = []
    for ngram_iter in ngrams_iterator:
        first, second = ngram_iter
        ngrams_list_text.append(first + second)
    return ngrams_list_text


def main() -> None:
    path_big_data = "big_dataset/"
    files_path_big_data = os.listdir(path_big_data)
    documents = []
    for files in files_path_big_data:
        file = os.listdir(path_big_data + files)
        print(files)
        for writer in file:
            try:
                with open(path_big_data + files + "/" + writer) as f:
                    text = f.read()
                    document = tokenize_doc(text)
                    documents.append(document)
                print(writer)
                break
            except Exception:
                print(Exception)
                pass
    documents = " ".join(documents)
    bigram_list = create_ngramm_list(documents, 2)
    train, vocab = padded_everygram_pipeline(2, [bigram_list])
    print(bigram_list)
    language_model_mle = MLE(2)
    language_model_mle.fit(train, vocab)
    with open("n-gram_lang_model.pkl", "wb") as f:
        pickle.dump(language_model_mle, f)


if __name__ == "__main__":
    main()
