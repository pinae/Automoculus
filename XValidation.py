#!/usr/bin/python
# -*- coding: utf-8 -*-

from copy import deepcopy
from multiprocessing import Lock, Queue, Process

import numpy as np
from sklearn import preprocessing

from Beatscript import getContextAndBeatListFromFile, coalesceBeats
from Classify import getDataMatrix, trainSVM, pointMetric
from Config import TRAIN_FILES, SHOT_NAMES
from ConvertData import getSingleFeatureLine


def calculateDistributionAndClassification(classifier, context, blocks, decisions,
                                           scaler, shot_or_cut=True,
                                           returnQueue=None, leave_out_class=None):
    """
    Calculates a distribution using the given classifier. From that distribution the
    highest Value is selected as classification. Both distribution and classification
    are returned.
    """
    feature_line = getSingleFeatureLine(context, blocks, decisions, shot_or_cut,
        leave_out_class=leave_out_class)
    feature_line.pop()
    feature_vector = scaler.transform(np.array([feature_line]))
    distribution = classifier.predict_proba(feature_vector)
    classification = distribution[0].tolist().index(max(distribution[0].tolist()))
    #classification = int(classifier.predict(feature_vector)[0])
    if returnQueue:
        returnQueue.put((distribution, classification))
        returnQueue.close()
    return distribution, classification


def testAllButFile(file, files, scaler, return_queue, fake_decisions=False, C=None,
                   gamma=None, leave_out_class=None):
    """
    This function trains with all files in files except file, which is used for
    testing. The performance of the test is returned.
    """
    training_set = [f for f in files if f != file]
    training_data, training_data_classes = getDataMatrix(training_set,
        leave_out_class=leave_out_class, shot=True)
    training_data = scaler.transform(training_data, training_data_classes)
    trained_svm = trainSVM(training_data, training_data_classes, C=C, gamma=gamma)
    context, beatList = getContextAndBeatListFromFile(file)
    blockList = coalesceBeats(beatList)
    part_blockList = []
    decisions = []
    correct_classification_count = 0
    medium_shot_count = 0
    metric_sum = 0
    correct_histogram = [0, 0, 0, 0, 0, 0, 0]
    guessed_histogram = [0, 0, 0, 0, 0, 0, 0]
    #correct_histogram = [0, 0]
    #guessed_histogram = [0, 0]
    #last_block = None
    for block in blockList:
        # prepare block-list and decision-list
        part_blockList.append(block)
        if fake_decisions:
            decisions = []
            for i in range(len(part_blockList)-1):
                decisions.append(part_blockList[i][-1].shot)
        svm_distribution, svm_classification = calculateDistributionAndClassification(
            trained_svm, deepcopy(context),  part_blockList, decisions, scaler,
            shot_or_cut=True, leave_out_class=leave_out_class)
        if not fake_decisions:
            decisions.append(svm_classification)
        guessed_histogram[svm_classification] += 1
        correct_histogram[block[-1].shot] += 1
        #is_shot = True
        #if last_block:
        #    is_shot = block[-1].shotId != last_block[-1].shotId
        #correct_histogram[int(is_shot)] += 1
        if svm_classification == block[-1].shot:
        #if boost_classification == int(is_shot):
            correct_classification_count += 1
        if block[-1].shot == 2: medium_shot_count += 1
        if len(part_blockList) >= 2:
            previous_correct_class = part_blockList[-2][-1].shot
            if len(decisions) >= 2:
                previous_guessed_class = decisions[-2]
            else: previous_guessed_class = previous_correct_class
        else:
            previous_correct_class = part_blockList[-1][-1].shot
            if len(decisions) >= 1:
                previous_guessed_class = decisions[-1]
            else: previous_guessed_class = previous_correct_class
        metric_sum += pointMetric(svm_classification, block[-1].shot,
            previous_guessed_class, previous_correct_class)
        #last_block = block
    performance = float(correct_classification_count)/len(blockList)
    medium_shot_performance = float(medium_shot_count)/len(blockList)
    return_queue.put((
    correct_histogram, guessed_histogram, performance, medium_shot_performance,
    float(metric_sum) / len(blockList)))
    return_queue.close()


def ParallelXValidation(files, scaler, fake_decisions=False, C=None, gamma=None,
                        leave_out_class=None):
    """
    Since the decisions of the classifiers during classifying a beatscript are used this
    is not a classical cross-validation. Instead the training is done with all but one
    Training files and the remaining beatscript is tested based on the classification from
    that data. This process is repeated with all files.
    In this case the decision history is faked by using the original classes from the
    testfile.
    This function tests the performance for decisions using a SVM, each with faked History.
    This is the parallel version of the cross-validation which tests all files at one.
    """
    correct_histogram = [0, 0, 0, 0, 0, 0, 0]
    guessed_histogram = [0, 0, 0, 0, 0, 0, 0]
    #correct_histogram = [0, 0]
    #guessed_histogram = [0, 0]
    performances = []
    allover_point_sum = 0.0
    medium_shot_performances = []
    test_processes = []
    return_queues = []
    print("Initialized Data. Performing parallel tests for all files.")
    for file in files:
        return_queues.append(Queue(maxsize=1))
        test_processes.append(Process(target=testAllButFile, args=(
        file, files, scaler, return_queues[-1], fake_decisions, C, gamma, leave_out_class)))
        test_processes[-1].start()
    for i, process in enumerate(test_processes):
        file_correct_histogram, file_guessed_histogram, file_performance,\
        file_medium_shot_performance, file_pint_sum = return_queues[i].get()
        process.join()
        for i, value in enumerate(file_correct_histogram):
            correct_histogram[i] += value
        for i, value in enumerate(file_guessed_histogram):
            guessed_histogram[i] += value
        performances.append(file_performance)
        medium_shot_performances.append(file_medium_shot_performance)
        allover_point_sum += file_pint_sum

    print(correct_histogram)
    print(guessed_histogram)

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
    print("Wrongness:\t" + str(allover_point_sum / len(performances)))
    return allover_point_sum / len(performances)


