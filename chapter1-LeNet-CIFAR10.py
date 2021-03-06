# -*- coding: utf-8 -*-
import torch
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import time
from tensorboardX import SummaryWriter

# 超参数设置
EPOCH = 50   #遍历数据集次数
BATCH_SIZE = 4      #批处理尺寸(batch_size)
LR = 0.001        #学习率


########################################################################
# The output of torchvision datasets are PILImage images of range [0, 1].
# We transform them to Tensors of normalized range [-1, 1].

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

trainset = torchvision.datasets.CIFAR10(
    root='/media/mcislab/GaoXiangjun/Learn_Pytorch/data/', train=True, download=True, transform=transform)
trainloader = torch.utils.data.DataLoader(
    trainset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)

testset = torchvision.datasets.CIFAR10(
    root='/media/mcislab/GaoXiangjun/Learn_Pytorch/data/', train=False, download=True, transform=transform)
testloader = torch.utils.data.DataLoader(
    testset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

classes = ('plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse',
           'ship', 'truck')

########################################################################
# 2. Define a Convolution Neural Network
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# Copy neural network from the Neural Networks section before and modify it to
# take 3-channel images (instead of 1-channel images as it was defined).


class LeNet(nn.Module):
    def __init__(self):
        super(LeNet, self).__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(-1, 16 * 5 * 5)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x


# functions to show an image


def imshow(img):
    img = img / 2 + 0.5  # unnormalize
    npimg = img.numpy()
    plt.imshow(np.transpose(npimg, (1, 2, 0)))


def main():

    writer = SummaryWriter('LeNet_CIFAR')
    net = LeNet()
    net.cuda()
    # device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    # net.to(device)
    ########################################################################
    # 3. Define a Loss function and optimizer
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    # Let's use a Classification Cross-Entropy loss and SGD with momentum.

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(net.parameters(), lr=LR)

    ########################################################################
    # 4. Train the network
    # ^^^^^^^^^^^^^^^^^^^^
    #
    # This is when things start to get interesting.
    # We simply have to loop over our data iterator, and feed the inputs to the
    # network and optimize.

    for epoch in range(EPOCH):  # loop over the dataset multiple times
        t0 = time.time()
        running_loss = 0.0
        total_train = 0
        correct_train = 0
        for i, data in enumerate(trainloader, 0):
            # get the inputs
            inputs, labels = data

            inputs = inputs.cuda()
            labels = labels.cuda()

            # zero the parameter gradients
            optimizer.zero_grad()

            # forward + backward + optimize
            outputs = net(inputs)
            _, predicted = torch.max(outputs.detach(), 1)
            total_train += labels.size(0)
            correct_train += (predicted == labels).sum().item()

            # 计算loss    反向传播
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            # print statistics
            running_loss += loss.item()
            if i % 2000 == 1999:  # print every 2000 mini-batches
                print('[%d, %5d] loss: %.3f' % (epoch + 1, i + 1,
                                                running_loss / 2000))
                writer.add_scalar("train_loss", running_loss/2000, (epoch)*len(trainloader)/2000 + i/2000)
                running_loss = 0.0
                t1 = time.time()
                #print('epoch:%d     batch:%d    time per 2000 batches:%lf' %
                #      (epoch+1, i+1, t1 - t0))
                t0 = time.time()

        print('epoch:%d    train_acc：%d%%' % (epoch + 1, (100 * correct_train / total_train)))
        writer.add_scalar('train_acc', (100 * correct_train / total_train),epoch+1)

        with torch.no_grad():
            correct = 0
            total = 0
            for data in testloader:
                images, labels = data
                images = images.cuda()
                labels = labels.cuda()
                outputs = net(images)
                _, predicted = torch.max(outputs.detach(), 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

            print('epoch:%d    val_acc：%d%%' % (epoch + 1, (100 * correct / total)))
            writer.add_scalar('val_acc', (100 * correct / total),epoch + 1)

        # 保存每个epoch下的模型参数
        torch.save(net.state_dict(), './LeNet_CIFAR/LeNet_CIFAR_%03d_params.pkl' % (epoch + 1))

    print('Finished Training')
    writer.export_scalars_to_json("./LeNet_MNIST/LeNet_MNIST.json")
    writer.close()


    ########################################################################
    # 5. Test the network on the test data
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #
    # We have trained the network for 2 passes over the training dataset.
    # But we need to check if the network has learnt anything at all.
    #
    # We will check this by predicting the class label that the neural network
    # outputs, and checking it against the ground-truth. If the prediction is
    # correct, we add the sample to the list of correct predictions.

    correct = 0
    total = 0
    with torch.no_grad():
        for data in testloader:
            images, labels = data
            images = images.cuda()
            labels = labels.cuda()
            outputs = net(images)
            _, predicted = torch.max(outputs.detach(), 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    print('Accuracy of the network on the 10000 test images: %d %%' %
          (100 * correct / total))


    ########################################################################
    # That looks waaay better than chance, which is 10% accuracy
    # (randomly picking a class out of 10 classes).
    # Seems like the network learnt something.
    #
    # Hmmm, what are the classes that performed well, and the classes that did
    # not perform well:

    class_correct = list(0. for i in range(10))  # 0. float
    class_total = list(0. for i in range(10))
    with torch.no_grad():
        for data in testloader:
            images, labels = data
            images = images.cuda()
            labels = labels.cuda()
            outputs = net(images)
            _, predicted = torch.max(outputs.detach(), 1)
            c = (predicted == labels).squeeze()
            for i in range(4):
                label = labels[i]
                class_correct[label] += c[i].item()
                class_total[label] += 1

    for i in range(10):
        print('Accuracy of %5s : %2d %%' %
              (classes[i], 100 * class_correct[i] / class_total[i]))


if __name__ == '__main__':
    main()
