"""Downloading models in advance inside the docker container."""

"""
These are versions of the models that are used at the current moment - hashes of commits from https://huggingface.co/dedoc.
Keys are the names of repositories with models.
"""
model_hash_dict = dict(
    txtlayer_classifier="9ca1de749d8d37147b00a3a228e03ee1776c695f",
    scan_orientation_efficient_net_b0="c60812552a1be624476c1e5b58599867b36f8d4e",
    font_classifier="db4481ad60ab050cbb42079b64f97f9e431feb07",
    paragraph_classifier="97c4b78bc20d87ec7d53389e09f1ca35c6ade067",
    line_type_classifiers="6ad0eacbfdea065b658cb6f039d13f75245d51ae",
    fintoc_classifiers="6a907b7d2437c3f61ac9c506f67175207982fae8"
)


def download_from_hub(out_dir: str, out_name: str, repo_name: str, hub_name: str) -> None:
    import os
    import shutil
    from huggingface_hub import hf_hub_download

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.realpath(hf_hub_download(repo_id=f"dedoc/{repo_name}", filename=hub_name, revision=model_hash_dict[repo_name]))
    shutil.move(path, os.path.join(out_dir, out_name))


def download(resources_path: str) -> None:
    import os

    download_from_hub(out_dir=resources_path, out_name="txtlayer_classifier.json", repo_name="txtlayer_classifier", hub_name="model.json")

    download_from_hub(out_dir=resources_path,
                      out_name="scan_orientation_efficient_net_b0.pth",
                      repo_name="scan_orientation_efficient_net_b0",
                      hub_name="model.pth")

    download_from_hub(out_dir=resources_path, out_name="paragraph_classifier.zip", repo_name="paragraph_classifier", hub_name="model.zip")

    line_clf_resources_path = os.path.join(resources_path, "line_type_classifiers")
    for classifier_type in ("diploma", "law", "law_txt", "tz", "tz_txt"):
        download_from_hub(out_dir=line_clf_resources_path,
                          out_name=f"{classifier_type}_classifier.zip",
                          repo_name="line_type_classifiers",
                          hub_name=f"{classifier_type}.zip")

    fintoc_classifiers_resources_path = os.path.join(resources_path, "fintoc_classifiers")
    for language in ("en", "fr", "sp"):
        for classifier_type in ("target", "binary"):
            download_from_hub(out_dir=fintoc_classifiers_resources_path,
                              out_name=f"{classifier_type}_classifier_{language}.json",
                              repo_name="fintoc_classifiers",
                              hub_name=f"{classifier_type}_classifier_{language}_txt_layer.json")


if __name__ == "__main__":
    from dedoc.config import get_config

    resources_path = get_config()["resources_path"]
    download(resources_path)
