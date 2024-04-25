"""
Merge results for all classifiers after running training script `train_fintoc_classifier.py`.
Results are represented in a table (.html file) in benchmarks directory.

Results are obtained from cross-validation on the training set from FinTOC 2022 Shared task (https://wp.lancs.ac.uk/cfie/fintoc2022/).
Three languages are supported: English, French and Spanish ("en", "fr", "sp").
Two readers are used: `PdfTabbyReader` and `PdfTxtlayerReader` ("tabby", "txt_layer").
"""
import json
import os
from collections import defaultdict

import pandas as pd

if __name__ == "__main__":
    scores_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "fintoc2022", "scores"))
    benchmarks_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "benchmarks"))

    assert os.path.isdir(scores_dir), "Directory with scores doesn't exist, run `train_fintoc_classifier.py` beforehand"

    all_scores_dict = defaultdict(list)
    names = []
    for scores_file in sorted(os.listdir(scores_dir)):
        if not scores_file.endswith(".json"):
            continue

        # files are named like: scores_en_tabby.json
        with open(os.path.join(scores_dir, scores_file), "r") as f:
            scores_dict = json.load(f)

        names.append(scores_file[len("scores_"):-len(".json")])

        for i, td_score in enumerate(scores_dict["td_scores"]):
            all_scores_dict[f"TD {i}"].append(td_score)
        all_scores_dict["TD mean"].append(scores_dict["td_mean"])

        for i, toc_score in enumerate(scores_dict["toc_scores"]):
            all_scores_dict[f"TOC {i}"].append(toc_score)
        all_scores_dict["TOC mean"].append(scores_dict["toc_mean"])

    scores_df = pd.DataFrame(all_scores_dict, index=names)
    with open(os.path.join(benchmarks_dir, "fintoc_scores.html"), "w") as f:
        f.write(scores_df.to_html())
