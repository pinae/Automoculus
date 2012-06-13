#!/usr/bin/python
# -*- coding: utf-8 -*- 

# =============================== Imports ======================================
import inspect
import sys
from copy import copy
from Config import DETAIL, CLOSEUP, MEDIUM_SHOT, AMERICAN_SHOT, FULL_SHOT, LONG_SHOT, EXTREME_LONG_SHOT
from Config import SHOT_NAMES
from Config import BEAT_TYPE_NAMES, DEMONSTRAT_TYPE_NAMES
from Config import INTRODUCE, EXPRESS, SAYS, ACTION, SHOW
from Config import PERSON, OBJECT, PLACE

CURRENT_MODULE = sys.modules[__name__]

# =============================== Initialization ===============================
def initializeContextVars(context):
    context["ThereWasNoEstablishingShot"] = True
    context["NoConflictIntroduction"] = True
    context["BeforeWasNoConflictIntroduction"] = True
    context["NoClimax"] = True
    context["DramaturgicalFactor"] = 0

# =============================== Base Class ===================================
class Feature:
    """Base class for all features"""

    def __init__(self, context, block):
        self.numbers = self.calculateNumbers(context, block)
        pass

    def calculateNumbers(self, context, block):
        raise NotImplementedError("IMPLEMENT THIS METHOD!")

    def getNumbers(self):
        return self.numbers

    def getText(self):
        pass

    def getNames(self):
        pass

# =============================== Features =====================================
class BlockBeatTypeCount(Feature):
    def calculateNumbers(self, context, block):
        beatCount = [0, 0, 0, 0, 0]
        for beat in block:
            beatCount[beat.type] += 1
        beatCount.pop(1)
        return beatCount

    def getText(self):
        output = "BeatTyp(Block): "
        for i, cnt in enumerate(self.numbers):
            if i >= 1: nameindex = i + 1
            else: nameindex = i
            output += BEAT_TYPE_NAMES[nameindex] + ":" + str(cnt) + " "
        return output

    def getNames(self):
        names = []
        for i in range(0, len(self.numbers)):
            if i >= 1: nameindex = i + 1
            else: nameindex = i
            names.append("Anzahl " + BEAT_TYPE_NAMES[nameindex] + " im aktuellen Block")
        return names


class AlloverBeatTypeCount(Feature):
    def calculateNumbers(self, context, block):
        beatCount = [0, 0, 0, 0, 0]
        for beat in context["BeatList"]:
            beatCount[beat.type] += 1
        beatCount.pop(0)
        return beatCount

    def getText(self):
        output = "BeatTyp(gesamt): "
        for i, cnt in enumerate(self.numbers):
            output += BEAT_TYPE_NAMES[i + 1] + ":" + str(cnt) + " "
        return output

    def getNames(self):
        names = []
        for i in range(0, len(self.numbers)):
            names.append("Anzahl " + BEAT_TYPE_NAMES[i + 1] + " bisher insgesamt")
        return names


class EstablishingShot(Feature):
    def calculateNumbers(self, context, block):
        if len(context["BygoneBlocks"])>=2:
          if context["ThereWasNoEstablishingShot"]:
            introducePlace = False
            for beat in context["BygoneBlocks"][-1]:
                if beat.type in [INTRODUCE, SHOW]:
                    if beat.subject.type == PLACE and not beat.invisible:
                        introducePlace = True
                        # Quick&Dirty: Establishing-Shot, wenn ein Ort introduced wird und die Einstellungsgröße mindestens full-shot ist.
            if (context["BygoneBlocks"][-1][-1].shot in range(FULL_SHOT, EXTREME_LONG_SHOT + 1)) and introducePlace:
                context["ThereWasNoEstablishingShot"] = False
                return [1]
            else:
                return [0]
          else:
            return [1]
        else: return [0]

    def getText(self):
        if self.numbers[0]:
            output = "Es gab einen Establishing-Shot."
        else:
            output = "Es gab keinen Establishing-Shot."
        return output

    def getNames(self):
        return ["Es gab einen Establishing-Shot?"]


class ConflictIntroduction(Feature):
    def calculateNumbers(self, context, block):
        context["BeforeWasNoConflictIntroduction"] = context["NoConflictIntroduction"]
        if context["NoConflictIntroduction"] and not context["ThereWasNoEstablishingShot"]:
            blockWithExpress = False
            for beat in block:
                if beat.type == EXPRESS and not beat.invisible: blockWithExpress = True
            if blockWithExpress:
                context["NoConflictIntroduction"] = False
                return [1]
            else:
                return [0]
        else:
            return [1]

    def getText(self):
        if not self.numbers[0]:
            return "Der Konflikt wurde noch nicht etabliert."
        else:
            return "Der Konflikt wurde etabliert"

    def getNames(self):
        return ["Der Konflikt wurde etabliert?"]


class Climax(Feature):
    def calculateNumbers(self, context, block):
        blockWithExpress = False
        for beat in block:
            if beat.type == EXPRESS and not beat.invisible: blockWithExpress = True
        if context["NoClimax"]:
            if not context["BeforeWasNoConflictIntroduction"]:
                if blockWithExpress:
                    context["NoClimax"] = False
                    return [1]
                else:
                    return [0]
            else: return [0]
        else:
            if blockWithExpress:
                return [1]
            else:
                context["NoClimax"] = True
                context["NoConflictIntroduction"] = True
                context["BeforeWasNoConflictIntroduction"] = True
                return [0]

    def getText(self):
        if not self.numbers[0]:
            return "Keine Höhepunktphase."
        else:
            return "Höhepunktphase."

    def getNames(self):
        return ["Höhepunktphase?"]


        #class DramaturgicalFactor(Feature):
        # In vielen Fällen entsteht Spannung durch die Interaktion zwischen den Figuren.
        # Daher wird der Dramaturgische Faktor immer hochgezählt, wenn eine Handlung einer
        # Figur eine Reaktion auf die Handlung einer anderen Gigur sein könnte. Gezählt
        # werden Actions, Expressions und Says.

