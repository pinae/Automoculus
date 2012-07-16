#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================== Imports ======================================
from multiprocessing import Process, Queue, Lock
import pickle
import sys

from sklearn import preprocessing

from Config import TRAIN_FILES, PERSON, OBJECT, PLACE
from Classify import getDataMatrix, trainSVM, classifyForShot
from Beatscript import readContext, readBeatscript, getBeatsBetweenFrames
import Features

# =============================== Methods ======================================
def trainWithAllExamples(shot):
    #if shot: domain = getDomain(orange.EnumVariable(name="Shot", values=SHOT_NAMES))
    #else: domain = getDomain(orange.EnumVariable(name="Cut", values=['True', 'False']))
    #trainingData = getTrainingExamples(domain, TRAIN_FILES, shot)
    #means, vars = getNormalizationTerms(trainingData)
    training_data, training_data_classes = getDataMatrix(TRAIN_FILES, shot)
    scaler = preprocessing.Scaler()
    training_data = scaler.fit_transform(training_data, training_data_classes)
    lock = Lock()
    #treeReturnQueue = Queue()
    #treeLearningProcess = Process(target=trainTree, args=(training_data, training_data_classes, treeReturnQueue, lock))
    #treeLearningProcess.start()
    svmReturnQueue = Queue()
    svmLearningProcess = Process(target=trainSVM, args=(training_data, training_data_classes, svmReturnQueue, lock))
    svmLearningProcess.start()
    #treeClassifier = treeReturnQueue.get()
    svmClassifier = svmReturnQueue.get()
    #treeLearningProcess.join()
    svmLearningProcess.join()
    return (svmClassifier,), scaler


# =============================== Interactions =========================================
def printListOfEntities(context):
    persons = [entity for name, entity in context["Entities"].items() if entity.type == PERSON]
    objects = [entity for name, entity in context["Entities"].items() if entity.type == OBJECT]
    places = [entity for name, entity in context["Entities"].items() if entity.type == PLACE]
    pickle.dump({"Persons" : persons, "Objects" : objects, "Places": places}, sys.stdout)


# =============================== Main =========================================
def determine_targets(context, current_block):
    lineTargets = []
    targets = []
    for beat in current_block:
        if beat.subject not in targets:
            targets.append(beat.subject)
        if beat.linetarget and beat.linetarget not in lineTargets:
            lineTargets.append(beat.linetarget)

    if len(targets) <= 1 and not lineTargets:
        linetarget = targets[0]
        target = targets[0]
        for block in reversed(context["BygoneBlocks"]):
            for beat in reversed(block):
                if beat.linetarget and beat.linetarget != target:
                    linetarget = beat.linetarget
                    break
                elif beat.subject != target:
                    linetarget = beat.subject
                    break
            if target is not linetarget:
                break
    else :
        if lineTargets:
            # get last person in lineTargets as lineTarget
            linetarget = lineTargets[-1]
            for t in reversed(lineTargets):
                if t.type == PERSON:
                    linetarget = t
                    break
        else:
            # trying to get persons as linetargets, because objects and places aren't as important
            linetarget = targets[-1]
            for t in reversed(targets):
                if t.type == PERSON :
                    linetarget = t
                    break

        # make sure linetarget != target
        if linetarget in targets:
            targets.remove(linetarget)

        # trying to get persons as targets, because objects and places aren't as important
        target = targets[-1]
        for t in reversed(targets):
            if t.type == PERSON :
                target = t
                break

        # switch target and linetarget, if only linetarget of the two is a person
        if linetarget.type == PERSON and target.type != PERSON:
            target, linetarget = linetarget, target

    # write
    sys.stdout.write(target.name + "\t" + linetarget.name + "\n")


def main():
    # Initialization and Training
    #cutClassifiers, means, vars = trainWithAllExamples(False)
    classifiers, scaler = trainWithAllExamples(True)
    #shot = orange.EnumVariable(name="Shot", values=SHOT_NAMES)
    #domain = getDomain(shot)
    #cut_domain = getDomain(orange.EnumVariable(name="Cut", values=['True', 'False']))
    beatscript_file = open(sys.argv[1], "r")
    lines = beatscript_file.readlines()
    context = readContext(lines)#
    beatscript = readBeatscript(lines, context)
    Features.initializeContextVars(context)
    beatList = getBeatsBetweenFrames(beatscript, -1, 0)
    current_frame = 0
    lastBlock = beatList
    context["BygoneBlocks"] = []
    sys.stdout.write("Training finished." + "\n")
    sys.stdout.flush()
    # Get Distribution
    dist = classifyForShot(lastBlock, context, classifiers, scaler)
    #cutBeforeThisClassification = classifyForCut(
    #                getDomain(orange.EnumVariable(name="Cut", values=['True', 'False'])), lastBlock, context,
    #                cutClassifiers, means, vars)
    #sys.stdout.write(distToStr(dist) + "\n")
    #sys.stdout.flush()
    while True:
        choice = raw_input("")
        if choice == "e":
            printListOfEntities(context)
        elif choice == "t": # get the names of the target and the linetarget
            determine_targets(context, lastBlock)
        elif choice == "p": # print out the classification propabilities
            pickle.dump(dist, sys.stdout)

        elif choice == "c": # Print out, if we should cut at this point
            blockList = []
            decisions = []
            for block in context["BygoneBlocks"]:
                blockList.append(block)
                decisions.append(block[0].shot)
            blockList.append(lastBlock)
            decisions.append(dist.index(max(dist)))
            #if len(decisions) >= 2:
            #        keepingPropability = dist[SHOT_NAMES.index(str(decisions[-2]))]
            #else:
            #        keepingPropability = 1.0
            #if cutBeforeThisBlock(blockList, decisions, keepingPropability):
            if True:
            #if cutBeforeThisClassification[0] > cutBeforeThisClassification[1]:
                sys.stdout.write("yes\n")
            else:
                sys.stdout.write("no\n")

        elif choice == "f": # check framenumber for a new block
            new_frame = int(raw_input(""))
            beatList = getBeatsBetweenFrames(beatscript, current_frame, new_frame)
            current_frame = new_frame
            if beatList :
                context["BygoneBlocks"].append(lastBlock)
                lastBlock = beatList
                dist = classifyForShot(lastBlock, context, classifiers, scaler)
                #cutBeforeThisClassification = classifyForCut(cut_domain, lastBlock, context, cutClassifiers, means, vars)
                sys.stdout.write("yes\n")
            else:
                sys.stdout.write("no\n")

        elif choice == "d": # recieve the decision for the lastBlock
            decision = int(raw_input(""))
            for beat in lastBlock:
                beat.shot = decision
            sys.stdout.write("decision recieved\n")

        elif choice == "q": # quit...
            sys.stdout.write("exiting...\n")
            sys.stdout.flush()
            break
        else:
            sys.stdout.write("You didn't enter something useful.\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
