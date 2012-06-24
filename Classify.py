#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================== Imports ======================================
from copy import deepcopy
from multiprocessing import Process, Queue, Lock
#import random
#import sys

import ConvertData
import orange, orngTree
import numpy as np

from ConvertData import getSingleFeatureLine
from Beatscript import getContextAndBeatListFromFile, coalesceBeats
from Config import SHOT_NAMES, TRAIN_FILES, CLOSEUP, ACTION, SAYS, MEDIUM_SHOT, EXPRESS
#from Config import FULL_SHOT
from Config import SHOW, INTRODUCE, DETAIL, AMERICAN_SHOT

# =============================== Methods ======================================
def getTrainingExamples(domain, files, shot, leaveoutfeature=-1):
    """
    Returns an orange.ExampleTable with the featureLines converted from all the beatscripts mentioned in files.
    """
    examples = orange.ExampleTable(domain)
    for file in files:
        featureLines = ConvertData.getFeatureLinesFromFile(file, shot, leaveout=leaveoutfeature)
        #featureLines = ConvertData.getFeatureLinesFromFileAndModify(file, shot)
        for featureLine in featureLines:
            examples.append(orange.Example(domain, featureLine))
            #print line
    return examples


def getTestExamples(domain, file, shot, leaveoutfeature=-1):
    """
    Returns an ExampleTable with featureLines converted from the given File.
    """
    examples = orange.ExampleTable(domain)
    featureLines = ConvertData.getFeatureLinesFromFile(file, shot, leaveout=leaveoutfeature)
    for line in featureLines:
        examples.append(orange.Example(domain, line))
    return examples

def getTestExample(domain, context, blockList, decisions, shot):
    """
    Returns just one Example calculated from the given blockList
    """
    featureLine = getSingleFeatureLine(context, blockList, decisions, shot)
    return orange.Example(domain, featureLine)

def getNormalizationTerms(referenceData):
    """
    Returns (means, vars) for an ExampleTable given in referenceData.
    """
    a, c, w = referenceData.to_numpy()
    means = a.mean(0)
    vars = a.var(0) + 0.00000001
    return means, vars


def normalizeData(domain, trainData, means, vars):
    """
    Returns an ExampleTable with normalized Numbers.
    """
    a, c, w = trainData.to_numpy()
    a = (a - means) / vars
    A = np.hstack((a, c.reshape(-1, 1)))
    return orange.ExampleTable(domain, A)


def normalizeDatum(datum, means, vars):
    for i in range(len(datum) - 1):
        datum[i] = orange.Value((datum[i].value - means[i]) / vars[i])
    return datum


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
    Returns a similar distribution which has values > 0 if neighbouring values of the original distribution were > 0.
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


def trainTree(trainingData, returnQueue=None, lock=None):
    """
    Returns a TreeLearner object trained with the given training_data.
    The object is also placed in the returnQueue.
    The lock is used for printing and nothing else.
    """
    tree = orngTree.TreeLearner(trainingData, mForPruning=2)
    if returnQueue:
        returnQueue.put(tree)
        returnQueue.close()
    if lock:
        lock.acquire()
        print("Training for Decision Tree finished.")
        lock.release()
    return tree


def trainRule(lock, trainingData, returnQueue):
    ruleLearner = orange.RuleLearner()
    ruleLearningClassifier = ruleLearner(trainingData)
    returnQueue.put(ruleLearningClassifier)
    returnQueue.close()
    lock.acquire()
    print("Training for Rule Induction finished.")
    lock.release()
    return ruleLearningClassifier


def trainSVM(trainingData, returnQueue=None, lock=None, C=0.79):
    """
    Returns a svmLearner object trained with the given training_data.
    The object is also placed in the returnQueue.
    The lock is used for printing and nothing else.
    """
    svmLearner = orange.SVMLearner()
    svmLearner.C = C
    svmLearner.svm_type = orange.SVMLearner.C_SVC
    svmClassifier = svmLearner(trainingData)
    if returnQueue:
        returnQueue.put(svmClassifier)
        returnQueue.close()
    if lock:
        lock.acquire()
        print("Training for SVM finished.")
        lock.release()
    return svmClassifier