#    def calculateNumbers(self, context, block):
#        SubjectChanges = 0
#        prevSubject = False
#        i = -1
#        while not prevSubject:
#            try:
#                previousBlock = context["BygoneBlocks"][i]
#            except IndexError:
#                break
#            for beat in previousBlock:
#                if beat.type in [ACTION, EXPRESS, SAYS]:
#                    prevSubject = beat.subject
#            i -= 1
#        for beat in block:
#            if beat.type in [ACTION, EXPRESS, SAYS]:
#                if prevSubject != beat.subject:
#                    SubjectChanges += 1
#                prevSubject = beat.subject
#                #print str(SubjectChanges)
#        if not context["NoConflictIntroduction"]:
#            if context["NoClimax"]:
#                context["DramaturgicalFactor"] += 3 * SubjectChanges
#        else:
#            context["DramaturgicalFactor"] += SubjectChanges
#        return [context["DramaturgicalFactor"]]


#    def getText(self):
#        return "Dramaturgischer-Spannungsfaktor: " + str(self.numbers[0])

#    def getNames(self):
#        return ["Dramaturgischer-Spannungsfaktor"]


class MiniDramaturgyFactor(Feature):
    # In vielen Fällen entsteht Spannung durch die Interaktion zwischen den Figuren.
    # Daher wird der Dramaturgische Faktor immer hochgezählt, wenn eine Handlung einer
    # Figur eine Reaktion auf die Handlung einer anderen Gigur sein könnte. Gezählt
    # werden Actions, Expressions und Says.
    def calculateNumbers(self, context, block):
        SubjectChanges = 0
        prevSubject = False
        i = -1
        while not prevSubject:
            try:
                previousBlock = context["BygoneBlocks"][i]
            except IndexError:
                break
            for beat in previousBlock:
                if beat.type in [ACTION, EXPRESS, SAYS]:
                    prevSubject = beat.subject
            i -= 1
        for beat in block:
            if beat.type in [ACTION, EXPRESS, SAYS]:
                if prevSubject != beat.subject:
                    SubjectChanges += 1
                prevSubject = beat.subject
        if not context["NoConflictIntroduction"]:
            if context["NoClimax"]:
                context["DramaturgicalFactor"] += SubjectChanges
        else:
            context["DramaturgicalFactor"] = 0
        return [context["DramaturgicalFactor"]]

    def getText(self):
        return "Minidramaturgiefaktor: " + str(self.numbers[0])

    def getNames(self):
        return ["Minidramaturgiefaktor"]


class Dialogue(Feature):
    def calculateNumbers(self, context, block):
        lastSaySubject = False
        dialogue = False
        actcounter = 0
        for beat in context["BeatList"]:
            if beat.type == SAYS:
                if lastSaySubject:
                    if actcounter <= 1:
                        if beat.subject != lastSaySubject:
                            dialogue = True
                    else:
                        dialogue = False
                lastSaySubject = beat.subject
                actcounter = 0
            if beat.type == ACTION and not beat.invisible:
                actcounter += 1
                if actcounter > 1:
                    dialogue = False
        context["DialoguePart"] = dialogue
        if dialogue: return [1]
        else: return [0]

    def getText(self):
        if self.numbers[0]:
            return "Dialogpassage."
        else:
            return "Handlungspassage."

    def getNames(self):
        return ["Dialog- oder Handlungspassage?"]


class EmotionalDialogueReaction(Feature):
    def calculateNumbers(self, context, block):
        if len(context["BeatList"]) >= 3:
            lastsayer = context["BeatList"][-1].subject
            for i in range(0, len(context["BeatList"]) - 2):
                if context["BeatList"][i].type == SAYS:
                    lastsayer = context["BeatList"][i].subject
            if context["BeatList"][-3].type == SAYS and context["BeatList"][-2].type == EXPRESS and\
               not context["BeatList"][-2].invisible and context["BeatList"][-1].type == SAYS and\
               context["BeatList"][-2].subject != context["BeatList"][-1].subject and\
               context["BeatList"][-3].subject == context["BeatList"][-1].subject and len(block) >= 2:
                return [1]
            elif context["BeatList"][-1].type == EXPRESS and not context["BeatList"][-1].invisible and\
                 context["BeatList"][-2].type == SAYS and\
                 context["BeatList"][-2].subject != context["BeatList"][-1].subject and context["DialoguePart"] and\
                 context["BeatList"][-1].subject == lastsayer:
                return [1]
            else:
                return [0]
        else: return [0]


    def getText(self):
        if self.numbers[0]:
            return "Emotionale Reaktion im Dialog."
        else:
            return "Keine Reaktion im Dialog."

    def getNames(self):
        return ["Emotionale Reaktion im Dialog?"]


class BlockChangeBeatType(Feature):
    def calculateNumbers(self, context, block):
        bygoneType = -1
        if len(context["BygoneBlocks"]) > 0:
            bygoneType = context["BygoneBlocks"][-1][-1].type
        return [bygoneType, block[-1].type]

    def getText(self):
        if self.numbers[0] < 0:
            bygonePart = "Es gab keinen vorherigen Beat."
        else:
            bygonePart = "Der Typ des vorherigen Beats ist " + BEAT_TYPE_NAMES[self.numbers[0]]
        return bygonePart + "\t Der Typ des ersten Beat des aktuellen Blocks ist " + BEAT_TYPE_NAMES[self.numbers[1]]

    def getNames(self):
        return ["Typ des vorherigen Beats", "Typ des ersten Beats des aktuellen Blocks"]


class BlockChangeTargetChange(Feature):
    def calculateNumbers(self, context, block):
        bygoneTarget = -1
        if len(context["BygoneBlocks"]) > 0:
            bygoneTarget = context["BygoneBlocks"][-1][-1].subject
        return [bygoneTarget != block[0].subject]

    def getText(self):
        if self.numbers[0]:
            return "Targetwechsel zu beginn des Blocks"
        else:
            return "Target des letzten Blocks hat auch den aktuellen Block begonnen."

    def getNames(self):
        return ["Target hat zu beginn des Blocks gewechselt"]


