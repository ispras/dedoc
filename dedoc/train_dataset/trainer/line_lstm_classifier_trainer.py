import hashlib
import json
import os
import logging
from typing import Callable, List, Iterator, Optional, Dict, Any
from collections import OrderedDict
from torch.autograd import Variable
import torch
from torch import nn
import time
import numpy as np
from sklearn.model_selection import KFold
from torch.nn.modules.loss import CrossEntropyLoss
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
from torch.optim.optimizer import Optimizer
from tqdm import tqdm
from statistics import mean
import pandas as pd

from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.train_dataset.data_structures.line_with_label import LineWithLabel
from dedoc.train_dataset.trainer.data_loader import DataLoader, LineEpsDataSet
from dedoc.utils.utils import flatten


class Attention(nn.Module):
    # source https://www.kaggle.com/bminixhofer/deterministic-neural-networks-using-pytorch
    def __init__(self, feature_dim: int, step_dim: int, bias: bool = True, **kwargs: Dict[str, Any]) -> None:
        super(Attention, self).__init__(**kwargs)

        self.supports_masking = True
        self.bias = bias
        self.feature_dim = feature_dim
        self.step_dim = step_dim
        self.features_dim = 0

        weight = torch.zeros(feature_dim, 1)
        nn.init.xavier_uniform_(weight)
        self.weight = nn.Parameter(weight)

        if bias:
            self.b = nn.Parameter(torch.zeros(step_dim))

    def forward(self, x: torch.Tensor, mask: torch.Tensor = None) -> torch.Tensor:
        feature_dim = self.feature_dim
        step_dim = self.step_dim

        eij = torch.mm(
            x.contiguous().view(-1, feature_dim),
            self.weight
        ).view(-1, step_dim)

        if self.bias:
            eij = eij + self.b

        eij = torch.tanh(eij)
        a = torch.exp(eij)
        if mask is not None:
            a = a * mask

        a = a / torch.sum(a, 1, keepdim=True) + 1e-10

        weighted_input = x * torch.unsqueeze(a, -1)
        return torch.sum(weighted_input, 1)


class LSTM(nn.Module):

    # define all the layers used in model
    def __init__(self, input_dim: int, hidden_dim: int, hidden_dim_2: int, num_classes: int, lstm_layers: int,
                 bidirectional: bool, dropout: float,
                 device: torch.device, maxlen: int = 7, with_attention: bool = True) -> None:
        super().__init__()
        # self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx = pad_index)
        self.input_dim = input_dim  # The number of expected features in the input `x`
        # hidden_dim - The number of features in the hidden state `h`
        # lstm_layers - Number of recurrent layers. E.g., setting ``num_layers=2``
        #             would mean stacking two LSTMs together to form a `stacked LSTM`,
        #             with the second LSTM taking in outputs of the first LSTM and
        #             computing the final results. Default: 1
        # batch_first: If ``True``, then the input and output tensors are provided
        #             as (batch, seq, feature).
        # with_attention - use or not Attention NN
        self.lstm = nn.LSTM(input_size=input_dim,
                            hidden_size=hidden_dim,
                            num_layers=lstm_layers,
                            bidirectional=bidirectional,
                            batch_first=True)
        self.lstm_attention = Attention(hidden_dim * 2, maxlen).to(device)
        num_directions = 2 if bidirectional else 1
        self.fc1 = nn.Linear(hidden_dim * num_directions, hidden_dim_2)
        self.fc2 = nn.Linear(hidden_dim_2, num_classes)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.lstm_layers = lstm_layers
        self.num_directions = num_directions
        self.lstm_units = hidden_dim
        self.with_attention = with_attention

    def init_hidden(self, batch_size: int, device: torch.device) -> [torch.Tensor, torch.Tensor]:
        h, c = (Variable(torch.zeros(self.lstm_layers * self.num_directions, batch_size, self.lstm_units)).to(device),
                Variable(torch.zeros(self.lstm_layers * self.num_directions, batch_size, self.lstm_units)).to(device))
        return h, c

    def forward(self, input_tensor: List[torch.Tensor], batch_lengths: torch.Tensor, device: torch.device) \
            -> torch.Tensor:
        batch_size = len(input_tensor)
        h_0, c_0 = self.init_hidden(batch_size, device)
        packed_embedded = pack_padded_sequence(input_tensor, batch_lengths, batch_first=True)
        output, _ = self.lstm(packed_embedded, (h_0, c_0))
        output_unpacked, output_lengths = pad_packed_sequence(output, batch_first=True)

        if self.with_attention:
            '''att_mask = torch.tensor(np.array([0.3, 0.3, 0.5, 1.0, 0.5, 0.3, 0.3]),
                  dtype=torch.float32, device=torch.device("cuda:0"))'''
            att_mask = None
            res_nn = self.lstm_attention(output_unpacked, mask=att_mask)
        else:
            res_nn = output_unpacked[:, -1, :]

        rel = self.relu(res_nn)
        dense1 = self.fc1(rel)
        drop = self.dropout(dense1)
        preds = self.fc2(drop)

        return preds