def classification(classifier, context, blockList, domain, decisions, means, vars, returnQueue=None, shot=True, leaveout=-1):
    featureLine = ConvertData.getSingleFeatureLine(context, blockList, decisions, shot, leaveout)
    datum = orange.Example(domain, featureLine)
    datum = normalizeDatum(datum, means, vars)
    classification = classifier(datum)
    if returnQueue:
        returnQueue.put(classification)
        returnQueue.close()
    return classification


def distribution(classifier, datum, returnQueue):
    distribution = normalizeDist(classifier(datum, classifier.GetProbabilities))
    returnQueue.put(distribution)
    returnQueue.close()
    return distribution


def getDomain(enumVariable, leaveoutfeature=-1):
    featureNames = ConvertData.getFeatureNames(leaveout=leaveoutfeature)
    attributes = []
    for name in featureNames:
        attributes.append(orange.FloatVariable(name=name))
    return orange.Domain(attributes, enumVariable)


def cutBeforeThisBlock(blockList, decisions, keepingPropability):
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
        #print(cut)
    return cut


def distributionOfClassification(domain, featureLine, classifiers, dist, means, vars):
    boostDatum = orange.Example(domain, featureLine)
    boostDatum = normalizeDatum(boostDatum, means, vars)
    treeDistributionReturnQueue = Queue()
    computeTreeDistribution = Process(target=distribution,
                                      args=(classifiers[0], boostDatum, treeDistributionReturnQueue))
    computeTreeDistribution.start()
    #ruleDistributionReturnQueue = Queue()
    #computeRuleDistribution = Process(target=distribution,
    #                                  args=(classifiers[1], boostDatum, ruleDistributionReturnQueue))
    #computeRuleDistribution.start()
    svmDistributionReturnQueue = Queue()
    computeSVMDistribution = Process(target=distribution,
                                     args=(classifiers[1], boostDatum, svmDistributionReturnQueue))
    computeSVMDistribution.start()
    treeDistribution = treeDistributionReturnQueue.get()
    #ruleDistribution = ruleDistributionReturnQueue.get()
    svmDistribution = svmDistributionReturnQueue.get()
    computeTreeDistribution.join()
    #computeRuleDistribution.join()
    computeSVMDistribution.join()
    for i in range(0, len(dist)):
        #dist[i] = (treeDistribution[i] * 0.39 + ruleDistribution[i] * 0.33 + svmDistribution[i] * 0.28)
        dist[i] = (treeDistribution[i] * 0.60 + svmDistribution[i] * 0.40)
    return smoothDistribution(dist)


def classifyForShot(domain, block, context, classifiers, means, vars):
    featureLine = ConvertData.getFeatureLine(context, block, True, -1)
    return distributionOfClassification(domain, featureLine, classifiers, dist=[0, 0, 0, 0, 0, 0, 0],
                                        means=means, vars=vars)


def classifyForCut(domain, block, context, classifiers, means, vars):
    featureLine = ConvertData.getFeatureLine(context, block, False, -1)
    return distributionOfClassification(domain, featureLine, classifiers, dist=[0, 0], means=means, vars=vars)


def classifyForDistribution(domain, beatscript, classifiers, history, means, vars):
    boostFeatureLine = ConvertData.getSingleFeatureLineFromFile(beatscript, history, True)
    return distributionOfClassification(domain, boostFeatureLine, classifiers, dist=[0, 0, 0, 0, 0, 0, 0],
                                        means=means, vars=vars)


def classifyForCutting(domain, beatscript, classifiers, history, means, vars):
    featureLine = ConvertData.getSingleFeatureLineFromFile(beatscript, history, False)
    return distributionOfClassification(domain, featureLine, classifiers, dist=[0, 0], means=means, vars=vars)


def calculateDistributionAndClassification(classifier, domain, context, blocks, decisions, means, vars, shot_or_cut=True, returnQueue=None):
    """
    Calculates a distribution using the given classifier. From that distribution the highest Value is selected as
     classification. Both distribution and classification are returned.
    """
    datum = getTestExample(domain, context, blocks, decisions, shot_or_cut)
    datum = normalizeData(domain, orange.ExampleTable([datum]), means, vars)[0]
    distribution = classifier(datum, classifier.GetProbabilities)
    classification = orange.Value(distribution.values().index(max(distribution)), domain.class_var)
    if returnQueue:
        returnQueue.put((distribution, classification))
        returnQueue.close()
    return distribution, classification


