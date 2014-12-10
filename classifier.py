import math
import random

class Naive_Bayesian:
    def __init__(self, dataset):
        self.attr_n = len(dataset[0])
        self.dataset = dataset
        self.ad_n = 0
        self.nad_n = 0
        self.ad_total = [0] * len(dataset[0])
        self.nad_total = [0] * len(dataset[0])
        for sample in dataset:
            if sample[-1] == "ad":
                self.ad_n += 1
                for i in range(len(dataset[0]) - 1):
                    self.ad_total[i] += sample[i]
            else:
                self.nad_n += 1
                for i in range(len(dataset[0]) - 1):
                    self.nad_total[i] += sample[i]
        self.ad_mean = [self.ad_total[0] / self.ad_n, self.ad_total[1] / self.ad_n, self.ad_total[2] / self.ad_n]
        self.nad_mean = [self.nad_total[0] / self.nad_n, self.nad_total[1] / self.nad_n, self.nad_total[2] / self.nad_n]
        self.ad_sqd = [0, 0, 0]
        self.nad_sqd = [0, 0, 0]
        for sample in dataset:
            if sample[-1] == "ad":
                for i in range(3):
                    self.ad_sqd[i] += (sample[i] - self.ad_mean[i]) * (sample[i] - self.ad_mean[i])
            else:
                for i in range(3):
                    self.nad_sqd[i] += (sample[i] - self.nad_mean[i]) * (sample[i] - self.nad_mean[i])
        self.ad_sqd = [self.ad_sqd[0] / self.ad_n, self.ad_sqd[1] / self.ad_n, self.ad_sqd[2] / self.ad_n]
        self.nad_sqd = [self.nad_sqd[0] / self.nad_n, self.nad_sqd[1] / self.nad_n, self.nad_sqd[2] / self.nad_n]

    def ndp(self, x, mean, std):
        x = (x - mean) / math.sqrt(std)
        return math.exp(-x * x / 2) / math.sqrt(math.acos(-1) * 2)

    def probability(self, sample):
        total = self.ad_n + self.nad_n
        ad_p = float(self.ad_n) / total
        nad_p = float(self.nad_n) / total
        for i in range(3):
            ad_p *= self.ndp(sample[i], self.ad_mean[i], self.ad_sqd[i])
            nad_p *= self.ndp(sample[i], self.nad_mean[i], self.nad_sqd[i])
        for i in range(3, len(sample)):
            if sample[i] == 1:
                ad_p *= float(self.ad_total[i]) / total
                nad_p *= float(self.nad_total[i]) / total
            else:
                ad_p *= 1 - float(self.ad_total[i]) / total
                nad_p *= 1 - float(self.nad_total[i]) / total
        category = ""
        if ad_p > nad_p:
            category = "ad"
        else:
            category = "nonad"
        return (ad_p, nad_p, category)

def read():
    fr = open("dataset/ad.imputed")
    dataset = []
    for sample in fr.readlines():
        sample = sample.split()
        for i in range(len(sample) - 1):
            if i < 3:
                sample[i] = float(sample[i])
            else:
                sample[i] = int(sample[i])
        dataset.append(sample)
    fr.close()
    return dataset

def ten_fold(dataset):
    folds = []
    index = []
    for i in range(10):
        folds.append([])
        index.append([])
    for i in range(len(dataset)):
        r = random.random()
        folds[int(r * 10)].append(dataset[i])
        index[int(r * 10)].append(i)
    total = 0
    return (folds, index)

def accuracy(nbc, testset):
    correct = 0
    total = len(testset)
    for test in testset:
        (ad_p, nad_p, label) = nbc.probability(test[:-1])
        if label == test[-1]:
            correct += 1
    return (correct, total)

def false_positive(nbc, testset):
    false = 0
    total = 0
    for test in testset:
        (ad_p, nad_p, label) = nbc.probability(test[:-1])
        if test[-1] == "nonad":
            total += 1
            if label == "ad":
                false += 1
    return (false, total)

def cross_validation(dataset):
    (folds, index) = ten_fold(dataset)
    correct = 0
    total = 0
    false = 0
    neg = 0
    for i in range(10):
        train = []
        test = folds[i]
        for j in range(10):
            if i != j:
                train.extend(folds[j])
        nbc = Naive_Bayesian(train)
        (fold_correct, fold_total) = accuracy(nbc, test)
        (fold_false, fold_neg) = false_positive(nbc, test)
        #print "Fold Accuracy: {0:.2%}".format(float(fold_correct) / fold_total)
        false += fold_false
        neg += fold_neg
        correct += fold_correct
        total += fold_total
    print "Cross Validation Accuracy: {0:.2%}".format(float(correct) / total)
    print "Cross Validation FPR: {0:.2%}".format(float(false) / neg)
    return float(correct) / total

def two_stage(dataset, threshold):
    (folds, index) = ten_fold(dataset)
    correct = 0
    total = 0
    u = set()
    undetermined = []
    for i in range(10):
        train = []
        test = folds[i]
        test_index = index[i]
        for j in range(10):
            if i != j:
                train.extend(folds[j])
        nbc = Naive_Bayesian(train)
        for i in range(len(test)):
            (ad_p, nad_p, label) = nbc.probability(test[i][:-1])
            if nad_p == 0 or ad_p / nad_p >= threshold:
                u.add(test_index[i])
    for num in u:
        undetermined.append(dataset[num])
    nbc_a = Naive_Bayesian(dataset)
    nbc_b = Naive_Bayesian(undetermined)
    return (nbc_a, nbc_b)

def cross_validation_stage(dataset, threshold):
    (folds, index) = ten_fold(dataset)
    correct = 0
    total = 0
    false = 0
    neg = 0
    for i in range(10):
        train = []
        testset = folds[i]
        for j in range(10):
            if i != j:
                train.extend(folds[j])
        (nbc_a, nbc_b) = two_stage(train, threshold)
        fold_correct = 0
        fold_total = len(testset)
        fold_false = 0
        fold_neg = 0
        for test in testset:
            (ad_p, nad_p, label) = nbc_a.probability(test[:-1])
            if nad_p == 0 or ad_p / nad_p >= threshold:
                (ad_p, nad_p, label) = nbc_b.probability(test[:-1])
            if label == test[-1]:
                fold_correct += 1
            if test[-1] == "nonad":
                fold_neg += 1
                if label == "ad":
                    fold_false += 1
        #print "Fold Accuracy: {0:.2%}".format(float(fold_correct) / fold_total)
        false += fold_false
        neg += fold_neg
        correct += fold_correct
        total += fold_total
    print "Cross Validation Accuracy: {0:.2%}".format(float(correct) / total)
    print "Cross Validation FPR: {0:.2%}".format(float(false) / neg)
    return float(correct) / total

def main():
    dataset = read()
    print "Naive Bayesian:"
    cross_validation(dataset)
    print "Two Stage:"
    cross_validation_stage(dataset, 1)

if __name__ == "__main__":
    main()
