#!/usr/bin/python
# -*- coding: utf-8 -*- 

# =============================== Imports ======================================
#import inspect
#import os
import random
import sys

import Features

from Config import SHOT_NAMES
from Config import SAYS
from Config import DELIMITER
from Beatscript import Beat, createContext, readContext, readBeatscript, coalesceBeats, getContextAndBeatListFromFile, getBlockList


def createDataLine(context, block, leaveout=-1):
    dataLine = [str(block[0].shotId) + "_" + str(block[0].beatId), str(block[0].shot)]
    featureClassList = Features.getAllFeatureClasses()
    context = Features.createBeatlist(context, block)
    for featureClass in featureClassList:
        #print featureClass.__name__
        feature = featureClass(context, block)
        dataLine += feature.getNumbers()
        #dataLine.append(feature.getText())
    if leaveout >= 0:
        dataLine.pop(leaveout)
    return dataLine


def getFeatureLine(context, block, shot, lastShotId, leaveout=-1):
    '''
    This Function creates a featureLine. This is done by calculating getNumbers() for all Feature-Classes in
     Features.py and appending the desired class. A featureLine consists of several Numbers and a String at the
     end for the class.
    '''
    line = []
    featureClassList = Features.getAllFeatureClasses()
    context = Features.createBeatlist(context, block)
    for featureClass in featureClassList:
        feature = featureClass(context, block)
        line += feature.getNumbers()
    if leaveout >= 0:
        line.pop(leaveout)
    if shot:
        line.append(SHOT_NAMES[block[0].shot])
    else:#is there a cut?
        line.append(str(lastShotId != block[0].shotId))
    return line


def getFeatureNames(leaveout=-1):
    names = []
    featureClassList = Features.getAllFeatureClasses()
    context = createContext()
    dummybeat = Beat("0_1	full_shot	false	introduce	person§Nobody", context)
    context = Features.createBeatlist(context, [dummybeat])
    Features.initializeContextVars(context)
    for featureClass in featureClassList:
        feature = featureClass(context, [dummybeat])
        names += feature.getNames()
        #print(len(names))
    #print(names[0])
    if leaveout >= 0:
        names.pop(leaveout)
    return names


def createFeatureLines(context, beatList, shot, leaveout=-1):
    '''
    Returns the list of featureLines converted from the Beats in beatList
    '''
    featureLines = []
    blockList = coalesceBeats(beatList)
    Features.initializeContextVars(context)
    lastShotId = -1
    for block in blockList:
        featureLines.append(getFeatureLine(context, block, shot, lastShotId, leaveout))
        context["BygoneBlocks"].append(block)
        lastShotId = block[-1].shotId
    return featureLines


def getFeatureLinesFromFile(file, shot, leaveout=-1):
    '''
    Returns a list of featureLines converted from the beatscript given in file.
    '''
    context, beatList = getContextAndBeatListFromFile(file)
    return createFeatureLines(context, beatList, shot, leaveout)


def getFeatureLinesFromFileAndModify(file, shot):
    context, beatList = getContextAndBeatListFromFile(file)
    originalList = []
    for beat in beatList:
        originalList.append(beat)
    for i in range(0, 2):
        for beat in originalList:
            beatList.append(beat)
            if beat.type == SAYS:
                if random.randint(0, 1):
                    beatList.append(beat)
    return createFeatureLines(context, beatList, shot)


def getDecidedBlockListFromFile(file, decisions):
    beatscriptFile = open(file, "r")
    lines = beatscriptFile.readlines()
    context = readContext(lines)
    blockList = getBlockList(lines, context)
    relevantBlockList = []
    for i in range(0, len(decisions)):
        block = blockList[i]
        for beat in block:
            beat.shot = Beat.shotType[decisions[i].value]
        relevantBlockList.append(block)
    return relevantBlockList


def applyDecisionsToBeatscript(context, blockList, decisions):
    """
    Applys the decisions to all Beats in the blockList. BygoneBlocks are updated during that process.
    """
    lastShotId = -1
    context["BygoneBlocks"] = []
    for i, decision in enumerate(decisions):
        block = blockList[i]
        for beat in block:
            beat.shot = Beat.shotType[decision.value]
        context["BygoneBlocks"].append(block)
        lastShotId = block[-1].shotId
    return lastShotId, context, blockList


def getSingleFeatureLineFromFile(file, decisions, shot, leave_out=-1):
    beatList, context = getContextAndBeatListFromFile(file)
    blockList = coalesceBeats(beatList)
    Features.initializeContextVars(context)
    lastShotId, context, blockList = applyDecisionsToBeatscript(context, blockList, decisions)
    featureLine = getFeatureLine(context, blockList[len(decisions)], shot, lastShotId, leave_out)
    return featureLine

def getSingleFeatureLine(context, blockList, decisions, shot, leave_out=-1):
    '''
    Returns a featureLine based on the context and the decisions.
    '''
    Features.initializeContextVars(context)
    lastShotId, context, blockList = applyDecisionsToBeatscript(context, blockList, decisions)
    featureLine = getFeatureLine(context, blockList[len(decisions)], shot, lastShotId, leave_out)
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
