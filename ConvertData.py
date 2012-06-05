#!/usr/bin/python
# -*- coding: utf-8 -*- 

# =============================== Imports ======================================
#import inspect
#import os
import random
import sys

import Features
from Config import DETAIL, CLOSEUP, MEDIUM_SHOT, AMERICAN_SHOT, FULL_SHOT, LONG_SHOT, EXTREME_LONG_SHOT
from Config import SHOT_NAMES
#from Config import BEAT_TYPE_NAMES, DEMONSTRAT_TYPE_NAMES
from Config import INTRODUCE, EXPRESS, SAYS, ACTION, SHOW
from Config import PERSON, OBJECT, PLACE
from Config import DELIMITER

# =============================== Datatypes ====================================
class Entity:
    entityType = {"person": PERSON, "object": OBJECT, "place": PLACE}

    def __init__(self, text):
        splitText = text.split("§")
        self.type = self.entityType[splitText[0]]
        self.name = splitText[1]


class Beat:
    beatType = {"introduce": INTRODUCE, "expresses": EXPRESS, "says": SAYS, "action": ACTION,
                "show": SHOW}
    shotType = {"detail": DETAIL, "closeup": CLOSEUP, "medium_shot": MEDIUM_SHOT,
                "american_shot": AMERICAN_SHOT, "full_shot": FULL_SHOT, "long_shot": LONG_SHOT,
                "extreme_long_shot": EXTREME_LONG_SHOT}

    def __init__(self, text, context):
        splitText = text.split("\t", 5)
        splitId = splitText[0].split("_")
        self.shotId = int(splitId[0])
        self.beatId = int(splitId[1])
        self.shot = self.shotType[splitText[1]]
        if splitText[2].strip() == "true": invisible = True
        else: invisible = False
        self.invisible = invisible
        self.type = self.beatType[splitText[3]]
        self.subject = entityFactory(splitText[4], context)
        self.linetarget = False
        if self.type == SAYS:
            linetargetText = splitText[5].strip('\t').split("\t")[1]
            if len(linetargetText) >= 8:
                self.linetarget = entityFactory(linetargetText, context)

# =============================== Methods ======================================

def createContext():
    context = {"Entities": {}, "KnownEntities": set(), "BygoneBlocks": [], "protagonist": False, "MainCharacters": [],
               "ExpositoryPhase": True}
    return context


def entityFactory(entityText, context):
    newEntity = Entity(entityText)
    if newEntity.name not in context["Entities"]:
        context["Entities"][newEntity.name] = newEntity
    return context["Entities"][newEntity.name]


def addEntityList(context, entityListLine):
    for entityText in entityListLine.split(","):
        entityStr = entityText.strip()
        if len(entityStr) > 0:
            entityFactory(entityStr, context)


def addInitialContext(context, contextLine):
    for conText in contextLine.split(","):
        entityStr = conText.strip()
        if len(entityStr) > 0:
            context["KnownEntities"].add(entityFactory(entityStr, context))


def readContext(textFile):
    context = createContext()
    for line in textFile:
        if line.strip().startswith("#"):
            splitline = line.strip("#,\n").strip().split("\t", 1)

            if splitline[0] == "Film:":
                context["Film"] = splitline[1] if len(splitline) >= 2 else ""
            elif splitline[0] == "Scene:":
                context["Scene"] = splitline[1] if len(splitline) >= 2 else ""
            elif splitline[0] == "FPS:":
                context["FPS"] = int(splitline[1]) if len(splitline) >= 2 else ""
            elif splitline[0] == "Context:":
                if len(splitline) >= 2:
                    addInitialContext(context, splitline[1])
            elif splitline[0] == "EntityList:":
                if len(splitline) >= 2:
                    addEntityList(context, splitline[1])
    return context


def readBeatscript(textFile, context):
    beatList = []
    for l in textFile:
        if l.startswith("#"): continue
        beatList.append(Beat(l, context))
    return beatList


def isSplittingPoint(block, nextBeat):
    if not len(block): return False
    lastBeat = block[-1]
    if lastBeat.shotId != nextBeat.shotId: return True
    if lastBeat.type in [INTRODUCE, SHOW]: return False
    if lastBeat.type in [SAYS, ACTION]: return True
    # lastBeat.type == EXPRESS
    if (nextBeat.type in [SAYS, ACTION] and
        lastBeat.subject == nextBeat.subject): return False
    else: return True


def coalesceBeats(beatList):
    blockList = []
    block = []
    for beat in beatList:
        if isSplittingPoint(block, beat):
            blockList.append(block)
            block = []
        else:
            block.append(beat)

    return blockList


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


def getBeatListAndContextFromFile(file):
    beatscriptFile = open(file, "r")
    lines = beatscriptFile.readlines()
    context = readContext(lines)
    beatList = readBeatscript(lines, context)
    return context, beatList


def createFeatureLines(context, beatList, shot, leaveout=-1):
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
    context, beatList = getBeatListAndContextFromFile(file)
    return createFeatureLines(context, beatList, shot, leaveout)


def getFeatureLinesFromFileAndModify(file, shot):
    context, beatList = getBeatListAndContextFromFile(file)
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


def getBlockList(lines, context):
    beatList = readBeatscript(lines, context)
    return coalesceBeats(beatList)


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


def getSingleFeatureLineFromFile(file, decisions, shot, leave_out=-1):
    featureLines = []
    beatscriptFile = open(file, "r")
    lines = beatscriptFile.readlines()
    context = readContext(lines)
    blockList = getBlockList(lines, context)
    Features.initializeContextVars(context)
    lastShotId = -1
    context["BygoneBlocks"] = []
    for i in range(0, len(decisions)):
        block = blockList[i]
        for beat in block:
            beat.shot = Beat.shotType[decisions[i].value]
        featureLines.append(getFeatureLine(context, block, shot, lastShotId))
        context["BygoneBlocks"].append(block)
        lastShotId = block[-1].shotId
    featureLine = getFeatureLine(context, blockList[len(decisions)], shot, lastShotId, leave_out)
    return featureLine


def getIdCount(file, frame_no):
    beatscriptFile = open(file, "r")
    lines = beatscriptFile.readlines()
    context = readContext(lines)
    beatList = readBeatscript(lines, context)
    count = 1
    lastShotId = beatList[0].shotID
    for beat in beatList:
        if frame_no >= beat.shotId != lastShotId:
            count += 1
    return count


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