class LastSevenBeatTypes(Feature):
    def calculateNumbers(self, context, block):
        types = []
        #subjects = []
        for i in range(0, 7 - len(context["BeatList"])):
            types.append(-1)
        for i in range(max(0, len(context["BeatList"]) - 7), len(context["BeatList"])):
            types.append(context["BeatList"][i].type)
        return types

    def getText(self):
        out = ""
        for i in range(len(self.numbers), 1, -1):
            if self.numbers[-i] < 0:
                out += "Der " + str(i) + ".letzte Beat existiert nicht.\t"
            else:
                out += "Typ des " + str(i) + ".letzten Beats: " + BEAT_TYPE_NAMES[self.numbers[-i]] + "\t"
        return out + "Typ des letzten Beats: " + BEAT_TYPE_NAMES[self.numbers[-1]]

    def getNames(self):
        names = []
        for i in range(len(self.numbers), 1, -1):
            names.append("Typ des " + str(i) + ".letzten Beats")
        names.append("Typ des letzten Beats")
        return names


class SameSubjectPairs(Feature):
    # TODO: Optimize this!
    def calculateNumbers(self, context, block):
        beatlist = copy(context["BeatList"])
        prev = False
        for beat in beatlist:
            if beat.invisible:
                del beat
                continue
            if prev:
                if beat.type == prev.type and beat.subject == prev.subject and beat.type in [ACTION, SAYS]:
                    del beat
                    continue
            prev = beat
        pairings = []
        if len(beatlist) >= 2:
            if beatlist[-1].subject == beatlist[-2].subject:
                pairings.append(1)
            else:
                pairings.append(0)
        else:
            pairings += [0]
        if len(beatlist) >= 3:
            if beatlist[-1].subject == beatlist[-3].subject:
                pairings.append(1)
            else:
                pairings.append(0)
            if beatlist[-2].subject == beatlist[-3].subject:
                pairings.append(1)
            else:
                pairings.append(0)
        else:
            pairings += [0, 0]
        if len(beatlist) >= 4:
            if beatlist[-1].subject == beatlist[-4].subject:
                pairings.append(1)
            else:
                pairings.append(0)
            if beatlist[-2].subject == beatlist[-4].subject:
                pairings.append(1)
            else:
                pairings.append(0)
            if beatlist[-3].subject == beatlist[-4].subject:
                pairings.append(1)
            else:
                pairings.append(0)
        else:
            pairings += [0, 0, 0]
        if len(beatlist) >= 5:
            if beatlist[-1].subject == beatlist[-5].subject:
                pairings.append(1)
            else:
                pairings.append(0)
            if beatlist[-2].subject == beatlist[-5].subject:
                pairings.append(1)
            else:
                pairings.append(0)
            if beatlist[-3].subject == beatlist[-5].subject:
                pairings.append(1)
            else:
                pairings.append(0)
            if beatlist[-4].subject == beatlist[-5].subject:
                pairings.append(1)
            else:
                pairings.append(0)
        else:
            pairings += [0, 0, 0, 0]
        if len(beatlist) >= 6:
            if beatlist[-1].subject == beatlist[-6].subject:
                pairings.append(1)
            else:
                pairings.append(0)
            if beatlist[-2].subject == beatlist[-6].subject:
                pairings.append(1)
            else:
                pairings.append(0)
            if beatlist[-3].subject == beatlist[-6].subject:
                pairings.append(1)
            else:
                pairings.append(0)
            if beatlist[-4].subject == beatlist[-6].subject:
                pairings.append(1)
            else:
                pairings.append(0)
            if beatlist[-5].subject == beatlist[-6].subject:
                pairings.append(1)
            else:
                pairings.append(0)
        else:
            pairings += [0, 0, 0, 0, 0]
        if len(beatlist) >= 7:
            if beatlist[-1].subject == beatlist[-7].subject:
                pairings.append(1)
            else:
                pairings.append(0)
            if beatlist[-2].subject == beatlist[-7].subject:
                pairings.append(1)
            else:
                pairings.append(0)
            if beatlist[-3].subject == beatlist[-7].subject:
                pairings.append(1)
            else:
                pairings.append(0)
            if beatlist[-4].subject == beatlist[-7].subject:
                pairings.append(1)
            else:
                pairings.append(0)
            if beatlist[-5].subject == beatlist[-7].subject:
                pairings.append(1)
            else:
                pairings.append(0)
            if beatlist[-6].subject == beatlist[-7].subject:
                pairings.append(1)
            else:
                pairings.append(0)
        else:
            pairings += [0, 0, 0, 0, 0, 0]
        return pairings

    def getText(self):
        if self.numbers[0]:
            out = "Die letzten beiden Subjects sind gleich.\t"
        else:
            out = "Die letzten beiden Subjects sind nicht gleich.\t"
        if self.numbers[1]:
            out += "Subjects -1 und -3 sind gleich.\t"
        else:
            out += "Subjects -1 und -3 sind nicht gleich.\t"
        if self.numbers[2]:
            out += "Subjects -2 und -3 sind gleich.\t"
        else:
            out += "Subjects -2 und -3 sind nicht gleich.\t"
        if self.numbers[3]:
            out += "Subjects -1 und -4 sind gleich.\t"
        else:
            out += "Subjects -1 und -4 sind nicht gleich.\t"
        if self.numbers[4]:
            out += "Subjects -2 und -4 sind gleich.\t"
        else:
            out += "Subjects -2 und -4 sind nicht gleich.\t"
        if self.numbers[5]:
            out += "Subjects -3 und -4 sind gleich.\t"
        else:
            out += "Subjects -3 und -4 sind nicht gleich.\t"
        if self.numbers[6]:
            out += "Subjects -1 und -5 sind gleich.\t"
        else:
            out += "Subjects -1 und -5 sind nicht gleich.\t"
        if self.numbers[7]:
            out += "Subjects -2 und -5 sind gleich.\t"
        else:
            out += "Subjects -2 und -5 sind nicht gleich.\t"
        if self.numbers[8]:
            out += "Subjects -3 und -5 sind gleich.\t"
        else:
            out += "Subjects -3 und -5 sind nicht gleich.\t"
        if self.numbers[9]:
            out += "Subjects -4 und -5 sind gleich.\t"
        else:
            out += "Subjects -4 und -5 sind nicht gleich.\t"
        if self.numbers[10]:
            out += "Subjects -1 und -6 sind gleich.\t"
        else:
            out += "Subjects -1 und -6 sind nicht gleich.\t"
        if self.numbers[11]:
            out += "Subjects -2 und -6 sind gleich.\t"
        else:
            out += "Subjects -2 und -6 sind nicht gleich.\t"
        if self.numbers[12]:
            out += "Subjects -3 und -6 sind gleich.\t"
        else:
            out += "Subjects -3 und -6 sind nicht gleich.\t"
        if self.numbers[13]:
            out += "Subjects -4 und -6 sind gleich.\t"
        else:
            out += "Subjects -4 und -6 sind nicht gleich.\t"
        if self.numbers[14]:
            out += "Subjects -5 und -6 sind gleich.\t"
        else:
            out += "Subjects -5 und -6 sind nicht gleich.\t"
        if self.numbers[15]:
            out += "Subjects -1 und -7 sind gleich.\t"
        else:
            out += "Subjects -1 und -7 sind nicht gleich.\t"
        if self.numbers[16]:
            out += "Subjects -2 und -7 sind gleich.\t"
        else:
            out += "Subjects -2 und -7 sind nicht gleich.\t"
        if self.numbers[17]:
            out += "Subjects -3 und -7 sind gleich.\t"
        else:
            out += "Subjects -3 und -7 sind nicht gleich.\t"
        if self.numbers[18]:
            out += "Subjects -4 und -7 sind gleich.\t"
        else:
            out += "Subjects -4 und -7 sind nicht gleich.\t"
        if self.numbers[19]:
            out += "Subjects -5 und -7 sind gleich.\t"
        else:
            out += "Subjects -5 und -7 sind nicht gleich.\t"
        if self.numbers[20]:
            out += "Subjects -6 und -7 sind gleich."
        else:
            out += "Subjects -6 und -7 sind nicht gleich."
        return out

    def getNames(self):
        return ["Die letzten beiden Subjects sind gleich?",
                "Subjects -1 und -3 sind gleich?",
                "Subjects -2 und -3 sind gleich?",
                "Subjects -1 und -4 sind gleich?",
                "Subjects -2 und -4 sind gleich?",
                "Subjects -3 und -4 sind gleich?",
                "Subjects -1 und -5 sind gleich?",
                "Subjects -2 und -5 sind gleich?",
                "Subjects -3 und -5 sind gleich?",
                "Subjects -4 und -5 sind gleich?",
                "Subjects -1 und -6 sind gleich?",
                "Subjects -2 und -6 sind gleich?",
                "Subjects -3 und -6 sind gleich?",
                "Subjects -4 und -6 sind gleich?",
                "Subjects -5 und -6 sind gleich?",
                "Subjects -1 und -7 sind gleich?",
                "Subjects -2 und -7 sind gleich?",
                "Subjects -3 und -7 sind gleich?",
                "Subjects -4 und -7 sind gleich?",
                "Subjects -5 und -7 sind gleich?",
                "Subjects -6 und -7 sind gleich?"]


