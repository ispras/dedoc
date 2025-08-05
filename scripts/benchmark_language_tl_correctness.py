import os
import zipfile
from pathlib import Path

import wget
from sklearn.metrics import accuracy_score, balanced_accuracy_score, precision_recall_fscore_support

from dedoc.config import get_config
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier import LanguageTxtlayerClassifier

if __name__ == "__main__":
    data_dir = Path(get_config()["intermediate_data_path"]) / "text_layer_correctness_data"
    os.makedirs(data_dir, exist_ok=True)
    txtlayer_classifier_dataset_dir = data_dir / "data"

    if not txtlayer_classifier_dataset_dir.is_dir():
        path_out = data_dir / "data.zip"
        wget.download("https://at.ispras.ru/owncloud/index.php/s/z9WLFiKKFo2WMgW/download", str(path_out))
        with zipfile.ZipFile(path_out, "r") as zip_ref:
            zip_ref.extractall(data_dir)
        os.remove(path_out)
        print(f"Dataset downloaded to {txtlayer_classifier_dataset_dir}")
    else:
        print(f"Use cached dataset from {txtlayer_classifier_dataset_dir}")
    assert txtlayer_classifier_dataset_dir.is_dir()

    correct_test_dir = txtlayer_classifier_dataset_dir / "correct_test/all"
    not_correct_test_dir = txtlayer_classifier_dataset_dir / "not_correct_test/all"

    correct_files = [correct_test_dir / file_name for file_name in os.listdir(correct_test_dir) if file_name.endswith(".txt")]
    incorrect_files = [not_correct_test_dir / file_name for file_name in os.listdir(not_correct_test_dir) if file_name.endswith(".txt")]

    true_labels = [True for file_name in correct_files] + [False for file_name in incorrect_files]
    txtlayer_classifier = LanguageTxtlayerClassifier(config={})

    texts = []
    for file_name in correct_files + incorrect_files:
        with open(file_name, "r") as f:
            texts.append(f.read().replace("\n", " "))

    predictions = txtlayer_classifier.model.predict(texts, threshold=0.5)
    predictions = [any(pred) for pred in predictions[1]]
    b_accuracy = balanced_accuracy_score(true_labels, predictions)
    accuracy = accuracy_score(true_labels, predictions)
    w_avg = precision_recall_fscore_support(true_labels, predictions, average="weighted")
    avg = precision_recall_fscore_support(true_labels, predictions, average=None, labels=[False, True])

    path_result = Path(__file__).parent.parent / "resources/benchmarks/benchmarks_language_tl_correctness.txt"
    output = f"Correct texts: {len(correct_files)}, incorrect texts: {len(incorrect_files)}\n"
    output += f"--- Balanced Accuracy --- = {b_accuracy}\n"
    output += f"--- Accuracy --- = {accuracy}\n"
    output += f"--- Weighted --- Precision = {w_avg[0]}, Recall={w_avg[1]}, F1={w_avg[2]}\n"
    output += f"--- Class corrected --- : Precision = {avg[0][0]}, Recall={avg[1][0]}, F1={avg[2][0]}\n"
    output += f"--- Class incorrected --- : Precision = {avg[0][1]}, Recall={avg[1][1]}, F1={avg[2][1]}\n"
    print(output)
    with open(path_result, "w") as f:
        f.write(output)
    print(f"Save result in {path_result}")
