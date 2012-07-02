#!/usr/bin/python
# -*- coding: utf-8 -*-

from Config import PERSON, OBJECT, PLACE, DEMONSTRAT_TYPE_NAMES, BEAT_TYPE_NAMES
from Config import INTRODUCE, EXPRESS, SAYS, ACTION, SHOW
from Config import DETAIL, CLOSEUP, MEDIUM_SHOT, AMERICAN_SHOT, FULL_SHOT, LONG_SHOT, EXTREME_LONG_SHOT

class Entity:
    entityType = {"person": PERSON, "object": OBJECT, "place": PLACE}

    def __init__(self, text):
        splitText = text.strip().split("§")
        self.type = self.entityType[splitText[0]]
        self.name = splitText[1]

    def __str__(self):
        return DEMONSTRAT_TYPE_NAMES[self.type] + "§" + self.name

    def __repr__(self):
        return "<Entity: " + str(self) + ">"


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
            r_split = splitText[5].strip('\t').split("\t")
            if len(r_split) > 0:
                self.speech = r_split[0]
            if len(r_split) > 1:
                self.audiences = [entityFactory(e, context) for e in r_split[1:]]
                self.linetarget = self.audiences[0]
        if self.type == ACTION:
            r_split = splitText[5].strip('\t').split("\t")
            if len(r_split) > 0:
                self.action = r_split[0]
            if len(r_split) > 1:
                self.description = r_split[1]
            if len(r_split) > 2:
                self.object = entityFactory(r_split[2], context)
                self.linetarget = self.object

    def __str__(self):
        return str(self.shotId) + "_" + str(self.beatId) + ": " + BEAT_TYPE_NAMES[self.type]

    def __repr__(self):
        return "<Beat " + str(self) + ">"

# =============================== Methods ======================================
def entityFactory(entityText, context):
    newEntity = Entity(entityText)
    if newEntity.name not in context["Entities"]:
        context["Entities"][newEntity.name] = newEntity
    return context["Entities"][newEntity.name]

def createContext():
    context = {"Entities": {}, "KnownEntities": set(), "BygoneBlocks": [], "protagonist": False, "MainCharacters": [],
               "ExpositoryPhase": True}
    return context

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
            split_line = line.strip("#,\n").strip().split("\t", 1)

            if split_line[0] == "Film:":
                context["Film"] = split_line[1] if len(split_line) >= 2 else ""
            elif split_line[0] == "Scene:":
                context["Scene"] = split_line[1] if len(split_line) >= 2 else ""
            elif split_line[0] == "FPS:":
                context["FPS"] = int(split_line[1]) if len(split_line) >= 2 else ""
            elif split_line[0] == "Context:":
                if len(split_line) >= 2:
                    addInitialContext(context, split_line[1])
            elif split_line[0] == "EntityList:":
                if len(split_line) >= 2:
                    addEntityList(context, split_line[1])
    return context

def readBeatscript(textFile, context):
    beatList = []
    for l in textFile:
        if l.startswith("#"): continue
        beatList.append(Beat(l, context))
    return beatList

def isSplittingPoint(block, nextBeat):
    """
    There is certainly a splitting point, where the shotId changes.
    If there was an introduce or a show-Beat before and the shotId is the same, there is no split.
    If there was speech or action before, then there is a split.
    If speech or action is coming and the subjects change, there is a split.
    """
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
    """
    Returns a blockList for a given beatList. This function uses isSplittingPoint which tries to determine which
    Beats in a row can be collected into the same block. This is never the case if the Beats share the same shotId.
    If the shotId is the same, the Blocks are only split if there was speech or action before or if speech or
    action is coming and the subjects change.
    """
    blockList = []
    block = []
    for beat in beatList:
        if isSplittingPoint(block, beat):
            blockList.append(block)
            block = [beat]
        else:
            block.append(beat)
    blockList.append(block)
    return blockList

def getContextAndBeatListFromFile(file):
    """
    This function reads the file, extracts a context with readContext and a beatList with readBeatscript.
    context and beatList is returned.
    """
    beatscript_file = open(file, "r")
    lines = beatscript_file.readlines()
    context = readContext(lines)
    beatList = readBeatscript(lines, context)
    return context, beatList

def getBlockList(lines, context):
    beatList = readBeatscript(lines, context)
    return coalesceBeats(beatList)

def getBeatsBetweenFrames(beatscript, start_frame, end_frame):
    """
    Get all beats in a given beatscript between start_frame (exclusive) and end_frame (inclusive).
    And set all the shots to DETAIL to prevent cheating.
    """
    beat_list = [beat for beat in beatscript if start_frame < beat.shotId <= end_frame]
    for beat in beat_list:
        beat.shot = DETAIL
    return beat_list