class InvisibleCount(Feature):
    def calculateNumbers(self, context, block):
        i = 0
        for beat in block:
            if beat.invisible: i += 1
        return [i]

    def getText(self):
        return "Im Block sind " + str(self.numbers[0]) + " unsichtbare beats."

    def getNames(self):
        return ["Anzahl unsichtbarer Beats im aktuellen Block"]


class PersonAnalyzer(Feature):
    # TODO: Optimize this!!
    def calculateNumbers(self, context, block):
        personHistogram = {}
        personBeatCount = 0
        for beat in context["BeatList"]:
            if beat.subject.type == PERSON:
                personBeatCount += 1
                if beat.subject in personHistogram:
                    personHistogram[beat.subject] += 1
                else:
                    personHistogram[beat.subject] = 1
        context["MainCharacters"] = []
        protagonistBeatCount = 0
        protagonist = block[-1].subject
        for person in personHistogram:
            if personHistogram[person] >= personBeatCount / len(personHistogram):
                context["MainCharacters"].append(person)
            if personHistogram[person] >= protagonistBeatCount:
                protagonist = person
                protagonistBeatCount = personHistogram[person]
        if protagonistBeatCount > 0 and "protagonist" in context:
            if context["protagonist"] != protagonist:
                protagonistChange = 1
            else: protagonistChange = 0
        else: protagonistChange = 0
        context["protagonist"] = protagonist
        mainCharacterBlockBeatCount = 0
        protagonistBlockBeatCount = 0
        for beat in block:
            if beat.subject in context["MainCharacters"]:
                mainCharacterBlockBeatCount += 1
            if beat.subject == protagonist:
                protagonistBlockBeatCount += 1
        lastBeatsFeatureProtagonist = []
        if len(context["BeatList"]) >= 3:
            if context["BeatList"][-3].subject == protagonist:
                lastBeatsFeatureProtagonist.append(1)
            else:
                lastBeatsFeatureProtagonist.append(0)
        else: lastBeatsFeatureProtagonist.append(0)
        if len(context["BeatList"]) >= 2:
            if context["BeatList"][-2].subject == protagonist:
                lastBeatsFeatureProtagonist.append(1)
            else:
                lastBeatsFeatureProtagonist.append(0)
        else: lastBeatsFeatureProtagonist.append(0)
        if context["BeatList"][-1].subject == protagonist:
            lastBeatsFeatureProtagonist.append(1)
        else:
            lastBeatsFeatureProtagonist.append(0)
        return [len(personHistogram), len(context["MainCharacters"]),
                int(round(100.0 * mainCharacterBlockBeatCount / len(block))),
                int(round(100.0 * protagonistBeatCount / personBeatCount)), protagonistChange,
                int(round(100.0 * protagonistBlockBeatCount / len(block)))] + lastBeatsFeatureProtagonist

    def getText(self):
        out = "Bisher kamen " + str(self.numbers[0]) + " Figuren vor.\t"
        out += "Es gibt " + str(self.numbers[1]) + " Hauptfiguren.\t"
        out += str(self.numbers[2]) + "% der Beats im aktuellen Block handeln von Hauptfiguren.\t"
        out += "Der Protagonist kommt in " + str(self.numbers[3]) + "% der Beats vor.\t"
        if self.numbers[4]:
            out += "Der Protagonist hat sich in diesem Block geändert.\t"
        else:
            out += "Es ist der gleiche Protagonist wie bisher.\t"
        out += "Der Protagonist kommt in " + str(self.numbers[5]) + "% der Beats des aktuellen Blocks vor.\t"
        if self.numbers[6]:
            out += "Der Protagonist kommt im 3.letzten Beat vor.\t"
        else:
            out += "Der Protagonist kommt im 3.letzten Beat nicht vor.\t"
        if self.numbers[7]:
            out += "Der Protagonist kommt im 2.letzten Beat vor.\t"
        else:
            out += "Der Protagonist kommt im 2.letzten Beat nicht vor.\t"
        if self.numbers[8]:
            out += "Der Protagonist kommt im letzten Beat vor."
        else:
            out += "Der Protagonist kommt im letzten Beat nicht vor."
        return out

    def getNames(self):
        return ["Anzahl bisher vorgekommener Figuren",
                "Anzahl Hauptfiguren",
                "Anteil der Beats im aktuellen Block, die von Hauptfiguren handeln",
                "Anteil der Beats in denen der Protagonist vorkommt",
                "Anderer Protagonist in diesem Block?",
                "Anteil der Beats vom aktuellen Block, in denen der Protagonist vorkommt",
                "Der Protagonist kommt im 3.letzten Beat vor?",
                "Der Protagonist kommt im 2.letzten Beat vor?",
                "Der Protagonist kommt im letzten Beat vor?"]


