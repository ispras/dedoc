"""Downloading models in advance inside the docker container."""
import os
import shutil

from huggingface_hub import hf_hub_download


def download(resources_path: str) -> None:
    os.makedirs(resources_path, exist_ok=True)

    path = os.path.realpath(hf_hub_download(repo_id="dedoc/scan_orientation_efficient_net_b0", filename="model.pth"))
    shutil.move(path, os.path.join(resources_path, "scan_orientation_efficient_net_b0.pth"))

    path = os.path.realpath(hf_hub_download(repo_id="dedoc/font_classifier", filename="model.pth"))
    shutil.move(path, os.path.join(resources_path, "font_classifier.pth"))

    path = os.path.realpath(hf_hub_download(repo_id="dedoc/paragraph_classifier", filename="model.pkl.gz"))
    shutil.move(path, os.path.join(resources_path, "paragraph_classifier.pkl.gz"))

    line_clf_resources_path = os.path.join(resources_path, "line_type_classifiers")
    os.makedirs(line_clf_resources_path, exist_ok=True)
    for classifier_type in ("diploma", "law", "law_txt", "tz", "tz_txt"):
        path = os.path.realpath(hf_hub_download(repo_id="dedoc/line_type_classifiers", filename=f"{classifier_type}.pkl.gz"))
        shutil.move(path, os.path.join(line_clf_resources_path, f"{classifier_type}_classifier.pkl.gz"))


if __name__ == "__main__":
    # make the resources directory inside with project root (near the dedoc package)
    resources_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "resources")
    download(resources_path)
