#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals, print_function

__author__ = 'Klaus'

from Config import *
import ConvertData
import orange, orngTree
from Classify import getTrainingExamples, getDomain, getTestExamples, getNormalizationTerms
from copy import copy
import numpy as np
from matplotlib import pyplot as plt

def getSVM(C = 1.0, gamma = 0.0):
    svmLearner = orange.SVMLearner()
    svmLearner.C = C
    svmLearner.gamma = gamma
    svmLearner.svm_type = orange.SVMLearner.C_SVC
    return svmLearner


def createCrossValidationSet(leaveOutIndex, domain):
    trainFiles = copy(TRAIN_FILES)
    testFile = trainFiles.pop(leaveOutIndex)
    trainData = getTrainingExamples(domain, trainFiles, True)
    testData = getTestExamples(domain, testFile, True)
    return trainData, testData, trainFiles, testFile

def classify(classifier, testFile, domain, decisions, means, vars):
    featureLine = ConvertData.getSingleFeatureLineFromFile(testFile, decisions, True)
    featureLine = list((np.array(featureLine[:-1]) - means) / vars) + [featureLine[-1]]
    datum = orange.Example(domain, featureLine)
    classification = classifier(datum)
    correct = datum.get_class()
    return classification, correct


def getDifference(predicedClass, actualClass):
    p = SHOT_NAMES.index(predicedClass)
    a = SHOT_NAMES.index(actualClass)
    if a == p:
        return 0
    elif abs(a-p) == 1:
        return 1
    else :
        return 2

def getPerformance(classifier, domain, testFiles, means, vars):
    correct = 0
    weightedDiff = 0
    total = 0
    for testFile in testFiles:
        f = open(testFile, "r")
        lines = f.readlines()
        f.close()
        context = ConvertData.readContext(lines)
        blockList = ConvertData.getBlockList(lines, context)
        decisions = []
        for _ in range(len(blockList)):
            shotClass, correctClass = classify(classifier, testFile, domain, decisions, means, vars)
            decisions.append(shotClass)
            if correctClass == shotClass:
                correct += 1
            weightedDiff += getDifference(shotClass, correctClass)
            total += 1
    return correct/ total, weightedDiff / total

def doAFullRun(C = 1.0, gamma=0.0):
    # classifier konfigurieren
    learner = getSVM(C=C, gamma=gamma)
    domain = getDomain(orange.EnumVariable(name="Shot", values=SHOT_NAMES))
    means, vars = getNormalizationTerms(domain)
    # trainingsdaten und testdaten zusammenstellen
    totalTest = 0.0
    totalTrain = 0.0
    totalTestW = 0.0
    totalTrainW = 0.0
    for i in range(len(TRAIN_FILES)):
        print("============= Round %d ================" %i)
        print("training classifier...")
        trainData, testData , trainFiles, testFile = createCrossValidationSet(i, domain)
        # train normalisieren
        a, c, w = trainData.to_numpy()
        a = (a-means)/vars
        A = np.hstack((a,c.reshape(-1,1)))
        trainData = orange.ExampleTable(domain, A)
        # train classifier
        classifier = learner(trainData)
        print("evaluating test-set performance")
        # test set performance
        testPerf, testW = getPerformance(classifier, domain, [testFile], means, vars)
        print("evaluating train-set performance")
        # training performance
        trainPerf, trainW = getPerformance(classifier, domain, trainFiles, means, vars)
        print("Training Performance \t: %04f (weighted: %f)"%(trainPerf, trainW))
        print("Test Performance     \t: %04f (weighted: %f)"%(testPerf, testW))
        totalTest += testPerf
        totalTrain += trainPerf
        totalTestW +=testW
        totalTrainW += trainW
        # perfomance bestimmen auf train und testdaten
    totalTest /= len(TRAIN_FILES)
    totalTrain /= len(TRAIN_FILES)
    totalTestW /= len(TRAIN_FILES)
    totalTrainW /= len(TRAIN_FILES)

    print ("Average Training Performance: %04f (weighted: %f)"%(totalTrain, totalTrainW))
    print ("Average Test Performance    : %04f (weighted: %f)"%(totalTest, totalTestW))

def runExampleForDifferentParams(gammas = (0.0, ), Cs = (1.0, ), i = 5):
    domain = getDomain(orange.EnumVariable(name="Shot", values=SHOT_NAMES))
    means, vars = getNormalizationTerms(domain)
    trainData, testData , trainFiles, testFile = createCrossValidationSet(i, domain)
    # train normalisieren
    a, c, w = trainData.to_numpy()
    a = (a-means)/vars
    A = np.hstack((a,c.reshape(-1,1)))
    trainData = orange.ExampleTable(domain, A)
    for gamma in gammas:
        for C in Cs:
            print("========== Params (C = %f, gamma = %f) ============"%(C, gamma))
             # classifier konfigurieren
            learner = getSVM(gamma=gamma, C=C)
            # trainingsdaten und testdaten zusammenstellen
            print("training classifier...")
            # train classifier
            classifier = learner(trainData)
            print("evaluating test-set performance")
            # test set performance
            testPerf, testW = getPerformance(classifier, domain, [testFile], means, vars)
            print("evaluating train-set performance")
            # training performance
            trainPerf, trainW = getPerformance(classifier, domain, trainFiles, means, vars)
            print("Training Performance \t: %04f (weighted: %f)"%(trainPerf, trainW))
            print("Test Performance     \t: %04f (weighted: %f)"%(testPerf, testW))

def createLearningCurve(C = 1.0, gamma=0.0):
    trainFiles = copy(TRAIN_FILES)
    # classifier konfigurieren
    learner = getSVM(C=C, gamma=gamma)
    domain = getDomain(orange.EnumVariable(name="Shot", values=SHOT_NAMES))
    means, vars = getNormalizationTerms(domain)
    trainData = getTrainingExamples(domain, trainFiles, True)
    a, c, w = trainData.to_numpy()
    # train normalisieren
    a = (a-means)/vars
    A = np.hstack((a,c.reshape(-1,1)))
    np.random.shuffle(A)
    performance = []
    wPerformance = []
    for j in range(100, A.shape[0],100):
        print("============= TrainingFiles %d ================"%j)
        print("training classifier...")
        trainData = orange.ExampleTable(domain, A[:j,:])
        # train classifier
        classifier = learner(trainData)
        # training performance
        print("testing classifier...")
        perf, perfW = getPerformance(classifier, domain, TRAIN_FILES, means, vars)
        print("Performance \t: %04f (weighted: %f)"%(perf, perfW))
        performance.append(perf)
        wPerformance.append(perfW)
    return performance, wPerformance


def main():
    doAFullRun()
    #a, b = createLearningCurve(C=0.78)
    #plt.plot(a)
    #plt.plot(b)
    #plt.show()


if __name__ == "__main__":
    main()