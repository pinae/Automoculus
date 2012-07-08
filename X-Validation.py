#!/usr/bin/python
# -*- coding: utf-8 -*-

from copy import deepcopy
from multiprocessing import Lock, Queue, Process

import numpy as np
from sklearn import cross_validation, preprocessing, svm, linear_model

from Beatscript import getContextAndBeatListFromFile, coalesceBeats
from Classify import getDataMatrix, trainSVM
from Config import TRAIN_FILES, SHOT_NAMES
from ConvertData import getSingleFeatureLine


def calculateDistributionAndClassification(classifier, context, blocks, decisions, scaler, shot_or_cut=True, returnQueue=None):
    """
    Calculates a distribution using the given classifier. From that distribution the highest Value is selected as
     classification. Both distribution and classification are returned.
    """
    feature_line = getSingleFeatureLine(context, blocks, decisions, shot_or_cut)
    feature_line.pop()
    #feature_vector = np.array(feature_line, dtype=np.float64)
    feature_vector = scaler.transform(np.array([feature_line]))
    distribution = classifier.predict_proba(feature_vector)
    #print(distribution.tolist())
    classification = distribution.tolist().index(max(distribution.tolist()))
    classification = int(classifier.predict(feature_vector)[0])
    #print(classifier.predict(feature_vector))
    if returnQueue:
        returnQueue.put((distribution, classification))
        returnQueue.close()
    return distribution, classification


def XValidation(files, fake_decisions = False):
    """
    Since the decisions of the classifiers during classifying a beatscript are used this is not a classical
     cross-validation. Instead the training is done with all but one Training files and the remaining beatscript
     is tested based on the classification from that data. This process is repeated with all files.
    In this case the decision history is faked by using the original classes from the testfile.
    This function tests the performance for boosted decisions using a treeLearner and a svmLearner, each with
     faked History.
    """
    reference_data, _ = getDataMatrix(TRAIN_FILES)
    #reference_data = np.array(reference_data, dtype=np.float64) # convert to float
    scaler = preprocessing.Scaler()
    scaler.fit(reference_data)
    correct_histogram = [0, 0, 0, 0, 0, 0, 0]
    guessed_histogram = [0, 0, 0, 0, 0, 0, 0]
    performances = []
    medium_shot_performances = []
    for file in files:
        print("X-Validation: ca. " + str(int(round(float(files.index(file)) / len(files) * 100))) +
              "% fertig.")
        training_set = [f for f in files if f != file]
        training_data, training_data_classes = getDataMatrix(training_set)
        #training_data = np.array(training_data, dtype=np.float64) # convert to float
        training_data = scaler.transform(training_data, training_data_classes)
        print("Trainingsdaten erzeugt. Trainiere Classifier...")
        print_lock = Lock()
        svm_queue = Queue(maxsize=1)
        svm_learning_process = Process(target=trainSVM, args=(training_data, training_data_classes, svm_queue, print_lock))
        svm_learning_process.start()
        #tree_queue = Queue(maxsize=1)
        #tree_learning_process = Process(target=trainTree, args=(training_data, tree_queue, print_lock))
        #tree_learning_process.start()

        context, beatList = getContextAndBeatListFromFile(file)
        blockList = coalesceBeats(beatList)
        part_blockList = []
        decisions = []
        correct_classification_count = 0
        medium_shot_count = 0

        #trained_tree = tree_queue.get()
        trained_svm = svm_queue.get()
        #tree_learning_process.join()
        svm_learning_process.join()
        print("Training finished for: " + file)
        for block in blockList:
            # prepare blocklist and decision-list
            part_blockList.append(block)
            if fake_decisions:
                decisions = []
                for i in range(len(part_blockList)-1):
                    decisions.append(part_blockList[i][-1].shot)
            svm_queue = Queue(maxsize=1)
            svm_classification_process = Process(target=calculateDistributionAndClassification,
                args=(trained_svm, deepcopy(context), part_blockList, decisions, scaler, True, svm_queue))
            svm_classification_process.start()
            #tree_queue = Queue(maxsize=1)
            #tree_classification_process = Process(target=calculateDistributionAndClassification,
            #    args=(trained_tree, domain, deepcopy(context), part_blockList, decisions, means, vars, True, tree_queue))
            #tree_classification_process.start()
            #tree_distribution, tree_classification = tree_queue.get()
            svm_distribution, svm_classification = svm_queue.get()
            #tree_classification_process.join()
            svm_classification_process.join()
            #boost_classification = calculateBoostingFromDistributions(domain, tree_distribution, svm_distribution)
            boost_classification = svm_classification
            if not fake_decisions:
                decisions.append(boost_classification)
            #print("Tree Classification:\t" + tree_classification.value)
            print("SVM Classification:\t" + SHOT_NAMES[svm_classification])
            #print("Boosted Classification:\t" + boost_classification.value)
            guessed_histogram[boost_classification] += 1
            print("Correct Class:\t\t" + SHOT_NAMES[block[-1].shot])
            correct_histogram[block[-1].shot] += 1
            if boost_classification == block[-1].shot:
                correct_classification_count += 1
            if block[-1].shot == 2: medium_shot_count += 1
            print("------------------------------------")

        print("File Performance: "+str(float(correct_classification_count)/len(blockList)*100)+"%")
        performances.append(float(correct_classification_count)/len(blockList))
        medium_shot_performances.append(float(medium_shot_count)/len(blockList))
        print("__________________________________________")

    performance_sum = 0
    performance_best = 0
    performance_last = 1
    for p in medium_shot_performances:
        performance_sum += p
        if p > performance_best: performance_best = p
        if p < performance_last: performance_last = p
    print("MS-Performance:\t" + str(performance_sum / len(performances) * 100.0) + "%\t(" +
          str(performance_last) + " - " + str(performance_best) + ")")

    performance_sum = 0
    performance_best = 0
    performance_last = 1
    for p in performances:
        performance_sum += p
        if p > performance_best: performance_best = p
        if p < performance_last: performance_last = p
    print("Performance:\t" + str(performance_sum / len(performances) * 100.0) + "%\t(" +
          str(performance_last) + " - " + str(performance_best) + ")")
    return performance_sum / len(performances)

# =============================== Main =========================================
def main():
    XValidation(TRAIN_FILES, False)

if __name__ == "__main__":
    main()

#X, y = getDataMatrix(TRAIN_FILES)
#X = np.array(X, dtype=np.float64) # convert to float
#X_scaled = preprocessing.scale(X) # normalize
######### SVM #########
#s = svm.SVC()
#scores = cross_validation.cross_val_score(s, X_scaled, y, cv=10)
#print "SVM Ergebnis: ", scores.mean()
#print "Einzelergebnisse für die 10-Fold-Cross-Validation:", scores
######### Linear Regression #########
#lr = linear_model.LogisticRegression()
#scores = cross_validation.cross_val_score(lr, X_scaled, y, cv=10)
#print "Lineare Regression Ergebnis: ", scores.mean()
#print "Einzelergebnisse für die 10-Fold-Cross-Validation:", scores