def calculateBoostingFromDistributions(domain, tree_distribution, svm_distribution):
    """
    Calculates a new classification based on the given tree_distribution and svm_distribution.
     The Used weighting is 3:2.
    """
    dist = []
    for i in range(len(tree_distribution)):
        dist.append(0.6 * tree_distribution[i] + 0.4 * svm_distribution[i])
    return orange.Value(dist.index(max(dist)), domain.class_var)


def XValidation(files, C=0.79):
    """
    Since the decisions of the classifiers during classifying a beatscript are used this is not a classical
     cross-validation. Instead the training is done with all but one Training files and the remaining beatscript
     is tested based on the classification from that data. This process is repeated with all files.
    This function tests the performance for boosted decisions using a treeLearner and a svmLearner.
    """
    domain = getDomain(orange.EnumVariable(name="Shot", values=SHOT_NAMES))
    reference_data = getTrainingExamples(domain, TRAIN_FILES, True)
    means, vars = getNormalizationTerms(reference_data)
    correct_histogram = [0, 0, 0, 0, 0, 0, 0]
    guessed_histogram = [0, 0, 0, 0, 0, 0, 0]
    performances = []
    medium_shot_performances = []
    for file in files:
        print("X-Validation: ca. " + str(int(round(float(files.index(file)) / len(files) * 100))) +
              "% fertig.")
        training_set = [f for f in files if f != file]
        training_data = getTrainingExamples(domain, training_set, True)
        training_data = normalizeData(domain, training_data, means, vars)
        print("Trainingsdaten erzeugt. Trainiere Classifier...")
        print_lock = Lock()
        svm_queue = Queue(maxsize=1)
        svm_learning_process = Process(target=trainSVM, args=(training_data, svm_queue, print_lock, C))
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
            part_blockList.append(block)
            svm_queue = Queue(maxsize=1)
            svm_classification_process = Process(target=calculateDistributionAndClassification,
                args=(trained_svm, domain, deepcopy(context), part_blockList, decisions, means, vars, True, svm_queue))
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
            decisions.append(boost_classification)
            #print("Tree Classification:\t" + tree_classification.value)
            print("SVM Classification:\t" + svm_classification.value)
            #print("Boosted Classification:\t" + boost_classification.value)
            guessed_histogram[SHOT_NAMES.index(boost_classification.value)] += 1
            print("Correct Class:\t\t" + SHOT_NAMES[block[-1].shot])
            correct_histogram[block[-1].shot] += 1
            if boost_classification.value == SHOT_NAMES[block[-1].shot]:
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


