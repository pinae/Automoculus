#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================== Imports ======================================
from multiprocessing import Process, Queue, Lock
#import cPickle
import orange#, orngTree
from Config import SHOT_NAMES, TRAIN_FILES, DETAIL, PERSON, OBJECT, PLACE
from Classify import getDomain, getTrainingExamples, trainTree, trainSVM, classifyForShot#, trainRule
from Classify import getNormalizationTerms, classifyForCut
#from Classify import cutBeforeThisBlock
import sys
from ConvertData import readContext, readBeatscript
import Features
import pickle

# =============================== Methods ======================================
def trainWithAllExamples(shot):
    if shot: domain = getDomain(orange.EnumVariable(name="Shot", values=SHOT_NAMES))
    else: domain = getDomain(orange.EnumVariable(name="Cut", values=['True', 'False']))
    trainingData = getTrainingExamples(domain, TRAIN_FILES, shot)
    means, vars = getNormalizationTerms(domain, shot)
    lock = Lock()
    treeReturnQueue = Queue()
    treeLearningProcess = Process(target=trainTree, args=(lock, trainingData, treeReturnQueue))
    treeLearningProcess.start()
    #ruleReturnQueue = Queue()
    #ruleLearningProcess = Process(target=trainRule, args=(lock, trainingData, ruleReturnQueue))
    #ruleLearningProcess.start()
    svmReturnQueue = Queue()
    svmLearningProcess = Process(target=trainSVM, args=(lock, trainingData, svmReturnQueue))
    svmLearningProcess.start()
    treeClassifier = treeReturnQueue.get()
    #ruleLearningClassifier = ruleReturnQueue.get()
    svmClassifier = svmReturnQueue.get()
    treeLearningProcess.join()
    #ruleLearningProcess.join()
    svmLearningProcess.join()
    #file = open(filename, 'wb')
    #cPickle.Pickler(file, cPickle.HIGHEST_PROTOCOL).dump((treeClassifier, ruleLearningClassifier, svmClassifier))
    #file.close()
    #return treeClassifier, ruleLearningClassifier, svmClassifier
    return (treeClassifier, svmClassifier), means, vars


def distToStr(dist):
    return "\t".join([str(x) for x in dist])


def readBeatscriptTillFrame(lines, context, frameno):
    wholeList = readBeatscript(lines, context)
    beatList = []
    for beat in wholeList:
        if beat.shotId <= frameno:
            beatList.append(beat)
    return beatList


def sameBeat(beat1, beat2):
    if beat1.shotId != beat2.shotId: return False
    elif beat1.beatId != beat2.beatId: return False
    elif beat1.shot != beat2.shot: return False
    elif beat1.invisible != beat2.invisible: return False
    elif beat1.type != beat2.type: return False
    elif beat1.subject != beat2.subject: return False
    elif beat1.linetarget != beat2.linetarget: return False
    else: return True

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
    cutClassifiers, means, vars = trainWithAllExamples(False)
    classifiers, means, vars = trainWithAllExamples(True)
    shot = orange.EnumVariable(name="Shot", values=SHOT_NAMES)
    domain = getDomain(shot)
    beatscriptFile = open(sys.argv[1], "r")
    lines = beatscriptFile.readlines()
    context = readContext(lines)
    Features.initializeContextVars(context)
    beatList = readBeatscriptTillFrame(lines, context, 0)
    for beat in beatList:
        beat.shot = DETAIL
    lastBlock = beatList
    context["BygoneBlocks"] = []
    sys.stdout.write("Training finished." + "\n")
    sys.stdout.flush()
    # Get Distribution
    dist = classifyForShot(domain, lastBlock, context, classifiers, means, vars)
    cutBeforeThisClassification = classifyForCut(
                    getDomain(orange.EnumVariable(name="Cut", values=['True', 'False'])), lastBlock, context,
                    cutClassifiers, means, vars)
    #sys.stdout.write(distToStr(dist) + "\n")
    #sys.stdout.flush()
    while True:
        choice = raw_input("")
        if choice == "e":
            printListOfEntities(context)
        elif choice == "t": # get the names of the target and the linetarget
            determine_targets(context, lastBlock)
        elif choice == "p": # print out the classification propabilities
            sys.stdout.write(distToStr(dist) + "\n")

        elif choice == "c": # Print out, if we should cut at this point
            blockList = []
            decisions = []
            for block in context["BygoneBlocks"]:
                blockList.append(block)
                decisions.append(orange.Value(shot, SHOT_NAMES[block[0].shot]))
            blockList.append(lastBlock)
            decisions.append(orange.Value(shot, SHOT_NAMES[dist.index(max(dist))]))
            #if len(decisions) >= 2:
            #        keepingPropability = dist[SHOT_NAMES.index(str(decisions[-2]))]
            #else:
            #        keepingPropability = 1.0
            #if cutBeforeThisBlock(blockList, decisions, keepingPropability):
            if cutBeforeThisClassification == "True":
                sys.stdout.write("yes\n")
            else:
                sys.stdout.write("no\n")

        elif choice == "f": # check framenumber for a new block
            beatList = readBeatscriptTillFrame(lines, context, int(raw_input("")))
            for block in context["BygoneBlocks"]:
                for _ in block:
                    if len(beatList) > 0:
                            del beatList[0]
            for _ in lastBlock:
                if len(beatList) > 0:
                        del beatList[0]
            if len(beatList) > 0:
                for beat in beatList: #Um sicher zu gehen, dass hier nicht beschissen wird.
                    beat.shot = DETAIL
                context["BygoneBlocks"].append(lastBlock)
                lastBlock = beatList
                dist = classifyForShot(domain, lastBlock, context, classifiers, means, vars)
                cutBeforeThisClassification = classifyForCut(
                    getDomain(orange.EnumVariable(name="Cut", values=['True', 'False'])), lastBlock, context,
                    cutClassifiers, means, vars)
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
