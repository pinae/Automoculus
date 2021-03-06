#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================== Imports ======================================
from multiprocessing import Process, Queue

import numpy as np
from sklearn import svm
#from sklearn import neighbors
#from sklearn import tree
#from sklearn import linear_model
#from sklearn import naive_bayes

from ConvertData import getSingleFeatureLine, getFeatureLinesFromFile, getFeatureLine
from Config import SHOT_NAMES, DETAIL, CLOSEUP, MEDIUM_SHOT, AMERICAN_SHOT
from Config import ACTION, SAYS, INTRODUCE, EXPRESS, SHOW

# =============================== Methods ======================================
def getDataMatrix(file_set, shot=True, leave_out_class=None):
    """
    Returns an Numpy-Array with the feature_lines converted from all the beatscripts
    mentioned in files.
    """
    matrix = []
    classes = []
    for file in file_set:
        feature_lines = getFeatureLinesFromFile(file, shot, leave_out_class=leave_out_class)
        for line in feature_lines:
            if shot:
                classes.append(SHOT_NAMES.index(line.pop()))
            else:
                classes.append(int(line.pop()=="True"))
            matrix.append(np.array(line))
    return np.array(matrix, dtype=np.float64), np.array(classes)


def normalizeDist(distribution):
    sum = 0.0
    for i in range(len(distribution)):
        sum += distribution[i]
    result = []
    for i in range(len(distribution)):
        result.append(distribution[i] / sum)
    return result


def smoothDistribution(dist):
    """
    Returns a similar distribution which has values > 0 if neighbouring values of the
    original distribution were > 0.
    """
    smoothed = [dist[0]]
    for i in range(1, len(dist)):
        value = 0.6 * dist[i]
        if i >= 2: value += 0.05 * i * dist[i - 1]
        else: value += 0.05 * i * dist[i]
        if i < len(dist) - 1: value += 0.05 * i * dist[i + 1]
        else: value += 0.05 * i * dist[i]
        smoothed.append(value)
    return smoothed


def trainSVM(training_data, training_data_classes, returnQueue=None, lock=None, C=None,
             gamma=None):
    """
    Returns a svmLearner object trained with the given training_data.
    The object is also placed in the returnQueue.
    The lock is used for printing and nothing else.
    The commented classifiers are for quick testing. If you want to switch to another
    classifier rename the function.
    """
    if C and gamma:
        svm_classifier = svm.SVC(probability = True, C=C, gamma=gamma, cache_size=1000.0)
        #svm_classifier = neighbors.KNeighborsClassifier(n_neighbors=C)
    else:
        svm_classifier = svm.SVC(probability = True, cache_size=1000.0)
        #svm_classifier = neighbors.KNeighborsClassifier()
        #svm_classifier = tree.DecisionTreeClassifier()
        #svm_classifier = linear_model.Perceptron()
        #svm_classifier = naive_bayes.GaussianNB()
    svm_classifier.fit(training_data, training_data_classes)
    if returnQueue:
        returnQueue.put(svm_classifier)
        returnQueue.close()
    if lock:
        lock.acquire()
        print("Training for SVM finished.")
        lock.release()
    return svm_classifier


def classification(classifier, context, blockList, decisions, scaler, returnQueue=None,
                   shot=True, leaveout=-1):
    """
    Returns a classification, no propabilities.
    """
    feature_line = getSingleFeatureLine(context, blockList, decisions, shot, leaveout)
    class_from_file = feature_line.pop()
    feature_line = scaler.transform(feature_line)
    classification = classifier.predict(feature_line)
    if returnQueue:
        returnQueue.put(classification)
        returnQueue.close()
    return classification


def calculateDistribution(classifier, datum, returnQueue=None):
    """
    Calculates a distribution from the scaled data.
    """
    distribution = normalizeDist(classifier.predict_proba(datum).tolist()[0])
    if returnQueue:
        returnQueue.put(distribution)
        returnQueue.close()
    return distribution