def excludedScriptLearnerComparison(domain, files, featureleaveout=-1):
    shot = orange.EnumVariable(name="Shot", values=SHOT_NAMES)
    treePerformances = []
    #ruleLearnerPerformances = []
    svmPerformances = []
    boostedPerformances = []
    correctHistogram = [0, 0, 0, 0, 0, 0, 0]
    guessHistogram = [0, 0, 0, 0, 0, 0, 0]
    wrongcuts = 0
    correctcuts = 0
    wrongcuts_hand = 0
    correctcuts_hand = 0
    real_cut_no = 0
    calculated_cut_no = 0
    #for i in range(3,len(files)): del files[-1]
    for file in files:
        print("excludedScriptLearnerComparison: " + str(int(round(float(files.index(file)) / len(files) * 100))) +
              "% fertig.")
        trainingSet = []
        for f in files:
            if f != file: trainingSet.append(f)
        testSet = [file]
        trainingData = getTrainingExamples(domain, trainingSet, True, featureleaveout)
        referenceData = getTrainingExamples(domain, TRAIN_FILES, shot, featureleaveout)
        means, vars = getNormalizationTerms(referenceData)
        trainingData = normalizeData(domain, trainingData, means, vars)
        cutTrainingData = getTrainingExamples(getDomain(orange.EnumVariable(name="Cut", values=['True', 'False']), featureleaveout),
                                              trainingSet, False, featureleaveout)
        cutTrainingData = normalizeData(getDomain(orange.EnumVariable(name="Cut", values=['True', 'False']), featureleaveout),
                                        cutTrainingData, means, vars)
        lock = Lock()
        treeReturnQueue = Queue()
        treeLearningProcess = Process(target=trainTree, args=(trainingData, treeReturnQueue, lock))
        treeLearningProcess.start()
        cutReturnQueue = Queue()
        cutLearningProcess = Process(target=trainSVM, args=(cutTrainingData, cutReturnQueue, lock))
        cutLearningProcess.start()
        #ruleReturnQueue = Queue()
        #ruleLearningProcess = Process(target=trainRule, args=(lock, trainingData, ruleReturnQueue))
        #ruleLearningProcess.start()
        svmReturnQueue = Queue()
        svmLearningProcess = Process(target=trainSVM, args=(trainingData, svmReturnQueue, lock))
        svmLearningProcess.start()
        treeCorrect = 0
        #ruleLearnerCorrect = 0
        svmCorrect = 0
        boostCorrect = 0
        blockCount = 0
        tree = treeReturnQueue.get()
        cutClassifier = cutReturnQueue.get()
        #ruleLearningClassifier = ruleReturnQueue.get()
        svmClassifier = svmReturnQueue.get()
        treeLearningProcess.join()
        cutLearningProcess.join()
        #ruleLearningProcess.join()
        svmLearningProcess.join()
        for testFile in testSet:
            testData = getTestExamples(domain, testFile, True, featureleaveout)
            treeDecisions = []
            #ruleDecisions = []
            svmDecisions = []
            boostDecisions = []
            # read test file
            context, beatList = getContextAndBeatListFromFile(file)
            blockList = coalesceBeats(beatList)

            for i in range(len(testData)):
                treeClassificationReturnQueue = Queue()
                treeClassify = Process(target=classification,
                                       args=(tree, deepcopy(context), blockList, domain, treeDecisions, means, vars,
                                             treeClassificationReturnQueue, True, featureleaveout))
                treeClassify.start()
                cutClassificationReturnQueue = Queue()
                cutClassify = Process(target=classification,
                                      args=(cutClassifier, deepcopy(context), blockList,
                                            getDomain(orange.EnumVariable(name="Cut", values=['True', 'False']), featureleaveout),
                                            boostDecisions, means, vars,
                                            cutClassificationReturnQueue, False, featureleaveout))
                cutClassify.start()
                #ruleClassificationReturnQueue = Queue()
                #ruleClassify = Process(target=classification,
                #                       args=(ruleLearningClassifier, testFile, domain, ruleDecisions, means, vars,
                #                             ruleClassificationReturnQueue, True))
                #ruleClassify.start()
                svmClassificationReturnQueue = Queue()
                svmClassify = Process(target=classification,
                                      args=(svmClassifier, deepcopy(context), blockList, domain, svmDecisions, means, vars,
                                            svmClassificationReturnQueue, True, featureleaveout))
                svmClassify.start()
                boostFeatureLine = ConvertData.getSingleFeatureLine(deepcopy(context), blockList, boostDecisions, True, featureleaveout)
                boostDatum = orange.Example(domain, boostFeatureLine)
                boostDatum = normalizeDatum(boostDatum, means, vars)
                cutFeatureLine = ConvertData.getSingleFeatureLine(deepcopy(context), blockList, boostDecisions, False, featureleaveout)
                cutDatum = orange.Example(getDomain(orange.EnumVariable(name="Cut", values=['True', 'False']), featureleaveout),
                                          cutFeatureLine)
                cutDatum = normalizeDatum(cutDatum, means, vars)
                treeDistributionReturnQueue = Queue()
                computeTreeDistribution = Process(target=distribution,
                                                  args=(tree, boostDatum, treeDistributionReturnQueue))
                computeTreeDistribution.start()
                #ruleDistributionReturnQueue = Queue()
                #computeRuleDistribution = Process(target=distribution,
                #                                  args=(
                #                                      ruleLearningClassifier, boostDatum, ruleDistributionReturnQueue))
                #computeRuleDistribution.start()
                svmDistributionReturnQueue = Queue()
                computeSVMDistribution = Process(target=distribution,
                                                 args=(svmClassifier, boostDatum, svmDistributionReturnQueue))
                computeSVMDistribution.start()
                dist = [0, 0, 0, 0, 0, 0, 0]
                treeClassification = treeClassificationReturnQueue.get()
                #ruleLearnerClassification = ruleClassificationReturnQueue.get()
                ruleLearnerClassification = treeClassification
                svmClassification = svmClassificationReturnQueue.get()
                treeDistribution = treeDistributionReturnQueue.get()
                #ruleDistribution = ruleDistributionReturnQueue.get()
                svmDistribution = svmDistributionReturnQueue.get()
                computeTreeDistribution.join()
                #computeRuleDistribution.join()
                computeSVMDistribution.join()
                #treeDistribution = smoothDistribution(treeDistribution)
                #svmDistribution = smoothDistribution(svmDistribution)
                for i in range(0, 7):
                    #dist[i] = (treeDistribution[i] * 0.39 + ruleDistribution[i] * 0.33 + svmDistribution[i] * 0.28)
                    #dist[i] = (treeDistribution[i] * 0.60 * (svmDistribution[i] *0.8 + 0.2) +
                    #           svmDistribution[i] * 0.40 * (treeDistribution[i] *0.8 + 0.2))
                    dist[i] = (treeDistribution[i] * 0.60 + svmDistribution[i] * 0.40)
                dist = smoothDistribution(dist)
                treeClassify.join()
                #ruleClassify.join()
                svmClassify.join()
                treeDecisions.append(treeClassification)
                #ruleDecisions.append(ruleLearnerClassification)
                svmDecisions.append(svmClassification)
                boostDecisions.append(orange.Value(shot, SHOT_NAMES[dist.index(max(dist))]))
                if boostDatum.getclass() == treeClassification: treeCorrect += 1
                #print("Original:\t" + str(boostDatum.getclass())+"\tTree:\t" + str(treeClassification))
                if boostDatum.getclass() == svmClassification: svmCorrect += 1
                #if boostDatum.getclass() == ruleLearnerClassification: ruleLearnerCorrect += 1
                if boostDatum.getclass() == orange.Value(shot, SHOT_NAMES[dist.index(max(dist))]): boostCorrect += 1
                correctHistogram[SHOT_NAMES.index(boostDatum.getclass())] += 1
                guessHistogram[dist.index(max(dist))] += 1
                cutClassification = cutClassificationReturnQueue.get()
                cutClassify.join()
                print("Schnitt? " + str(cutClassification))
                print("Schnitt: " + str(cutDatum.getclass()))
                if str(cutDatum.getclass()) != cutClassification: wrongcuts += 1
                else: correctcuts += 1
                if "False" == str(cutDatum.getclass()): real_cut_no += 1
                # Vor diesem Block schneiden? Performance das Handalgorithmus
                if len(boostDecisions) >= 2:
                    keepingPropability = dist[SHOT_NAMES.index(str(boostDecisions[-2]))]
                else:
                    keepingPropability = 1.0
                shouldHandCut = True
                if not cutBeforeThisBlock(ConvertData.getDecidedBlockListFromFile(testFile, boostDecisions),
                                          boostDecisions, keepingPropability) and len(boostDecisions) >= 2:
                    calculated_cut_no += 1
                    shouldHandCut = False
                if str(cutDatum.getclass()) != str(shouldHandCut): wrongcuts_hand += 1
                else: correctcuts_hand += 1

                #if "False" == str(cutClassification) and len(boostDecisions) >= 2:
                #    del boostDecisions[-1]
                #    boostDecisions.append(boostDecisions[-1])
                if testData[i].getclass() != treeClassification or\
                   testData[i].getclass() != ruleLearnerClassification or\
                   testData[i].getclass() != svmClassification:
                    print("Boosted probabilities: " +
                          str(int(round(dist[0] * 100))) + "%\t" + str(int(round(dist[1] * 100))) + "%\t" +
                          str(int(round(dist[2] * 100))) + "%\t" + str(int(round(dist[3] * 100))) + "%\t" +
                          str(int(round(dist[4] * 100))) + "%\t" + str(int(round(dist[5] * 100))) + "%\t" +
                          str(int(round(dist[6] * 100))) + "%\t")
                    print("Original:\t" + str(testData[i].getclass()))
                    print("Boosted:\t" + SHOT_NAMES[dist.index(max(dist))])
                    print("Tree:\t\t" + str(treeClassification))
                    #print("Rule:\t\t" + str(ruleLearnerClassification))
                    print("SVM:\t\t" + str(svmClassification))
                blockCount += 1
        treePerformances.append(float(treeCorrect) / blockCount)
        #ruleLearnerPerformances.append(float(ruleLearnerCorrect) / blockCount)
        svmPerformances.append(float(svmCorrect) / blockCount)
        boostedPerformances.append(float(boostCorrect) / blockCount)
        print("Performance:\tTree: " + str(float(treeCorrect) / float(blockCount)))
        #print("Performance:\tRule: " + str(float(ruleLearnerCorrect) / float(blockCount)))
        print("Performance:\tSVM: " + str(float(svmCorrect) / float(blockCount)))
        print("Performance:\tBoost: " + str(float(boostCorrect) / float(blockCount)))
    sum = 0.0
    last = 1.0
    best = 0.0
    for p in treePerformances:
        sum += p
        if p > best: best = p
        if p < last: last = p
    print("Tree Performance:\t\t" + str(sum / len(treePerformances)) + " (" + str(last) + " - " + str(best) + ")")
    #sum = 0.0
    #last = 1.0
    #best = 0.0
    #for p in ruleLearnerPerformances:
    #    sum += p
    #    if p > best: best = p
    #    if p < last: last = p
    #print("Rule Learner Performance:\t\t" + str(sum / len(ruleLearnerPerformances)) + " (" + str(last) + " - " + str(
    #    best) + ")")
    sum = 0.0
    last = 1.0
    best = 0.0
    for p in svmPerformances:
        sum += p
        if p > best: best = p
        if p < last: last = p
    print("SVM Performance:\t\t" + str(sum / len(svmPerformances)) + " (" + str(last) + " - " + str(best) + ")")
    sum = 0.0
    last = 1.0
    best = 0.0
    for p in boostedPerformances:
        sum += p
        if p > best: best = p
        if p < last: last = p
    print("Boosted Performance:\t\t" + str(sum / len(boostedPerformances)) + " (" + str(last) + " - " + str(best) + ")")
    print(correctHistogram)
    print(guessHistogram)
    print("Cut-classifier rate:\t" + str(int(round(100.0 * correctcuts / (correctcuts + wrongcuts)))) + "%")
    print(str(wrongcuts) +
          " falsche Schnitte beim Classifier (" + str(correctcuts + wrongcuts) + " Schnitte insgesamt).")
    print("Cut-decision by hand rate:\t" + str(
        int(round(100.0 * correctcuts_hand / (correctcuts_hand + wrongcuts_hand)))) + "%")
    print(str(wrongcuts_hand) +
          " falsche Schnitte beim Algorithmus (" + str(correctcuts_hand + wrongcuts_hand) + " Schnitte insgesamt).")
    print(str(real_cut_no) + " mal sollte nicht geschnitten werden. " + str(
        calculated_cut_no) + " mal wurde nicht geschnitten.")
    return sum / len(boostedPerformances)

# =============================== Main =========================================
def main():
    results = []
    domain = getDomain(orange.EnumVariable(name="Shot", values=SHOT_NAMES))
    boostedPerformace = excludedScriptLearnerComparison(domain, TRAIN_FILES)
    results.append(str(boostedPerformace))
    #for i in range(0,118):
    #    featureleaveout = i
    #    domain = getDomain(orange.EnumVariable(name="Shot", values=SHOT_NAMES), featureleaveout)
    #    boostedPerformace = excludedScriptLearnerComparison(domain, TRAIN_FILES, featureleaveout)
    #    results.append(str(boostedPerformace))
    print("==============================================")
    print("  ")
    print("  ")
    print("  ")
    for line in results:
        print(line)

def new_main():
    f = open("C-Performances.csv",'w')
    for i in range(1,100):
        f.write(str(float(i)/100)+","+str(XValidation(TRAIN_FILES,float(i)/100)))
    f.close()


if __name__ == "__main__":
    new_main()
    #main()