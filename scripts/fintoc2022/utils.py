import os
from collections import defaultdict
from typing import Dict, List, Tuple, Union

import pandas as pd


def create_json_result(data: pd.DataFrame, predictions: List[int]) -> Dict[str, List[Dict[str, Union[str, int]]]]:
    """
    Creates dictionary with TOCs for each document: {"doc_name": TOC}.
    TOC is a following list of dictionaries:
    [
        {
            "text": String, # text of the TOC item/entry
            "id": Int # identifier of the item/entry corresponding to its order in the TOC
            "depth": Int # hierarchical level of the item
            "page": Int # the (physical) page number where the item appears
        }
    ]
    """
    uid2line = {
        item[1].uid: {
            "text": item[1].line.strip() if isinstance(item[1].line, str) else "",
            "page": int(item[1].page_id + 1),
            "group": item[1].group
        } for item in data.iterrows()
    }
    result = defaultdict(list)
    assert data.shape[0] == len(predictions)
    for i, (line_uid, prediction) in enumerate(zip(data.uid, predictions)):
        line = uid2line[line_uid]
        if line["text"] == "" or prediction == -1:
            continue
        # TODO crop text lines containing colon
        result[line["group"]].append({"id": i, "depth": str(prediction), "text": line["text"], "page": line["page"]})
    return result


def get_values_from_csv(dir_path: str) -> Tuple[float, float]:
    td_name = "td_report.csv"
    toc_name = "toc_report.csv"
    td_df = pd.read_csv(os.path.join(dir_path, td_name), delimiter="\t")
    toc_df = pd.read_csv(os.path.join(dir_path, toc_name), delimiter="\t")
    f1 = td_df[td_df["Doc"] == "AVG"]["F1"].item()
    inex_f1 = toc_df[toc_df["Doc"] == " AVG "]["Inex08-F1"].item()
    return f1, inex_f1