class LSTMTrainer:
    lr = 1e-4
    batch_size = 16
    hidden_dim2 = 128
    num_layers = 2  # LSTM layers
    bi_directional = True
    num_epochs = 5
    n_splits = 10

    def __init__(self,
                 tmp_dir: str,
                 data_url: str,
                 path_out: str,
                 logger: logging.Logger,
                 config: dict,
                 feature_extractor: AbstractFeatureExtractor,
                 label_transformer: Callable[[str], str],
                 class_dict: dict,
                 on_gpu: bool,
                 path_scores: str) -> None:
        self.data_url = data_url
        self.path_out = path_out
        self.logger = logger
        self.tmp_dir = "/tmp" if tmp_dir is None else tmp_dir
        url_hash = hashlib.md5(self.data_url.encode()).hexdigest()
        self.dataset_dir = os.path.join(self.tmp_dir, "dataset_{}".format(url_hash))
        self.data_loader = DataLoader(dataset_dir=self.dataset_dir,
                                      label_transformer=label_transformer,
                                      logger=logger,
                                      data_url=data_url,
                                      config=config)
        self.path_scores = path_scores
        self.feature_extractor = feature_extractor
        self.class_dict = class_dict
        self.num_classes = len(class_dict)
        if torch.cuda.is_available() and on_gpu:
            print("Device is cuda")  # noqa
            self.device = torch.device("cuda:0")
        else:
            print("Device is cpu")  # noqa
            self.device = torch.device("cpu")

    def __get_labels(self, data: List[List[LineWithLabel]]) -> List[str]:
        result = [line.label for line in flatten(data)]
        return result

    def get_features_with_separing(self, data: List[List[LineWithLabel]]) \
            -> [pd.DataFrame, pd.DataFrame, List[str], List[str]]:
        features = self.feature_extractor.fit_transform(data)
        n = features.shape[0] // 10
        features_train, features_test = features[n:], features[:n]
        labels = self.__get_labels(data)
        labels_train, labels_test = labels[n:], labels[:n]
        self.logger.info("data train shape {}".format(features_train.shape))
        self.logger.info("data test shape {}".format(features_test.shape))

        return features_train, features_test, labels_train, labels_test

    def get_features(self, data: List[List[LineWithLabel]]) -> [pd.DataFrame, List[str]]:
        features = self.feature_extractor.fit_transform(data)
        labels = self.__get_labels(data)
        return features, labels

    def training_and_evaluation_process(self, lstm_model: nn.Module, optimizer: Optimizer, criteria: CrossEntropyLoss,
                                        features_train: pd.DataFrame, labels_train: List[str],
                                        features_test: pd.DataFrame, labels_test: List[str],
                                        file_log: Optional,
                                        with_save: bool = True,
                                        with_eval: bool = True) -> [float, float, float]:
        # train and evaluation
        best_loss = 100000.0
        res_loss, res_acc = 0.0, 0.0
        time_epoch = 0.0

        for epoch in range(self.num_epochs):
            print("\n\t Epoch: {}".format(epoch))  # noqa
            # The Dataloader class handles all the shuffles for you

            loader_iter = iter(LineEpsDataSet(features_train, labels_train, self.class_dict))
            time_begin = time.time()
            train_loss, train_acc = self.train(lstm_model, loader_iter, len(labels_train),
                                               optimizer, criteria, batch_size=self.batch_size)
            time_epoch += time.time() - time_begin
            print("\n\t \x1b\33[33mTrain: epoch: {}| Train loss: {} | Train acc: {}\x1b[0m".format(epoch, train_loss,  # noqa
                                                                                                   train_acc))
            if file_log:
                file_log.write("\t Train: epoch: {}| Train loss: {} | Train acc: {}\n".format(epoch, epoch, train_loss))

            # Evaluation
            if with_eval:
                loader_iter = iter(LineEpsDataSet(features_test, labels_test, self.class_dict))
                test_loss, test_acc = self.evaluate(lstm_model, loader_iter, len(labels_test), criteria,
                                                    batch_size=self.batch_size)
                print("\n\t \x1b\33[92mEvaluation: Test loss: {} | Test acc: {}\x1b[0m".format(test_loss, test_acc))  # noqa
                if file_log:
                    file_log.write(
                        "\t Eval: epoch: {}| Test loss: {} | Test acc: {}\n".format(epoch, test_loss, test_acc))
                curr_loss = test_loss
                res_acc += test_acc
                res_loss += test_loss
            else:
                curr_loss = train_loss
                res_acc += train_acc
                res_loss += train_loss

            # Save the best model
            if with_save and curr_loss < best_loss:
                best_loss = curr_loss
                torch.save(lstm_model.state_dict(), self.path_out)
                print("Model has been saved into {}".format(self.path_out))  # noqa

        return res_loss / self.num_epochs, res_acc / self.num_epochs, time_epoch / self.num_epochs

    def fit(self, with_cross_val: bool = True) -> None:
        data = self.data_loader.get_data(no_cache=False)
        # optimization algorithm

        criteria = nn.CrossEntropyLoss()
        lstm_drop_out = 0.1
        lstm_hidden_dim = 128
        lstm_layers = 2

        scores_dict = OrderedDict()

        data = np.array(data, dtype=object)

        if with_cross_val:
            print("\n\x1b\33[95m---------Evaluation process (cross-validation) starts-------\x1b[0m\n")  # noqa
            kf = KFold(n_splits=self.n_splits)
            scores = []
            epoch_time = []
            logfile_kfold_tmp = open("/tmp/lstm_kfold.txt", "w")
            for iteration, (train_index, val_index) in tqdm(enumerate(kf.split(data)), total=self.n_splits):
                data_train, data_val = data[train_index].tolist(), data[val_index].tolist()
                features_train, labels_train = self.get_features(data_train)
                features_test, labels_test = self.get_features(data_val)

                lstm_model = LSTM(input_dim=features_train.shape[1], hidden_dim=features_train.shape[1],
                                  hidden_dim_2=lstm_hidden_dim, num_classes=self.num_classes, lstm_layers=lstm_layers,
                                  bidirectional=self.bi_directional, dropout=lstm_drop_out, device=self.device) \
                    .to(self.device)
                optimizer = torch.optim.Adam(lstm_model.parameters(), lr=self.lr)
                logfile_kfold_tmp.write("\t KFold iter = {}\n".format(iteration))
                loss, acc, epoch_sec = self.training_and_evaluation_process(lstm_model, optimizer, criteria,
                                                                            features_train, labels_train, features_test,
                                                                            labels_test,
                                                                            file_log=logfile_kfold_tmp,
                                                                            with_save=False, with_eval=True)
                logfile_kfold_tmp.write("\t time_epoch_(sec)={}\n".format(epoch_sec))
                logfile_kfold_tmp.flush()
                scores.append(acc)
                epoch_time.append(epoch_sec)

            scores_dict["mean"] = mean(scores)
            scores_dict["mean_epoch_sec"] = mean(epoch_time)
            scores_dict["scores"] = scores
            logfile_kfold_tmp.close()

        print("\n\x1b\33[95m-------------------Train process starts------------------\x1b[0m\n")  # noqa
        features_train, labels_train = self.get_features(data)
        lstm_model = LSTM(input_dim=features_train.shape[1], hidden_dim=features_train.shape[1],
                          hidden_dim_2=lstm_hidden_dim, num_classes=self.num_classes, lstm_layers=lstm_layers,
                          bidirectional=self.bi_directional, dropout=lstm_drop_out, device=self.device).to(self.device)
        optimizer = torch.optim.Adam(lstm_model.parameters(), lr=self.lr)
        loss, acc, _ = self.training_and_evaluation_process(lstm_model, optimizer, criteria,
                                                            features_train, labels_train, features_test=None,
                                                            labels_test=None,
                                                            file_log=None,
                                                            with_save=True, with_eval=False)
        print("\x1b\33[92mFinal Accuracy from training = {}\x1b[0m".format(acc))  # noqa
        scores_dict["final_accuracy"] = acc

        if self.path_scores is not None:
            self.logger.info("Save scores in {}".format(self.path_scores))
            os.makedirs(os.path.basename(self.path_scores), exist_ok=True)
            with open(self.path_scores, "w") as file:
                json.dump(obj=scores_dict, fp=file, indent=4)

    def accuracy(self, probs: torch.Tensor, target: List[int]) -> float:
        winners = probs.argmax(dim=1)

        corrects = [int(winners[i] == target[i]) for i in range(len(target))]
        accuracy = sum(corrects) / float(len(target))

        return accuracy

    def _evaluate_batch_num(self, cnt_data: int, batch_size: int) -> [int, int]:
        cnt_batch = cnt_data // batch_size
        rest = cnt_data % batch_size

        if rest > 0:
            cnt_batch += 1
        return cnt_batch, rest

    def _get_batch_data(self, curr_batch_size: int, iterator: Iterator) -> [List[Iterator], List[int], List[str]]:
        batch_features, batch_lens, labels = [], [], []
        for num in range(curr_batch_size):
            curr = next(iterator)
            batch_features.append(curr[0])
            batch_lens.append(curr[2])
            labels.append(curr[1])

        return batch_features, batch_lens, labels

    def train(self, model: nn.Module, iterator: Iterator, cnt_data: int, optimizer: Optimizer,
              criteria: CrossEntropyLoss, batch_size: int) -> [float, float]:
        epoch_loss = 0
        epoch_acc = 0
        cnt = 0
        cnt_batch, rest_batch = self._evaluate_batch_num(cnt_data, batch_size)
        log_per_cnt = cnt_batch // 10
        model.train()

        for batch_num in range(cnt_batch):
            optimizer.zero_grad()
            curr_batch_size = rest_batch if batch_num == cnt_batch - 1 and rest_batch < batch_size else batch_size
            batch_fatures, batch_lens, labels = self._get_batch_data(curr_batch_size, iterator)
            if len(labels) == 0:
                continue
            predictions = model(torch.tensor(batch_fatures, dtype=torch.float32).to(self.device),
                                torch.tensor(batch_lens).to(self.device),
                                self.device)
            loss = criteria(predictions, torch.tensor(labels).to(self.device))
            accuracy = self.accuracy(predictions, labels)

            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            epoch_acc += accuracy
            cnt += 1
            if log_per_cnt != 0 and batch_num % log_per_cnt == 0:
                print("\t\tbatch_num: {}, loss={}, acc={}".format(batch_num, epoch_loss / cnt, epoch_acc / cnt))  # noqa

        return epoch_loss / cnt, epoch_acc / cnt

    def evaluate(self, model: nn.Module, iterator: Iterator, cnt_data: int, criteria: CrossEntropyLoss,
                 batch_size: int) -> [float, float]:
        epoch_loss = 0
        epoch_acc = 0
        cnt = 0
        cnt_batch, rest_batch = self._evaluate_batch_num(cnt_data, batch_size)

        model.eval()
        with torch.no_grad():
            for batch_num in range(cnt_batch):
                curr_batch_size = rest_batch if batch_num == cnt_batch - 1 and rest_batch > 0 else batch_size
                batch_fatures, batch_lens, labels = self._get_batch_data(curr_batch_size, iterator)

                predictions = model(torch.tensor(batch_fatures, dtype=torch.float32).to(self.device),
                                    torch.tensor(batch_lens).to(self.device),
                                    self.device)

                loss = criteria(predictions, torch.tensor(labels).to(self.device))
                accuracy = self.accuracy(predictions, labels)

                epoch_loss += loss.item()
                epoch_acc += accuracy
                cnt += 1

        return epoch_loss / cnt, epoch_acc / cnt
