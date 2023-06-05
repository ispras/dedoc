import logging
import warnings
from typing import Tuple, Optional
import numpy as np
import torch
from PIL import Image
from torchvision import transforms
from torchvision.transforms.functional import resize
import cv2
from os import path

from dedoc.download_models import download_from_hub
from dedoc.readers.pdf_reader.pdf_image_reader.columns_orientation_classifier.model import ClassificationModelTorch
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_utils.img_processing import \
    __detect_horizontal_and_vertical_lines as detect_horizontal_and_vertical_lines
from dedoc.config import get_config


class ColumnsOrientationClassifier(object):
    """
    Class Classifier for work with Orientation Network. This class set device,
    preprocessing (transform) input data, weights of model
    """

    _nets = {}

    def __init__(self, on_gpu: bool, checkpoint_path: Optional[str], delete_lines: bool, *, config: dict) -> None:
        self.logger = config.get("logger", logging.getLogger())
        self._set_device(on_gpu)
        self._set_transform_image()
        self.checkpoint_path = path.abspath(checkpoint_path)
        self.classes = [1, 2, 0, 90, 180, 270]
        self.no_lines = delete_lines

    @property
    def net(self) -> ClassificationModelTorch:
        # lazy loading and net sharing, comrade
        if self.checkpoint_path not in self._nets:
            if self.checkpoint_path is not None:
                net = ClassificationModelTorch(path.join(self.checkpoint_path, "scan_orientation_efficient_net_b0.pth"))
                self._load_weights(net)
            else:
                net = ClassificationModelTorch(None)
            net.to(self.device)
            self._nets[self.checkpoint_path] = net
        return self._nets[self.checkpoint_path]

    @staticmethod
    def my_resize(image: Image) -> Image:
        max_dim = max(image.size)
        image1 = resize(image, size=[round(image.size[1] / max_dim * 1200), round(image.size[0] / max_dim * 1200)])
        white_image = Image.new(size=(1200, 1200), color=(255, 255, 255), mode="RGB")
        white_image.paste(image1)
        return white_image

    def _set_device(self, on_gpu: bool) -> None:
        """
        Set device configuration
        """
        if on_gpu and torch.cuda.is_available():
            self.device = torch.device("cuda:0")
            self.location = lambda storage, loc: storage.cuda()
        else:
            self.device = torch.device("cpu")
            self.location = 'cpu'

    def _load_weights(self, net: ClassificationModelTorch) -> None:
        path_checkpoint = path.join(self.checkpoint_path, "scan_orientation_efficient_net_b0.pth")
        if not path.isfile(path_checkpoint):
            download_from_hub(out_dir=self.checkpoint_path,
                              out_name="scan_orientation_efficient_net_b0.pth",
                              repo_name="scan_orientation_efficient_net_b0",
                              hub_name="model.pth")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            net.load_state_dict(torch.load(path_checkpoint, map_location=self.location))
            self.logger.info('Weights were loaded from {}'.format(path_checkpoint))

    def save_weights(self, path_checkpoint: str) -> None:
        torch.save(self.net.state_dict(), path_checkpoint)
        self.logger.info('Weights were saved into {}'.format(path_checkpoint))

    def _set_transform_image(self) -> None:
        """
        Set configuration preprocessing for input image
        """
        self.transform = transforms.Compose([
            transforms.Lambda(self.my_resize),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])

    def get_features_no_lines(self, image: np.array) -> torch.Tensor:
        """
        Get features for image without horizontal and vertical lines
        """
        image = self.transform(Image.fromarray(np.uint8(image)))
        item_np = (image.numpy().transpose(1, 2, 0) * 255).astype(np.uint8)
        img = cv2.cvtColor(item_np, cv2.COLOR_BGR2GRAY)
        (thresh, img_bin) = cv2.threshold(img, 245, 255, cv2.THRESH_BINARY)
        img_bin = 255 - img_bin
        img_lines_bin = detect_horizontal_and_vertical_lines(img_bin, get_config(), "orientation")
        img_final = 255 - img * img_lines_bin
        backtorgb = cv2.cvtColor(img_final, cv2.COLOR_GRAY2RGB).transpose(2, 0, 1) / 255.
        image = torch.tensor(backtorgb).unsqueeze(0).float().to(self.device)
        return image

    def get_features(self, image: np.array) -> torch.Tensor:
        """
        Get features for image with horizontal and vertical lines
        """
        image = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(np.uint8(image)).convert('RGB')
        tensor_image = self.transform(pil_image).unsqueeze(0).float().to(self.device)
        return tensor_image

    def predict(self, image: np.ndarray) -> Tuple[int, int]:
        """
        Predict class orientation of input image
        """
        self.net.eval()
        with torch.no_grad():

            if self.no_lines:
                tensor_image = self.get_features_no_lines(image)
            else:
                tensor_image = self.get_features(image)
            outputs = self.net(tensor_image)
            # first 2 classes mean columns number
            # last 4 classes mean orientation
            columns_out, orientation_out = outputs[:, :2], outputs[:, 2:]

            _, columns_predicted = torch.max(columns_out, 1)
            _, orientation_predicted = torch.max(orientation_out, 1)

        columns, orientation = int(columns_predicted[0]), int(orientation_predicted[0])
        columns_predict = self.classes[columns]
        angle_predict = self.classes[2 + orientation]
        return columns_predict, angle_predict