class DecidedShots(Feature):
    def calculateNumbers(self, context, block):
        last_shot_id = context["BeatList"][-1].shotId
        beat_count = 1
        beat_counts = []
        last_shot = -3
        shots = []
        subject_histograms = [[0, 0, 0]]
        subject_histograms[-1][context["BeatList"][-1].subject.type] += 1
        beat_histograms = [[0, 0, 0, 0, 0]]
        beat_histograms[-1][context["BeatList"][-1].type] += 1
        subjects = [context["BeatList"][-1].subject]
        subject_counts = []
        for i in range(len(context["BeatList"]) - 2, -1, -1):
            if context["BeatList"][i].shotId != last_shot_id and abs(context["BeatList"][i].shot - last_shot) >= 2:
                beat_counts.append(beat_count)
                beat_count = 1
                last_shot = context["BeatList"][i].shot
                last_shot_id = context["BeatList"][i].shotId
                shots.append(last_shot)
                subject_histograms.append([0, 0, 0])
                subject_histograms[-1][context["BeatList"][i].subject.type] += 1
                beat_histograms.append([0, 0, 0, 0, 0])
                beat_histograms[-1][context["BeatList"][i].type] += 1
                subject_counts.append(len(subjects))
                subjects = [context["BeatList"][i].subject]
            else:
                beat_count += 1
                subject_histograms[-1][context["BeatList"][i].subject.type] += 1
                beat_histograms[-1][context["BeatList"][i].type] += 1
                if not context["BeatList"][i].subject in subjects:
                    subjects.append(context["BeatList"][i].subject)
            if len(beat_counts) >= 4:
                break
        while len(shots) < 4: shots.append(-3)
        shots.reverse()
        beat_counts.append(beat_count)
        beat_counts = beat_counts[:4]
        while len(beat_counts) < 4: beat_counts.append(0)
        subject_counts.append(len(subjects))
        subject_counts = subject_counts[:2]
        while len(subject_counts) < 2: subject_counts.append(0)
        subject_counts.reverse()
        while len(beat_histograms) < 2: beat_histograms.append([0, 0, 0, 0, 0])
        while len(subject_histograms) < 2: subject_histograms.append([0, 0, 0])
        return shots + beat_counts + subject_counts + beat_histograms[0] + subject_histograms[0] +\
               beat_histograms[1] + subject_histograms[1]

    def getText(self):
        if self.numbers[0] < 0:
            out = "Es gab noch keine 4.letzte Einstellungsgröße.\t"
        else:
            out = "Die 4.letzte Einstellungsgröße war: " + SHOT_NAMES[self.numbers[0]] + "\t"
        if self.numbers[1] < 0:
            out += "Es gab noch keine 3.letzte Einstellungsgröße.\t"
        else:
            out += "Die 3.letzte Einstellungsgröße war: " + SHOT_NAMES[self.numbers[1]] + "\t"
        if self.numbers[2] < 0:
            out += "Es gab noch keine 2.letzte Einstellungsgröße.\t"
        else:
            out += "Die 2.letzte Einstellungsgröße war: " + SHOT_NAMES[self.numbers[2]] + "\t"
        if self.numbers[3] < 0:
            out += "Es gab noch keine letzte Einstellungsgröße.\t"
        else:
            out += "Die letzte Einstellungsgröße war: " + SHOT_NAMES[self.numbers[3]] + "\t"
        out += "Der letzte Schnitt liegt " + str(self.numbers[4]) + " Beats in der Vergangenheit.\t"
        out += "Die vorletzte Einstellung war " + str(self.numbers[5]) + " Beats lang.\t"
        out += "Die 2.letzte Einstellung war " + str(self.numbers[6]) + " Beats lang.\t"
        out += "Die 3.letzte Einstellung war " + str(self.numbers[7]) + " Beats lang.\t"
        out += "In der letzten Einstellung waren " + str(self.numbers[8]) + " Subjects zu sehen.\t"
        out += "Seit dem letzten Schnitt müssen " + str(self.numbers[9]) + " Subjects zu sehen sein.\t"
        for i in range(0, 5):
            out += str(self.numbers[10 + i]) + " mal " + BEAT_TYPE_NAMES[i] + " seit dem letzten Schnitt.\t"
        for i in range(0, 3):
            out += str(self.numbers[15 + i]) + " " + DEMONSTRAT_TYPE_NAMES[i] + " seit dem letzten Schnitt.\t"
        for i in range(0, 5):
            out += str(self.numbers[18 + i]) + " mal " + BEAT_TYPE_NAMES[i] + " in der vorherigen Einstellung.\t"
        for i in range(0, 3):
            out += str(self.numbers[23 + i]) + " " + DEMONSTRAT_TYPE_NAMES[i] + " in der vorherigen Einstellung.\t"
        return out.strip("\t")

    def getNames(self):
        return ["Typ der 4.letzten Einstellungsgröße", "Typ der 3.letzten Einstellungsgröße",
                "Typ der 2.letzten Einstellungsgröße", "Typ der letzten Einstellungsgröße",
                "Anzahl der Beats seit dem letzten Schnitt", "Länge der vorletzten Einstellung",
                "Länge der 2.letzten Einstellung", "Länge der 3.letzten Einstellung",
                "Anzahl der Subjekte in der letzten Einstellung",
                "Anzahl der Subjekte in den Beats seit dem letzten Schnitt",
                "Anzahl " + BEAT_TYPE_NAMES[0] + " seit dem letzten Schnitt",
                "Anzahl " + BEAT_TYPE_NAMES[1] + " seit dem letzten Schnitt",
                "Anzahl " + BEAT_TYPE_NAMES[2] + " seit dem letzten Schnitt",
                "Anzahl " + BEAT_TYPE_NAMES[3] + " seit dem letzten Schnitt",
                "Anzahl " + BEAT_TYPE_NAMES[4] + " seit dem letzten Schnitt",
                "Anzahl " + DEMONSTRAT_TYPE_NAMES[0] + " seit dem letzten Schnitt",
                "Anzahl " + DEMONSTRAT_TYPE_NAMES[1] + " seit dem letzten Schnitt",
                "Anzahl " + DEMONSTRAT_TYPE_NAMES[2] + " seit dem letzten Schnitt",
                "Anzahl " + BEAT_TYPE_NAMES[0] + " in der vorherigen Einstellung",
                "Anzahl " + BEAT_TYPE_NAMES[1] + " in der vorherigen Einstellung",
                "Anzahl " + BEAT_TYPE_NAMES[2] + " in der vorherigen Einstellung",
                "Anzahl " + BEAT_TYPE_NAMES[3] + " in der vorherigen Einstellung",
                "Anzahl " + BEAT_TYPE_NAMES[4] + " in der vorherigen Einstellung",
                "Anzahl " + DEMONSTRAT_TYPE_NAMES[0] + " in der vorherigen Einstellung",
                "Anzahl " + DEMONSTRAT_TYPE_NAMES[1] + " in der vorherigen Einstellung",
                "Anzahl " + DEMONSTRAT_TYPE_NAMES[2] + " in der vorherigen Einstellung"]


