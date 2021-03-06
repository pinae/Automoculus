#!/usr/bin/python
# -*- coding: utf-8 -*- 

# =============================== Imports ======================================
from copy import deepcopy
import random
import sys

import Features

from Config import SHOT_NAMES
from Config import SAYS
from Config import DELIMITER
from Beatscript import Beat, createContext, readContext, readBeatscript, coalesceBeats
from Beatscript import getContextAndBeatListFromFile


def createDataLine(context, block, leaveout=-1):
    dataLine = [str(block[0].shotId) + "_" + str(block[0].beatId), str(block[0].shot)]
    featureClassList = Features.getAllFeatureClasses()
    context = Features.createBeatList(context, block)
    for featureClass in featureClassList:
        feature = featureClass(context, block)
        dataLine += feature.getNumbers()
        # activate to generate a human readable featureLine
        #dataLine.append(feature.getText())
    if leaveout >= 0:
        dataLine.pop(leaveout)
    return dataLine


def getFeatureLine(context, block, shot, lastShotId, leave_out_class=None):
    """
    This function creates a featureLine. This is done by calculating getNumbers() for
    all Feature-Classes in Features.py and appending the desired class. A featureLine
    consists of several Numbers and a String at the end for the class.
    """
    line = []
    featureClassList = Features.getAllFeatureClasses()
    context = Features.createBeatList(context, block)
    # use all features except leave_out_class if given
    #for featureClass in [x for x in featureClassList if x != leave_out_class]:
    # use only features which contribute significant information
    for featureClass in [featureClassList[x] for x in range(len(featureClassList)) if
                         x in [9, 10, 11, 12, 13, 15, 19, 25, 27, 28, 30, 31, 32, 33, 37,
                               39, 41, 42]]:
        feature = featureClass(context, block)
        line += feature.getNumbers()
    if shot:
        line.append(SHOT_NAMES[block[0].shot])
    else:#is there a cut?
        line.append(str(lastShotId != block[0].shotId))
    return line


def getFeatureNames(leave_out_class=None):
    """
    Returns an array of feature names corresponding to the featureLine.
    """
    names = []
    featureClassList = Features.getAllFeatureClasses()
    context = createContext()
    dummy_beat = Beat("0_1\tfull_shot\tfalse\tintroduce\tperson§Nobody", context)
    context = Features.createBeatList(context, [dummy_beat])
    Features.initializeContextVars(context)
    for featureClass in [x for x in featureClassList if x != leave_out_class]:
        feature = featureClass(context, [dummy_beat])
        names += feature.getNames()
    return names


def createFeatureLines(context, beatList, shot, leave_out_class=None):
    """
    Returns the list of featureLines converted from the Beats in beatList
    """
    featureLines = []
    blockList = coalesceBeats(beatList)
    Features.initializeContextVars(context)
    lastShotId = -1
    for block in blockList:
        featureLines.append(
            getFeatureLine(context, block, shot, lastShotId, leave_out_class))
        context["BygoneBlocks"].append(block)
        lastShotId = block[-1].shotId
    return featureLines


def getFeatureLinesFromFile(file, shot, leave_out_class=None):
    """
    Returns a list of featureLines converted from the beatscript given in file.
    """
    context, beatList = getContextAndBeatListFromFile(file)
    return createFeatureLines(context, beatList, shot, leave_out_class)


def getFeatureLinesFromFileAndModify(file, shot, leave_out=-1):
    """
    Creates featureLines by blowing up the data with duplicating SAYS in some
    cases. This rapidly increases training times.
    """
    context, beatList = getContextAndBeatListFromFile(file)
    originalList = deepcopy(beatList)
    for i in range(0, 2):
        for beat in originalList:
            beatList.append(beat)
            if beat.type == SAYS:
                if random.randint(0, 1):
                    beatList.append(beat)
    return createFeatureLines(context, beatList, shot, leave_out)


def applyDecisionsToBeatscript(context, blockList, decisions):
    """
    Applys the decisions to all Beats in the blockList. BygoneBlocks are updated
    during that process.
    """
    lastShotId = -1
    context["BygoneBlocks"] = []
    for i, decision in enumerate(decisions):
        block = blockList[i]
        for beat in block:
            beat.shot = decision
        context["BygoneBlocks"].append(block)
        lastShotId = block[-1].shotId
    return lastShotId, context, blockList


def getSingleFeatureLineFromFile(file, decisions, shot, leave_out_class=None):
    """
    This is a less troublesome but slow method to get a featureLine.
    """
    beatList, context = getContextAndBeatListFromFile(file)
    blockList = coalesceBeats(beatList)
    Features.initializeContextVars(context)
    lastShotId, context, blockList = applyDecisionsToBeatscript(context, blockList,
        decisions)
    featureLine = getFeatureLine(context, blockList[len(decisions)], shot, lastShotId,
        leave_out_class)
    return featureLine


def getSingleFeatureLine(context, blockList, decisions, shot, leave_out_class=None):
    """
    Returns a featureLine based on the context and the decisions.
    """
    Features.initializeContextVars(context)
    lastShotId, context, blockList = applyDecisionsToBeatscript(context, blockList,
        decisions)
    # This is for preventing the classifier to cheat by using the correct class.
    # Activate if you're suspicious.
    #for beat in blockList[len(decisions)]:
    #    beat.shot = 0
    featureLine = getFeatureLine(context, blockList[len(decisions)], shot, lastShotId,
        leave_out_class)
    return featureLine

# =============================== Main =========================================
def main():
    beatscriptFile = open(sys.argv[1], "r")
    lines = beatscriptFile.readlines()
    context = readContext(lines)
    beatList = readBeatscript(lines, context)
    blockList = coalesceBeats(beatList)
    Features.initializeContextVars(context)
    dataLines = []
    for block in blockList:
        dataLines.append(createDataLine(context, block))
        context["BygoneBlocks"].append(block)

    outputFile = open(sys.argv[2], "w")
    for dataLine in dataLines:
        outputFile.write(DELIMITER.join([str(x) for x in dataLine]) + "\n")
        #outputFile.write(DELIMITER.join(dataLine) + "\n")
    outputFile.close()

if __name__ == "__main__":
    main()
