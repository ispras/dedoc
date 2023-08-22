from typing import Optional

import torch
from torch import nn
from torchvision import models


class ClassificationModelTorch(nn.Module):
    """
    Class detects EfficientNet B0 model
    """
    def __init__(self, model_path: Optional[str], num_classes: int = 6) -> None:
        """
        first 2 classes mean columns number
        last 4 classes mean orientation
        """
        super(ClassificationModelTorch, self).__init__()
        self.efficientnet_b0 = models.efficientnet_b0(pretrained=model_path is None)
        self.efficientnet_b0.classifier[1] = nn.Linear(in_features=1280, out_features=num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.efficientnet_b0(x)
        return out