class ShotHistogram(Feature):
    def calculateNumbers(self, context, block):
        lastShotId = context["BeatList"][-1].shotId
        shotHistogram = [0, 0, 0, 0, 0, 0, 0]
        for beat in context["BeatList"]:
            if beat.shotId != lastShotId:
                shotHistogram[beat.shot] += 1
        total = 0
        for i in shotHistogram: total += i
        for i in range(0, len(shotHistogram)):
            if total > 0: shotHistogram[i] = int(round(100.0 * shotHistogram[i] / total))
        return shotHistogram

    def getText(self):
        out = ""
        for i in range(0, 7):
            out += str(self.numbers[i]) + "% " + SHOT_NAMES[i] + ".\t"
        return out.strip("\t")

    def getNames(self):
        return ["Anteil " + SHOT_NAMES[0], "Anteil " + SHOT_NAMES[1], "Anteil " + SHOT_NAMES[2],
                "Anteil " + SHOT_NAMES[3], "Anteil " + SHOT_NAMES[4], "Anteil " + SHOT_NAMES[5],
                "Anteil " + SHOT_NAMES[6]]


class PersonsInTheShot(Feature):
    def calculateNumbers(self, context, block):
        beatlist = copy(context["BeatList"])
        lastShotId = beatlist[-1].shotId
        emoPersons = {}
        sayPersons = {}
        for beat in beatlist:
            if beat.shotId == lastShotId:
                if beat.subject in emoPersons.keys():
                    if beat.type == EXPRESS:
                        emoPersons[beat.subject] += 1
                    if beat.type == SAYS:
                        sayPersons[beat.subject] += 1
                else:
                    emoPersons[beat.subject] = 0
                    sayPersons[beat.subject] = 0
        lastFive = []
        i = 1
        while i < len(beatlist) and len(lastFive) < 5:
            if not beatlist[-i].subject in lastFive:
                lastFive.append(beatlist[-i].subject)
            i += 1
        emoPersonsArray = []
        sayPersonsArray = []
        for person in lastFive:
            if person in emoPersons.keys():
                emoPersonsArray.append(emoPersons[person])
            if person in sayPersons.keys():
                sayPersonsArray.append(sayPersons[person])
        while len(emoPersonsArray) < 5:
            emoPersonsArray.append(0)
        while len(sayPersonsArray) < 5:
            sayPersonsArray.append(0)
        return emoPersonsArray + sayPersonsArray

    def getText(self):
        out = ""
        for i in range(0, 5):
            out += "Die " + str(i) + ".letzte Figur hat seit dem letzten Schnitt " + str(
                self.numbers[i]) + " mal Emotionen gezeigt.\t"
        for i in range(5, 10):
            out += "Die " + str(i - 5) + ".letzte Figur hat seit dem letzten Schnitt " + str(
                self.numbers[i]) + " mal geredet.\t"
        return out.strip("\t")

    def getNames(self):
        names = []
        for i in range(0, 5):
            names.append("Anzahl der Emotionalen Beats der " + str(i) + ".letzten Figur seit dem letzten Schnitt")
        for i in range(0, 5):
            names.append("Anzahl der Speak-Beats der " + str(i) + ".letzten Figur seit dem letzten Schnitt")
        return names


class ShowingObject(Feature):
    def calculateNumbers(self, context, block):
        showingOnlyObjects = True
        noVisibleBeats = True
        for beat in block:
            if not((beat.type in [INTRODUCE, SHOW] and beat.subject.type == OBJECT) or beat.invisible):
                showingOnlyObjects = False
            if beat.type in [INTRODUCE, SHOW] and not beat.invisible:
                noVisibleBeats = False
        if showingOnlyObjects and not noVisibleBeats:
            if len(context["BygoneBlocks"]) > 0:
                if context["BygoneBlocks"][-1][-1].shot != DETAIL:
                    return [1]
                else:
                    return [0]
            else:
                return [1]
        else:
            return [0]

    def getText(self):
        if self.numbers[0]:
            return "Die Beats seit dem letzten Schnitt zeigen nur ein Objekt."
        else:
            return "Es wird nicht nur ein Objekt gezeigt."

    def getNames(self):
        return ["Nur ein gezeigtes Objekt seit dem letzten Schnitt?"]


