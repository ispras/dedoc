import os
from typing import Callable, Dict

import pandas as pd
import torch
from skimage import io
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from dedoc.readers.pdf_reader.pdf_image_reader.columns_orientation_classifier.transforms import TransformWithLabels


class DatasetImageOrient(object):
    """
    Class to loading dataset from csv_file and root_dir
    """

    def __init__(self, csv_file: str, root_dir: str, transform: Callable = None) -> None:
        """
        Args:
            csv_file (string): Path to the csv file with annotations.
            root_dir (string): Directory with all the images.
            transform (callable, optional): Optional transform to be applied on a sample.
        """
        self.label_loader = pd.read_csv(csv_file)
        self.root_dir = root_dir
        self.transform = transform

    def __len__(self) -> int:
        return len(self.label_loader)

    def __getitem__(self, idx: torch.Tensor) -> Dict[str, str]:
        if torch.is_tensor(idx):
            idx = idx.tolist()

        img_name = os.path.join(self.root_dir, self.label_loader.iloc[idx, 0])
        image = io.imread(img_name)
        label = self.label_loader.iloc[idx, 1:]
        orientation = label["orientation"]
        orientation = orientation.astype("int")
        columns = label["columns"]
        columns = columns.astype("int")
        sample = {"image": image, "orientation": orientation, "columns": columns, "image_name": img_name}

        if self.transform:
            sample = self.transform(sample)

        return sample


class DataLoaderImageOrient(Dataset):
    """
    Class create torch DataLoader
    """
    def __init__(self) -> None:
        self.transform = transforms.Compose([TransformWithLabels()])
        self.classes = ("1", "2", "0", "90", "180", "270")

    def load_dataset(self, csv_path: str, image_path: str, batch_size: int = 4) -> DataLoader:
        trainset = DatasetImageOrient(csv_file=csv_path, root_dir=image_path, transform=self.transform)
        trainloader = DataLoader(trainset, batch_size=batch_size, shuffle=True, num_workers=2)

        return trainloader
