import argparse
import os
from time import time
from typing import List

import numpy as np
import torch
from sklearn.metrics import precision_recall_fscore_support
from texttable import Texttable
from torch import nn
from torch import optim
from torch.utils.data import DataLoader
from tqdm import tqdm

from dedoc.config import get_config
from dedoc.readers.pdf_reader.pdf_image_reader.columns_orientation_classifier.columns_orientation_classifier import ColumnsOrientationClassifier
from dedoc.readers.pdf_reader.pdf_image_reader.columns_orientation_classifier.dataset_executor import DataLoaderImageOrient

parser = argparse.ArgumentParser()
checkpoint_path_save = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "efficient_net_b0_fixed.pth"))
checkpoint_path_load = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "efficient_net_b0_fixed.pth"))
checkpoint_path = "../../resources"
output_dir = os.path.abspath(os.path.join(checkpoint_path, "benchmarks"))

parser.add_argument("-t", "--train", type=bool, help="run for train model", default=False)
parser.add_argument("-s", "--checkpoint_save", help="Path to checkpoint for save or load", default=checkpoint_path_save)
parser.add_argument("-l", "--checkpoint_load", help="Path to checkpoint for load", default=checkpoint_path_load)
parser.add_argument("-f", "--from_checkpoint", type=bool, help="run for train model", default=True)
parser.add_argument("-d", "--input_data_folder", help="Path to data with folders train or test",
                    default="/home/ox/work/datasets/generate_dataset_orient_cls/generate_dataset_orient_classifier")

args = parser.parse_args()
BATCH_SIZE = 1
ON_GPU = True

"""
Input data are available from our confluence (closed data).
First, you need generate full train/test data (all orientation of src documents)  using scripts/gen_dataset.py
Then, you can use this script.
"""


def evaluation_step(data_executor: DataLoaderImageOrient, net_executor: ColumnsOrientationClassifier) -> None:
    """
    Function calculates accuracy for the trained model
    :param data_executor: Extractor Data from path
    :param net_executor: Classifier
    :return:
    """
    net_executor.net.eval()
    testloader = data_executor.load_dataset(
        csv_path=os.path.join(args.input_data_folder, "test/labels.csv"),
        image_path=args.input_data_folder,
        batch_size=BATCH_SIZE
    )
    dataiter = iter(testloader)
    sample = dataiter.__next__()
    _, orientation, columns = sample["image"], sample["orientation"], sample["columns"]

    print(f"GroundTruth: orientation {orientation}, columns {columns}")

    evaluation(testloader, data_executor.classes, net_executor)


def print_metrics(precision: np.array, recall: np.array, f1: np.array, cnt: np.array, avg: np.array, classes: List[str]) -> Texttable:
    table = Texttable()

    table.header(["Class", "Precision", "Recall", "F1", "Count"])
    for i, name_class in enumerate(classes):
        table.add_row([name_class, precision[i], recall[i], f1[i], cnt[i]])

    table.add_row(["AVG", avg[0], avg[1], avg[2], "None"])

    return table