def cutBeforeThisBlock(blockList, decisions, keepingPropability):
    """
    This is the old handwritten cut prediction this code was used to construct a feature
    which utilizes the information to achieve a better performance.
    """
    cut = True
    if len(blockList) >= 2 <= len(decisions):
        if blockList[-1][0].subject == blockList[-2][-1].subject and (
            decisions[-2] >= MEDIUM_SHOT and blockList[-1][0].type in [SAYS, ACTION]) or (
            decisions[-2] >= CLOSEUP and blockList[-1][0].type == SAYS):
            cut = False
        if decisions[-2] == decisions[-1]:
            cut = False
            subjects_of_history = set()
            for block in blockList[-2]:
                subjects_of_history.add(block.subject)
            subjects_of_today = set()
            for block in blockList[-1]:
                subjects_of_today.add(block.subject)
            for subject in subjects_of_today:
                if not subject in subjects_of_history:
                    cut = True
        if decisions[-2] >= AMERICAN_SHOT and decisions[-1] >= MEDIUM_SHOT:
            cut = False
            if len(blockList) >= 4:
                subjects_of_history = set()
                for i in range(-4, -2):
                    for block in blockList[i]:
                        subjects_of_history.add(block.subject)
                subjects_of_today = set()
                for block in blockList[-1]:
                    subjects_of_today.add(block.subject)
                for subject in subjects_of_today:
                    if not subject in subjects_of_history:
                        cut = True
            if keepingPropability < 0.02:
                cut = True
            for beat in blockList[-1]:
                if beat.type in [SHOW, INTRODUCE] and len(blockList) >= 5:
                    cut = True
        if blockList[-1][0].subject != blockList[-2][0].subject and\
           blockList[-1][0].type == SAYS and blockList[-2][0].type == SAYS:
            cut = True
    if len(decisions) >= 2:
        if decisions[-2] == DETAIL:
            cut = True
    if len(blockList) >= 1:
        if blockList[-1][0].type == EXPRESS:
            cut = True
    return cut


def distributionOfClassification(feature_line, classifiers, dist):
    """
    Calculates a distribution using the first of the given classifiers and the scaled
    data from feature_line.
    """
    svm = classifiers[0]
    svmDistributionReturnQueue = Queue()
    computeSVMDistribution = Process(target=calculateDistribution,
                                     args=(svm, feature_line, svmDistributionReturnQueue))
    computeSVMDistribution.start()
    svmDistribution = svmDistributionReturnQueue.get()
    computeSVMDistribution.join()
    # this is a hack for classifiers with less useful propabilities (eg. Decision Tree)
    #return smoothDistribution(dist)
    # use this for SVMs
    return svmDistribution


def classifyForShot(block, context, classifiers, scaler):
    """
    Constructs a feature-line from the block and the history in context. There needs to
    be a correctly constructed context for this function to work. The feature-line is
    scaled using the scaler. Then the distribution for all classifiers is compted and
    a single mixed distribution is returned.
    """
    feature_line = getFeatureLine(context, block, True, -1)
    feature_line.pop()
    feature_line = scaler.transform(feature_line)
    return distributionOfClassification(feature_line, classifiers,
        dist=[0, 0, 0, 0, 0, 0, 0])


def classifyForCut(block, context, classifiers, scaler):
    """
    Constructs a feature-line from the block and the history in context. There needs
    to be a correctly constructed context for this function to work. The feature-line
    is scaled using the scaler. Then the distribution for all classifiers is compted
    and a single mixed distribution is returned. This function is for computing the
    decision if there should be a cut or not.
    """
    if len(context["BygoneBlocks"]) >= 1:
        last_shot_id = context["BygoneBlocks"][-1][-1].shotId
    else: last_shot_id = 0
    feature_line = getFeatureLine(context, block, True, last_shot_id)
    feature_line.pop()
    feature_line = scaler.transform(feature_line)
    return distributionOfClassification(feature_line, classifiers, dist=[0, 0])


def pointMetric(guessed_class, correct_class, previous_guessed_class,
                previous_correct_class):
    if correct_class == DETAIL:
        if guessed_class != correct_class: return 5
        else: return 0
    else:
        if (correct_class - previous_correct_class) - (
        guessed_class - previous_guessed_class) >= 0:
            direction_value = 0
        else: direction_value = 1
        return 2 * min(abs(correct_class - guessed_class), 2) + direction_value


# =============================== Main =========================================
def main():
    print("nothing to do")

if __name__ == "__main__":
    main()