def XValidation(files, fake_decisions = False):
    """
    Since the decisions of the classifiers during classifying a beatscript are used this
    is not a classical cross-validation. Instead the training is done with all but one
    Training files and the remaining beatscript is tested based on the classification from
    that data. This process is repeated with all files.
    In this case the decision history is faked by using the original classes from the
    testfile.
    This function tests the performance for decisions using a SVM, each with faked History.
    """
    reference_data, _ = getDataMatrix(TRAIN_FILES)
    scaler = preprocessing.Scaler()
    scaler.fit(reference_data)
    correct_histogram = [0, 0, 0, 0, 0, 0, 0]
    guessed_histogram = [0, 0, 0, 0, 0, 0, 0]
    performances = []
    allover_point_sum = 0.0
    medium_shot_performances = []
    for file in files:
        print("X-Validation: ca. " +
              str(int(round(float(files.index(file)) / len(files) * 100))) +
              "% fertig.")
        training_set = [f for f in files if f != file]
        training_data, training_data_classes = getDataMatrix(training_set)
        training_data = scaler.transform(training_data, training_data_classes)
        print("Trainingsdaten erzeugt. Trainiere Classifier...")
        print_lock = Lock()
        svm_queue = Queue(maxsize=1)
        svm_learning_process = Process(target=trainSVM,
            args=(training_data, training_data_classes, svm_queue, print_lock))
        svm_learning_process.start()

        context, beatList = getContextAndBeatListFromFile(file)
        blockList = coalesceBeats(beatList)
        part_blockList = []
        decisions = []
        correct_classification_count = 0
        medium_shot_count = 0
        metric_sum = 0

        trained_svm = svm_queue.get()
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
            svm_classification_process = Process(
                target=calculateDistributionAndClassification,
                args=(
                trained_svm, deepcopy(context), part_blockList, decisions, scaler, True,
                svm_queue))
            svm_classification_process.start()
            svm_distribution, svm_classification = svm_queue.get()
            svm_classification_process.join()
            if not fake_decisions:
                decisions.append(svm_classification)
            print("SVM Classification:\t" + SHOT_NAMES[svm_classification])
            guessed_histogram[svm_classification] += 1
            print("Correct Class:\t\t" + SHOT_NAMES[block[-1].shot])
            if len(part_blockList)>= 2:
                previous_correct_class = part_blockList[-2][-1].shot
                if len(decisions) >= 2:
                    previous_guessed_class = decisions[-2]
                else: previous_guessed_class = previous_correct_class
            else:
                previous_correct_class = part_blockList[-1][-1].shot
                if len(decisions) >= 1:
                    previous_guessed_class = decisions[-1]
                else: previous_guessed_class = previous_correct_class
            metric_value = pointMetric(svm_classification, block[-1].shot,
                previous_guessed_class, previous_correct_class)
            print("Wrongness:\t\t\t" + str(metric_value))
            metric_sum += metric_value
            correct_histogram[block[-1].shot] += 1
            if svm_classification == block[-1].shot:
                correct_classification_count += 1
            if block[-1].shot == 2: medium_shot_count += 1
            print("------------------------------------")

        print("File Performance: " + str(
            float(correct_classification_count) / len(blockList) * 100) + "%")
        print(
        "File Wrongness: " + str(float(metric_sum) / len(blockList)) + " Points ( 0 - 5 )")
        performances.append(float(correct_classification_count) / len(blockList))
        medium_shot_performances.append(float(medium_shot_count) / len(blockList))
        allover_point_sum += float(metric_sum) / len(blockList)
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
    print("Wrongness:\t" + str(allover_point_sum / len(performances)))
    return allover_point_sum / len(performances)

# =============================== Main =========================================
def main():
    #XValidation(TRAIN_FILES, True)
    reference_data, _ = getDataMatrix(TRAIN_FILES, shot=True)
    scaler = preprocessing.Scaler()
    scaler.fit(reference_data)
    #ParallelXValidation(TRAIN_FILES, scaler, True, C=2582.61517656, gamma=0.00036375303213)
    #ParallelXValidation(TRAIN_FILES, scaler, True, C=2583.31718583, gamma=0.00191943088336)
    #ParallelXValidation(TRAIN_FILES, scaler, True, C=2585.53147506, gamma=2.60057621686e-05)
    #ParallelXValidation(TRAIN_FILES, scaler, True, C=2585.61614258, gamma=2.15704131861e-05)
    #ParallelXValidation(TRAIN_FILES, scaler, True, C=2585.81448898, gamma=1.73105463456e-05)
    #ParallelXValidation(TRAIN_FILES, scaler, True, C=1999.62466242, gamma=1.62885637292e-06)
    #ParallelXValidation(TRAIN_FILES, scaler, True, C=1999.32984556, gamma=3.03787358388e-07)
    ParallelXValidation(TRAIN_FILES, scaler, False, C=1999.85770959, gamma=6.30930490772e-07)

if __name__ == "__main__":
    main()