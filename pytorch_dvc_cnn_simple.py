# coding: utf-8

# Dogs-vs-cats classification with CNNs

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from datetime import datetime

from pytorch_dvc_cnn import get_train_loader_hdf5, get_validation_loader_hdf5, get_test_loader_hdf5
from pytorch_dvc_cnn import device, train, evaluate, get_tensorboard

model_file = 'dvc_simple_cnn.pt'


# Option 1: Train a small CNN from scratch

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, (3, 3))
        self.pool1 = nn.MaxPool2d((2, 2))
        self.conv2 = nn.Conv2d(32, 32, (3, 3))
        self.pool2 = nn.MaxPool2d((2, 2))
        self.conv3 = nn.Conv2d(32, 64, (3, 3))
        self.pool3 = nn.MaxPool2d((2, 2))
        self.fc1 = nn.Linear(17*17*64, 64)
        self.fc1_drop = nn.Dropout(0.5)
        self.fc2 = nn.Linear(64, 1)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = self.pool1(x)
        x = F.relu(self.conv2(x))
        x = self.pool2(x)
        x = F.relu(self.conv3(x))
        x = self.pool3(x)

        # "flatten" 2D to 1D
        x = x.view(-1, 17*17*64)
        x = F.relu(self.fc1(x))
        x = self.fc1_drop(x)
        return torch.sigmoid(self.fc2(x))


def train_main():
    model = Net().to(device)
    optimizer = optim.SGD(model.parameters(), lr=0.1)
    criterion = nn.BCELoss()

    print(model)

    batch_size = 25
    train_loader = get_train_loader_hdf5(batch_size)
    validation_loader = get_validation_loader_hdf5(batch_size)

    # for data, target in train_loader:
    #     print(data.shape, data.dtype)
    #     print(target.shape, target.dtype)
    #     print(target[0])
    #     break
    # return

    log = get_tensorboard('simple')
    epochs = 20

    warmup_epochs = 1
    tot_time = 0
    for epoch in range(1, epochs + 1):
        start_time = datetime.now()
        train(model, train_loader, criterion, optimizer, epoch, log)

        with torch.no_grad():
            print('\nValidation:')
            evaluate(model, validation_loader, criterion, epoch, log)
        end_time = datetime.now()
        epoch_time = (end_time - start_time).total_seconds()
        txt = 'Epoch took {:.2f} seconds.'.format(epoch_time)
        if epoch > warmup_epochs:
            tot_time += epoch_time
            secs_per_epoch = tot_time/(epoch-warmup_epochs)
            txt += ' Running average: {:.2f}'.format(secs_per_epoch)

        print(txt)

    print('Total training time: {:.2f}, {:.2f} secs/epoch.'.format(tot_time, secs_per_epoch))

    torch.save(model.state_dict(), model_file)
    print('Wrote model to', model_file)


def test_main():
    print('Reading', model_file)
    model = Net()
    model.load_state_dict(torch.load(model_file))
    model.to(device)

    test_loader = get_test_loader_hdf5(25)

    print('=========')
    print('Simple:')
    with torch.no_grad():
        evaluate(model, test_loader)


if __name__ == '__main__':
    train_main()
    test_main()