class ShowingPlace(Feature):
    def calculateNumbers(self, context, block):
        showingOnlyObjects = True
        noVisibleBeats = True
        for beat in block:
            if not((beat.type in [INTRODUCE, SHOW] and beat.subject.type == PLACE) or beat.invisible):
                showingOnlyObjects = False
            if beat.type in [INTRODUCE, SHOW] and not beat.invisible:
                noVisibleBeats = False
        if showingOnlyObjects and not noVisibleBeats:
            if len(context["BygoneBlocks"]) > 0:
                if context["BygoneBlocks"][-1][-1].shot in range(FULL_SHOT,EXTREME_LONG_SHOT+1):
                    return [1]
                else:
                    return [0]
            else:
                return [1]
        else:
            return [0]

    def getText(self):
        if self.numbers[0]:
            return "Die Beats seit dem letzten Schnitt zeigen nur einen Ort."
        else:
            return "Es wird nicht nur ein Ort gezeigt."

    def getNames(self):
        return ["Nur ein gezeigter Ort seit dem letzten Schnitt?"]


class ShowingPerson(Feature):
    def calculateNumbers(self, context, block):
        showingOnlyOnePerson = True
        noVisibleBeats = True
        person = False
        for beat in block:
            if not beat.invisible:
                noVisibleBeats = False
                if beat.subject.type == PERSON:
                    if person:
                        if person != beat.subject:
                            showingOnlyOnePerson = False
                    else:
                        person = beat.subject
                else:
                    showingOnlyOnePerson = False
        if showingOnlyOnePerson and not noVisibleBeats:
            return [1]
        else:
            return [0]

    def getText(self):
        if self.numbers[0]:
            return "Die Beats seit dem letzten Schnitt zeigen nur eine Person."
        else:
            return "Es wird seit dem letzten Schnitt nicht nur eine Person gezeigt."

    def getNames(self):
        return ["Nur eine gezeigte Person seit dem letzten Schnitt?"]


class Linetargets(Feature):
    def calculateNumbers(self, context, block):
        numberOfLinetargets = 0
        lastLinetarget = False
        for beat in block:
            if beat.linetarget:
                numberOfLinetargets += 1
                lastLinetarget = beat.linetarget
        lastLinetargetIsSubjects = []
        for i in range(1, 9):
            if len(context["BeatList"]) > i:
                if context["BeatList"][-i].subject is lastLinetarget:
                    lastLinetargetIsSubjects.append(1)
                else: lastLinetargetIsSubjects.append(0)
            else: lastLinetargetIsSubjects.append(0)
        if lastLinetarget:
            return lastLinetargetIsSubjects + [numberOfLinetargets, lastLinetarget.type != PERSON,
                                               lastLinetarget in context["MainCharacters"],
                                               lastLinetarget == context["protagonist"]]
        else:
            return lastLinetargetIsSubjects + [numberOfLinetargets, 0, lastLinetarget in context["MainCharacters"],
                                               lastLinetarget == context["protagonist"]]

    def getText(self):
        if self.numbers[0]: out = "Das Linetarget ist gleich dem Subjekt des letzten Beats.\t"
        else: out = "Das Linetarget ist nicht Subjekt des letzten Beats.\t"
        if self.numbers[1]: out = "Das Linetarget ist gleich dem Subjekt des 2. letzten Beats.\t"
        else: out += "Das Linetarget ist nicht Subjekt des 2. letzten Beats.\t"
        if self.numbers[2]: out += "Das Linetarget ist gleich dem Subjekt des 3. letzten Beats.\t"
        else: out += "Das Linetarget ist nicht Subjekt des 3. letzten Beats.\t"
        if self.numbers[3]: out += "Das Linetarget ist gleich dem Subjekt des 4. letzten Beats.\t"
        else: out += "Das Linetarget ist nicht Subjekt des 4. letzten Beats.\t"
        if self.numbers[4]: out += "Das Linetarget ist gleich dem Subjekt des 5. letzten Beats.\t"
        else: out += "Das Linetarget ist nicht Subjekt des 5. letzten Beats.\t"
        if self.numbers[5]: out += "Das Linetarget ist gleich dem Subjekt des 6. letzten Beats.\t"
        else: out += "Das Linetarget ist nicht Subjekt des 6. letzten Beats.\t"
        if self.numbers[6]: out += "Das Linetarget ist gleich dem Subjekt des 7. letzten Beats.\t"
        else: out += "Das Linetarget ist nicht Subjekt des 7. letzten Beats.\t"
        if self.numbers[7]: out += "Das Linetarget ist gleich dem Subjekt des 8. letzten Beats.\t"
        else: out += "Das Linetarget ist nicht Subjekt des 8. letzten Beats.\t"
        out += "Im Aktuellen Block gibt es " + str(self.numbers[8]) + " linetargets.\t"
        if self.numbers[9]: out += "Das letzte Linetarget im Block war keine Person.\t"
        else: out += "Das letzte Linetarget im Block war eine Person.\t"
        if self.numbers[10]: out += "Das letzte Linetarget im Block war eine Hauptperson.\t"
        else: out += "Das letzte Linetarget im Block war nicht unter den Hauptpersonen.\t"
        if self.numbers[11]: out += "Das letzte Linetarget im Block war der Protagonist."
        else: out += "Das letzte Linetarget im Block war nicht der Protagonist."
        return out

    def getNames(self):
        return ["Das Linetarget ist gleich dem Subjekt des letzten Beats?",
                "Das Linetarget ist gleich dem Subjekt des 2. letzten Beats?",
                "Das Linetarget ist gleich dem Subjekt des 3. letzten Beats?",
                "Das Linetarget ist gleich dem Subjekt des 4. letzten Beats?",
                "Das Linetarget ist gleich dem Subjekt des 5. letzten Beats?",
                "Das Linetarget ist gleich dem Subjekt des 6. letzten Beats?",
                "Das Linetarget ist gleich dem Subjekt des 7. letzten Beats?",
                "Das Linetarget ist gleich dem Subjekt des 8. letzten Beats?",
                "Anzahl der Linetargets im aktuellen Block", "Ist das letzte Linetarget im Block eine Person?",
                "Ist das letzte Linetarget im Block eine Hauptperson?", "War das letzte Linetarget der Protagonist?"]


