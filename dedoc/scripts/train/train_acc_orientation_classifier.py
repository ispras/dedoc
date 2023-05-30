import argparse
import os
from time import time
from typing import List

import numpy as np
import torch
from torch import nn
from torch import optim
from torch.utils.data import DataLoader

from dedoc.readers.scanned_reader.pdfscanned_reader.columns_orientation_classifier.columns_orientation_classifier \
    import ColumnsOrientationClassifier
from dedoc.readers.scanned_reader.pdfscanned_reader.columns_orientation_classifier.dataset_executor import \
    DataLoaderImageOrient


parser = argparse.ArgumentParser()
checkpoint_path_save = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                    "../../resources/efficient_net_b0_fixed.pth"))
checkpoint_path_load = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                    "../../../resources/efficient_net_b0_fixed_tmp.pth"))
checkpoint_path = "../../../resources"

parser.add_argument("-t", "--train", type=bool, help="run for train model", default=False)
parser.add_argument("-s", "--checkpoint_save", help="Path to checkpoint for save or load",
                    default=checkpoint_path_save)
parser.add_argument("-l", "--checkpoint_load", help="Path to checkpoint for load",
                    default=checkpoint_path_load)
parser.add_argument("-f", "--from_checkpoint", type=bool, help="run for train model", default=True)
parser.add_argument("-d", "--input_data_folder", help="Path to data with folders train or test",
                    default="/home/nasty/data/columns_orientation")

args = parser.parse_args()
BATCH_SIZE = 1
ON_GPU = False


def accuracy_step(data_executor: DataLoaderImageOrient, net_executor: ColumnsOrientationClassifier) -> None:
    """
    Function calculates accuracy for the trained model
    :param data_executor: Extractor Data from path
    :param net_executor: Classifier
    :return:
    """
    testloader = data_executor.load_dataset(
        csv_path=os.path.join(args.input_data_folder, 'test/labels.csv'),
        image_path=args.input_data_folder,
        batch_size=BATCH_SIZE
    )
    dataiter = iter(testloader)
    sample = dataiter.__next__()
    _, orientation, columns = sample['image'], sample['orientation'], sample['columns']

    print('GroundTruth: orientation {}, columns {}'.format(orientation, columns))

    calc_accuracy_by_classes(testloader, data_executor.classes, net_executor, batch_size=1)


def calc_accuracy_by_classes(testloader: DataLoader,
                             classes: List,
                             classifier: ColumnsOrientationClassifier,
                             batch_size: int = 1) -> None:
    """
    Function calculates accuracy ba each class
    :param testloader: DataLoader
    :param classes: List of name classes
    :param classifier: Classifier with predict method
    :param batch_size: size of batch
    :return:
    """
    class_correct = list(0. for i in range(len(classes)))
    class_total = list(0. for i in range(len(classes)))
    time_predict = 0
    cnt_predict = 0
    with torch.no_grad():
        for data in testloader:
            images, orientation, columns = data['image'], data['orientation'], data['columns']
            time_begin = time()

            if classifier.no_lines:
                for i in range(len(images)):
                    image_w_o_lines = classifier.get_features_no_lines((images[i].numpy().transpose(1, 2, 0) * 255).astype(np.uint8))
                    images[i] = torch.squeeze(image_w_o_lines, 0)

            outputs = classifier.net(images.float().to(classifier.device))
            time_predict += time() - time_begin
            cnt_predict += len(images)
            # first 2 classes mean columns number
            # last 4 classes mean orientation
            columns_out, orientation_out = outputs[:, :2], outputs[:, 2:]
            _, columns_predicted = torch.max(columns_out, 1)
            _, orientation_predicted = torch.max(orientation_out, 1)

            orientation_c = (orientation_predicted == orientation.to(classifier.device)).squeeze()
            columns_c = (columns_predicted == columns.to(classifier.device)).squeeze()

            for i in range(batch_size):
                orientation_i = orientation[i]
                columns_i = columns[i]
                orientation_bool_predict = orientation_c.item() if batch_size == 1 else orientation_c[i].item()
                columns_bool_predict = columns_c.item() if batch_size == 1 else columns_c[i].item()
                class_correct[2 + orientation_i] += orientation_bool_predict
                class_total[2 + orientation_i] += 1
                class_correct[columns_i] += orientation_bool_predict
                class_total[columns_i] += 1
                if not orientation_bool_predict or not columns_bool_predict:
                    print('{} predict as \norientation: {} \ncolumns: {}'.format(data['image_name'][i],
                                                                                 classes[2 + orientation_predicted[i]],
                                                                                 classes[columns_predicted[i]]))

    for i in range(len(classes)):
        print('Accuracy of %5s : %2d %%' % (
            classes[i], 100 * class_correct[i] / class_total[i] if class_total[i] != 0 else 0))
    print('=== AVG Time predict {}'.format(time_predict / cnt_predict))


def train_model(trainloader: DataLoader,
                checkpoint_path_save: str,
                classifier: ColumnsOrientationClassifier,
                epoch_cnt: int = 7,
                save_step: int = 500) -> None:
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
            inputs, orientation, columns = data['image'], data['orientation'], data['columns']

            if classifier.no_lines:
                for j in range(len(inputs)):
                    image_w_o_lines = classifier.get_features_no_lines((inputs[j].numpy().transpose(1, 2, 0) * 255).astype(np.uint8))
                    inputs[j] = torch.squeeze(image_w_o_lines, 0)

            # zero the parameter gradients
            optimizer.zero_grad()

            # forward + backward + optimize
            outputs = classifier.net(inputs.float().to(classifier.device))

            loss = criterion(outputs[:, :2],
                             columns.to(classifier.device)) + criterion(outputs[:, 2:],
                                                                        orientation.to(classifier.device))
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

            # print statistics
            if i % 100 == 99:
                print('[%d, %5d] loss: %.3f' %
                      (epoch + 1, i + 1, running_loss / 100))
                running_loss = 0.0

            # save checkpoint
            if i % save_step == save_step - 1:
                classifier.save_weights(checkpoint_path_save)

    classifier.save_weights(checkpoint_path_save)
    print('Finished Training')


def train_step(data_executor: DataLoaderImageOrient, classifier: ColumnsOrientationClassifier) -> None:
    # Part 1 - load datas
    trainloader = data_executor.load_dataset(
        csv_path=os.path.join(args.input_data_folder, 'train/labels.csv'),
        image_path=args.input_data_folder,
        batch_size=BATCH_SIZE
    )

    # get some random training images
    dataiter = iter(trainloader)
    sample = dataiter.__next__()
    _, orientation, columns = sample['image'], sample['orientation'], sample['columns']

    # print labels
    print(' '.join('%5s' % data_executor.classes[orientation[j]] for j in range(BATCH_SIZE)))
    print(' '.join('%5s' % data_executor.classes[columns[j]] for j in range(BATCH_SIZE)))

    # Part 2 - train model
    train_model(trainloader, args.checkpoint_save, classifier)


if __name__ == "__main__":
    from config import _config as config
    data_executor = DataLoaderImageOrient()
    net = ColumnsOrientationClassifier(on_gpu=True,
                                       checkpoint_path=checkpoint_path if not args.train else None,
                                       delete_lines=False,
                                       config=config)

    if args.train:
        train_step(data_executor, net)
    else:
        accuracy_step(data_executor, net)
