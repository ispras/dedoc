import argparse
import json
import os
import random
import time
import warnings
from collections import defaultdict
from itertools import chain
from typing import List, Tuple

import numpy as np
import torch
from PIL import Image
from joblib import Parallel, delayed
from numpy import mean
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from torch.nn import BCELoss
from torch.nn import Sequential, Linear, ReLU, Sigmoid, BatchNorm1d
from torch.nn.modules.loss import _Loss
from torch.optim import Adam, Optimizer
from torch.utils.data import Dataset, DataLoader
from torchvision.models import resnet18, ResNet
from torchvision.transforms import ToTensor
from tqdm import tqdm


from dedoc.data_structures.bbox import BBox
from dedoc.readers.scanned_reader.line_metadata_extractor.font_type_classifier import FontTypeClassifier
from dedoc.utils.image_utils import get_bbox_from_image

parser = argparse.ArgumentParser(add_help=True)
parser.add_argument("-l", "--labels_path", type=str, help="path to the json file with labeled bboxes", required=True)
parser.add_argument("-o", "--output_file", type=str, help="name of file with trained classifier", required=True)
args = parser.parse_args()

print("GO")

path = args.labels_path
path_out = args.output_file
seed = 42

torch.manual_seed(seed)
torch.cuda.manual_seed(seed)
np.random.seed(seed)
random.seed(seed)

device = "cuda" if torch.cuda.is_available() else "cpu"

print(device)


def get_model() -> ResNet:
    model = resnet18(pretrained=True)
    model.fc = Sequential(
        Linear(in_features=512, out_features=256),
        ReLU(),
        BatchNorm1d(256),
        Linear(256, out_features=2),
        Sigmoid(),
    )
    return model


class FontTypeDataset(Dataset):

    def __init__(self, path: str, items: List[dict]) -> None:
        super().__init__()
        self.labels_list = FontTypeClassifier.labels_list
        self.to_tensor = ToTensor()

        self.images = Parallel(n_jobs=8)(delayed(self._image2cropped)(path, i) for i in tqdm(items))
        self.images = [self.to_tensor(image) for image in self.images]
        labels = []
        for item in items:
            labels.append(self._encode_labels(item))
        self.labels = torch.tensor(labels).float()

    def _image2cropped(self, path: str, item: dict) -> Image:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            image_path = os.path.join(path, "original_documents", item["data"]["original_document_name"])
            image = Image.open(image_path)
            bbox_dict = item["data"]["bbox"]["bbox"]
            bbox = BBox(x_top_left=bbox_dict["x_upper_left"],
                        y_top_left=bbox_dict["y_upper_left"],
                        height=bbox_dict["height"],
                        width=bbox_dict["width"]
                        )
            return get_bbox_from_image(image=image, bbox=bbox)

    def _encode_labels(self, item: dict) -> List[int]:
        labels_item = []
        for label in self.labels_list:
            if label in item["labeled"]:
                labels_item.append(1)
            else:
                labels_item.append(0)
        assert len(labels_item) == len(self.labels_list)
        return labels_item

    def __getitem__(self, index: int) -> Tuple[Image, torch.Tensor]:
        return self.images[index], self.labels[index]

    def __len__(self) -> int:
        return len(self.labels)


def get_data(path: str) -> Tuple[List, List]:
    grouped_tasks = defaultdict(list)

    with open(os.path.join(path, "labeled_tasks.json")) as file:
        data = json.load(file)
        for item in data.values():
            image = item["data"]["original_document_name"]
            if os.path.isfile(os.path.join(path, "original_documents", image)):
                grouped_tasks[image].append(item)

    train_group, val_group = train_test_split(list(grouped_tasks.values()), train_size=0.8, )
    train_group = list(chain(*train_group))
    val_group = list(chain(*val_group))
    return train_group, val_group


def one_batch_train(model: torch.nn.Module,
                    data_loader: DataLoader,
                    optimizer: Optimizer,
                    criterion: _Loss) -> List[float]:
    epoch_losses = []
    for data_input, labels in data_loader:
        optimizer.zero_grad()

        data_input = data_input.to(device)
        labels = labels.float().to(device)
        predictions = model(data_input)
        loss = criterion(predictions, labels)
        loss.backward()
        optimizer.step()
        epoch_losses.append(float(loss))
    return epoch_losses


def one_batch_val(model: torch.nn.Module,
                  data_loader: DataLoader,
                  criterion: _Loss) -> Tuple[List[float], torch.Tensor, torch.Tensor]:
    epoch_losses = []
    predictions_all = []
    labels_all = []
    with torch.no_grad():
        for data_input, labels in data_loader:
            data_input = data_input.to(device)
            labels = labels.float().to(device)
            predictions = model(data_input)
            loss = criterion(predictions, labels)
            epoch_losses.append(float(loss))
            predictions_all.append(predictions.cpu())
            labels_all.append(labels.cpu())
    return epoch_losses, torch.cat(predictions_all, dim=0), torch.cat(labels_all, dim=0)


def train_model(model: torch.nn.Module,
                criterion: _Loss,
                optimizer: Optimizer,
                dataloaders: DataLoader,
                epoch_start: int = 0,
                epoch_end: int = 15) -> None:
    res = []
    for epoch in range(epoch_start, epoch_end):
        epoch_losses_train = one_batch_train(model, dataloaders["train"], optimizer, criterion)
        epoch_losses_val, predictions_all, labels_all = one_batch_val(model, dataloaders["val"], criterion)

        roc_bold = roc_auc_score(y_score=predictions_all[:, 0], y_true=labels_all[:, 0])
        roc_other = roc_auc_score(y_score=predictions_all[:, 1], y_true=labels_all[:, 1])
        epoch_losses_train = mean(epoch_losses_train)
        epoch_losses_val = mean(epoch_losses_val)
        res.append((epoch, epoch_losses_train, epoch_losses_val, roc_bold, roc_other))
        report_template = "{:011d} epoch={:06d}  train {:01.4f}  val {:01.4f}  bold {:01.4f} other {:01.4f}"
        print(report_template.format(int(time.time()), *res[-1]))
    return


def main() -> None:
    train_group, val_group = get_data(path)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        dataset_val = FontTypeDataset(path, val_group)
        dataset_train = FontTypeDataset(path, train_group)

    dataloaders = {
        "val": DataLoader(dataset_val, batch_size=16, drop_last=True),
        "train": DataLoader(dataset_train, batch_size=16, shuffle=True, drop_last=True)
    }
    print("GET DATA")

    font_classifier = get_model()
    print("GET MODEL")

    font_classifier.requires_grad_(False)
    font_classifier.fc.requires_grad_(True)
    font_classifier = font_classifier.to(device)
    optimizer = Adam(params=font_classifier.fc.parameters(), lr=1e-5)
    train_model(model=font_classifier,
                criterion=BCELoss(),
                dataloaders=dataloaders,
                optimizer=optimizer,
                epoch_start=0,
                epoch_end=15)

    font_classifier.requires_grad_(True)
    optimizer = Adam(params=font_classifier.parameters(), lr=1e-4)
    train_model(model=font_classifier,
                dataloaders=dataloaders,
                criterion=BCELoss(),
                optimizer=optimizer,
                epoch_start=15,
                epoch_end=35)
    with open(path_out, "wb") as file_out:
        font_classifier = font_classifier.cpu()
        torch.save(obj=font_classifier, f=file_out)


if __name__ == '__main__':
    main()