class HandwrittenCutCriteria(Feature): #TODO: aktuellen Block berücksichtigen! Ist alles um einen Block verschoben? - Nein, shot wird benutzt.
    def calculateNumbers(self, context, block):
        cutCriteria = []
        if len(context["BygoneBlocks"]) >= 2:
            #if context["BygoneBlocks"][-1][0].subject == context["BygoneBlocks"][-2][-1].subject and (
            #    context["BygoneBlocks"][-2][-1].shot >= MEDIUM_SHOT and
            #    context["BygoneBlocks"][-1][0].type in [SAYS, ACTION]) or (
            #    context["BygoneBlocks"][-2][-1].shot >= CLOSEUP and context["BygoneBlocks"][-1][0].type == SAYS):
            #    cutCriteria.append(0)
            #else:
            #    cutCriteria.append(1)
            if context["BygoneBlocks"][-2][-1].shot == context["BygoneBlocks"][-1][-1].shot:
                cut = False
                subjects_of_history = set()
                for block in context["BygoneBlocks"][-2]:
                    subjects_of_history.add(block.subject)
                subjects_of_today = set()
                for block in context["BygoneBlocks"][-1]:
                    subjects_of_today.add(block.subject)
                for subject in subjects_of_today:
                    if not subject in subjects_of_history:
                        cut = True
                if cut: cutCriteria.append(1)
                else: cutCriteria.append(0)
            else: cutCriteria.append(1)
            if context["BygoneBlocks"][-2][-1].shot >= AMERICAN_SHOT and\
               context["BygoneBlocks"][-1][-1].shot >= MEDIUM_SHOT:
                cut = False
                if len(context["BygoneBlocks"]) >= 4:
                    subjects_of_history = set()
                    for i in range(-4, -2):
                        for block in context["BygoneBlocks"][i]:
                            subjects_of_history.add(block.subject)
                    subjects_of_today = set()
                    for block in context["BygoneBlocks"][-1]:
                        subjects_of_today.add(block.subject)
                    for subject in subjects_of_today:
                        if not subject in subjects_of_history:
                            cut = True
                for beat in context["BygoneBlocks"][-1]:
                    if beat.type in [SHOW, INTRODUCE] and len(context["BygoneBlocks"]) >= 5:
                        cut = True
                if cut: cutCriteria.append(1)
                else: cutCriteria.append(0)
            else: cutCriteria.append(1)
            if context["BygoneBlocks"][-1][0].subject != context["BygoneBlocks"][-2][0].subject and\
               context["BygoneBlocks"][-1][0].type == SAYS and context["BygoneBlocks"][-2][0].type == SAYS:
                cutCriteria.append(1)
            else: cutCriteria.append(0)
        else:
            #cutCriteria.append(1)
            cutCriteria.append(1)
            cutCriteria.append(1)
            cutCriteria.append(0)
        if len(context["BygoneBlocks"]) >= 2:
            if context["BygoneBlocks"][-2][-1].shot == DETAIL:
                cutCriteria.append(1)
            else: cutCriteria.append(0)
        else: cutCriteria.append(0)
        if len(context["BygoneBlocks"]) >= 1:
            if context["BygoneBlocks"][-1][0].type == EXPRESS:
                cutCriteria.append(1)
            else: cutCriteria.append(0)
        else: cutCriteria.append(0)
        return cutCriteria

    def getText(self):
        return "Die Handarbeit sagt " + str(self.numbers)

    def getNames(self):
        return ["Handgeschriebenes Schnittkriterium 1.", "Handgeschriebenes Schnittkriterium 2.",
                "Handgeschriebenes Schnittkriterium 3.", "Handgeschriebenes Schnittkriterium 4.",
                "Handgeschriebenes Schnittkriterium 5."]


class ExpositoryPhaseOfTheScene(Feature):
    def calculateNumbers(self, context, block):
        if context["ExpositoryPhase"]:
            shownPlace = False
            emotionallySituatedPersons = set()
            allPersons = set()
            for beat in block: allPersons.add(beat.subject)
            beatlist = copy(context["BeatList"])
            for beat in beatlist:
                allPersons.add(beat.subject)
                if beat.linetarget and beat.linetarget.type == PERSON: allPersons.add(beat.linetarget)
                if beat.type == EXPRESS: emotionallySituatedPersons.add(beat.subject)
                if beat.type == SHOW and beat.subject.type == PERSON: emotionallySituatedPersons.add(beat.subject)
                if beat.type in [INTRODUCE, SHOW] and beat.subject.type == PLACE: shownPlace = True
            if (shownPlace and emotionallySituatedPersons is allPersons) or (shownPlace and len(beatlist) > 15):
                context["ExpositoryPhase"] = False
                return [0]
            else:
                return [1]
        else:
            return [1]

    def getText(self):
        if self.numbers[0]:
            return "Wir sind in der Expositionsphase der Szene."
        else:
            return "Wir sind in der Handlungsentwicklungsphase der Szene."

    def getNames(self):
        return ["Expositionsphase?"]


# =============================== Helper Methods ===============================
def getAllFeatureClasses():
    '''
    Returns a list of all subclasses of Feature defined in, or imported into this module.
    '''
    featureClassList = []
    for name, obj in inspect.getmembers(CURRENT_MODULE):
        if inspect.isclass(obj) and issubclass(obj, Feature) and (obj != Feature):
            featureClassList.append(obj)
    return featureClassList


def createBeatlist(context, block):
    '''
    This function reconstructs a beatList from the BygoneBlocks in the context and the given new block.
    The beatList is saved in the context. It is necessary to do this before calculating a featureLine,
     because otherwise there is no correct BeatList in the context, which is used by the Feature-Classes.
    '''
    beatlist = []
    for bblock in context["BygoneBlocks"]:
        for beat in bblock:
            beatlist.append(beat)
    for beat in block:
        beatlist.append(beat)
    context["BeatList"] = beatlist
    return context