def evaluation(testloader: DataLoader, classes: List, classifier: ColumnsOrientationClassifier) -> None:
    """
    Function calculates accuracy ba each class
    :param testloader: DataLoader
    :param classes: List of name classes
    :param classifier: Classifier with predict method
    :param batch_size: size of batch
    :return:
    """
    orientation_pred, orientation_true = [], []
    column_pred, column_true = [], []

    time_predict = 0
    cnt_predict = 0
    with torch.no_grad():
        for data in tqdm(testloader):
            images, orientation, columns = data["image"], data["orientation"], data["columns"]

            time_begin = time()
            outputs = classifier.net(images.float().to(classifier.device))
            time_predict += time() - time_begin
            cnt_predict += len(images)

            # first 2 classes mean columns number
            # last 4 classes mean orientation
            columns_out, orientation_out = outputs[:, :2], outputs[:, 2:]
            _, columns_predicted = torch.max(columns_out, 1)
            _, orientation_predicted = torch.max(orientation_out, 1)

            orientation_pred.append(classes[2 + orientation_predicted.squeeze().item()])
            orientation_true.append(classes[2 + orientation.to(classifier.device).squeeze().item()])

            column_pred.append(classes[columns_predicted.squeeze().item()])
            column_true.append(classes[columns.to(classifier.device).squeeze().item()])

    with open(os.path.join(output_dir, "orient_classifier_scores.txt"), "w") as benchmark_file:
        orient_metrics = precision_recall_fscore_support(orientation_true, orientation_pred, average=None, labels=classes[2:])
        orient_avg = precision_recall_fscore_support(orientation_true, orientation_pred, average="weighted")
        table = print_metrics(*orient_metrics, orient_avg, classes[2:])
        print(table.draw())
        benchmark_file.write("\nOrientation predictions:\n")
        benchmark_file.write(table.draw())

        column_metrics = precision_recall_fscore_support(column_true, column_pred, average=None, labels=classes[:2])
        column_avg = precision_recall_fscore_support(column_true, column_pred, average="weighted")
        table = print_metrics(*column_metrics, column_avg, classes[:2])
        print(table.draw())
        benchmark_file.write("\nColumn predictions:\n")
        benchmark_file.write(table.draw())

    print(f"=== AVG Time predict {time_predict / cnt_predict}")


def train_model(trainloader: DataLoader, checkpoint_path_save: str, classifier: ColumnsOrientationClassifier, epoch_cnt: int = 7, save_step: int = 500) -> None:
    """
    Function for train orientation classifier
    :param trainloader: DataLoader
    :param checkpoint_path_save: path where weights are saved
    :param classifier: Classifier Model
    :param epoch_cnt: count of train epoch
    :param save_step: number step for save checkpoint
    :return:
    """
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(classifier.net.parameters(), lr=0.001, momentum=0.9)

    for epoch in range(epoch_cnt):  # loop over the dataset multiple times
        running_loss = 0.0
        for i, data in enumerate(trainloader, 0):
            # get the inputs; data is a list of [inputs, labels]
            inputs, orientation, columns = data["image"], data["orientation"], data["columns"]

            # zero the parameter gradients
            optimizer.zero_grad()

            # forward + backward + optimize
            outputs = classifier.net(inputs.float().to(classifier.device))

            loss = criterion(outputs[:, :2], columns.to(classifier.device)) + criterion(outputs[:, 2:], orientation.to(classifier.device))
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

            # print statistics
            if i % 100 == 99:
                print(f"[{epoch + 1}, {i + 1:5d}] loss: {running_loss / 100:.3f}")
                running_loss = 0.0

            # save checkpoint
            if i % save_step == save_step - 1:
                classifier.save_weights(checkpoint_path_save)

    classifier.save_weights(checkpoint_path_save)
    print("Finished Training")


def train_step(data_executor: DataLoaderImageOrient, classifier: ColumnsOrientationClassifier) -> None:
    classifier.net.train()
    # Part 1 - load datas
    trainloader = data_executor.load_dataset(
        csv_path=os.path.join(args.input_data_folder, "train/labels.csv"),
        image_path=args.input_data_folder,
        batch_size=BATCH_SIZE
    )

    # get some random training images
    dataiter = iter(trainloader)
    sample = dataiter.__next__()
    _, orientation, columns = sample["image"], sample["orientation"], sample["columns"]

    # print labels
    print(" ".join(f"{data_executor.classes[orientation[j]]:5s}" for j in range(BATCH_SIZE)))
    print(" ".join(f"{data_executor.classes[columns[j]]:5s}" for j in range(BATCH_SIZE)))

    # Part 2 - train model
    train_model(trainloader, args.checkpoint_save, classifier)


if __name__ == "__main__":
    config = get_config()
    data_executor = DataLoaderImageOrient()
    net = ColumnsOrientationClassifier(on_gpu=True, checkpoint_path=checkpoint_path if not args.train else "", config=config)
    if args.train:
        train_step(data_executor, net)
    else:
        evaluation_step(data_executor, net)
