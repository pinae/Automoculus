#!/usr/bin/python
# -*- coding: utf-8 -*- 

# =============================== Imports ======================================
import inspect
import sys
from copy import copy
import itertools
from Config import DETAIL, CLOSEUP, MEDIUM_SHOT, AMERICAN_SHOT, FULL_SHOT, EXTREME_LONG_SHOT
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
    context["MiniDramaturgicalFactor"] = 0

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
class X_BlockBeatTypeCount(Feature):
    def calculateNumbers(self, context, block):
        beatCount = [0, 0, 0, 0, 0]
        for beat in block:
            beatCount[beat.type] += 1
        return beatCount

    def getText(self):
        output = "BeatTyp(Block): "
        for i, cnt in enumerate(self.numbers):
            output += BEAT_TYPE_NAMES[i] + ":" + str(cnt) + " "
        return output

    def getNames(self):
        names = []
        for i in range(len(self.numbers)):
            names.append("Anzahl " + BEAT_TYPE_NAMES[i] + " im aktuellen Block")
        return names


class X_AlloverBeatTypeCount(Feature):
    def calculateNumbers(self, context, block):
        beatCount = [0, 0, 0, 0, 0]
        for beat in context["BeatList"]:
            beatCount[beat.type] += 1
        return beatCount

    def getText(self):
        output = "BeatTyp(gesamt): "
        for i, cnt in enumerate(self.numbers):
            output += BEAT_TYPE_NAMES[i] + ":" + str(cnt) + " "
        return output

    def getNames(self):
        names = []
        for i in range(len(self.numbers)):
            names.append("Anzahl " + BEAT_TYPE_NAMES[i] + " bisher insgesamt")
        return names


class X_BlockBeatCount(Feature):
    def calculateNumbers(self, context, block):
        return [len(block)]

    def getText(self):
        return "Der Block besteht aus " + str(self.numbers[0]) + " Beats."

    def getNames(self):
        return ["Anzahl Beats im Block"]


class X_PlaceShowingBlock(Feature):
    """
    If the block introduces or shows a place it is time for an establishing shot. Mostly.
    """
    def calculateNumbers(self, context, block):
        place_showing_block = 0
        for beat in block:
            if beat.subject.type == PLACE and beat.type in [INTRODUCE, SHOW] and not beat.invisible:
                place_showing_block = 1
        return [place_showing_block]

    def getText(self):
        if self.numbers[0]: return "In diesem Block wird ein Ort gezeigt."
        else: return "Im aktuellen Block wird kein Ort gezeigt."

    def getNames(self):
        return ["Ort im aktuellen Block?"]


class A01_EstablishingShot(Feature):
    """
    If you want to know if there was an establishing shot you have to check if there was a block with a INTRODUCE
    or SHOW-beat which shows a place. This shot should have been classified as FULL-SHOT or wider, otherwise the
    audience couldn't have gained a sense of orientation in that place.
    """
    def calculateNumbers(self, context, block):
        if len(context["BygoneBlocks"])>=2:
          if context["ThereWasNoEstablishingShot"]:
            introduce_place = False
            for beat in context["BygoneBlocks"][-1]:
                if beat.type in [INTRODUCE, SHOW]:
                    if beat.subject.type == PLACE and not beat.invisible:
                        introduce_place = True
            if (context["BygoneBlocks"][-1][-1].shot in range(FULL_SHOT, EXTREME_LONG_SHOT + 1)) and introduce_place:
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


class A02_ConflictIntroduction(Feature):
    """
    If you want to know if the block is in a phase of conflict introduction or climax you have to check if there
    was an establishing shot.
    A conflict is usually showed to the audience which has more information than the figures. When the figure realizes
    that there is a conflict the audience already knows of it. The realization of the figure is marked by an EXPRESS-
    Beat. But when the figure expresses the realization there must have been something that happened or was said so the
    figure got additional information.
    So this algorithm searches for EXPRESS-Beats in the current block if there was an establishing shot. When there is
    an EXPRESS in the current block, it searches for the ACT- or SAY-beat which gave the decisive information. This is
    either a SAY or ACT directly before the EXPRESS or a SAY or ACT with the figure in linetargets.
    """
    def calculateNumbers(self, context, block):
        context["BeforeWasNoConflictIntroduction"] = context["NoConflictIntroduction"]
        context["PositionOfConflictIntroduction"] = -1
        if not context["ThereWasNoEstablishingShot"]:
            if EXPRESS in [beat.type for beat in block]:
                express_subject = None
                express_position = -1
                i = len(context["BeatList"])-len(block)-1
                while i>=0:
                    beat = context["BeatList"][i]
                    if beat.type == EXPRESS:
                        express_subject = beat.subject
                        if i-1 >= 0 and context["BeatList"][i-1].type in [SAYS, ACTION]:
                            context["NoConflictIntroduction"] = False
                            context["PositionOfConflictIntroduction"] = i
                            return [1]
                        else:
                            express_position = i
                    if express_subject and beat.type in [SAYS, ACTION] and\
                       beat.linetarget and beat.linetarget == express_subject:
                        context["NoConflictIntroduction"] = False
                        context["NoClimax"] = True
                        context["PositionOfConflictIntroduction"] = express_position
                        return [1]
                    i -= 1
        return [0]

    def getText(self):
        if not self.numbers[0]:
            return "Der Konflikt wurde noch nicht etabliert."
        else:
            return "Der Konflikt wurde etabliert"

    def getNames(self):
        return ["Der Konflikt wurde etabliert?"]


class A03_Climax(Feature):
    """
    After an establishing shot and a conflict introduction there could be a climax. A climax provokes an emotional
    reaction by the subject of the conflict introduction. Before that EXPRESS there needs to be a minimum of one other
    figure to ACT or SAY something. Otherwise the conflict could not have been acted out.
    """
    def calculateNumbers(self, context, block):
        there_was_a_climax = 0
        subjects = set()
        linetargets = set()
        if not context["NoConflictIntroduction"]:
            for i in range(context["PositionOfConflictIntroduction"],len(context["BeatList"])):
                beat = context["BeatList"][i]
                subjects.add(beat.subject)
                if beat.linetarget: linetargets.add(beat.linetarget)
                if beat.type == EXPRESS and len(subjects) >= 2:
                    there_was_a_climax = 1
        if there_was_a_climax:
            context["NoConflictIntroduction"] = True
            context["PositionOfConflictIntroduction"] = -1
            context["BeforeWasNoConflictIntroduction"] = True
            context["NoClimax"] = False
        return [there_was_a_climax,len(subjects),len(linetargets)]

    def getText(self):
        if not self.numbers[0]:
            return "Keine Höhepunktphase."
        else:
            return "Höhepunktphase mit "+str(self.numbers[1])+" Akteuren und "+str(self.numbers[2])+" Bezugspersonen."

    def getNames(self):
        return ["Höhepunktphase?", "Anzahl Subjects in der Phase", "Anzahl Linetargets in der Phase"]


class A04_DramaturgicalFactor(Feature):
    """
    In vielen Fällen entsteht Spannung durch die Interaktion zwischen den Figuren.
    Daher wird der Dramaturgische Faktor immer hochgezählt, wenn eine Handlung einer
    Figur eine Reaktion auf die Handlung einer anderen Gigur sein könnte. Gezählt
    werden Actions, Expressions und Says.
    """
    def calculateNumbers(self, context, block):
        subject_changes = 0
        prev_subject = None
        i = -1
        while not prev_subject:
            try:
                previousBlock = context["BygoneBlocks"][i]
            except IndexError:
                break
            for beat in previousBlock:
                if beat.type in [ACTION, EXPRESS, SAYS]:
                    prev_subject = beat.subject
            i -= 1
        for beat in block:
            if beat.type in [ACTION, EXPRESS, SAYS]:
                if prev_subject != beat.subject:
                    subject_changes += 1
                prev_subject = beat.subject

        if not context["NoConflictIntroduction"]:
            if context["NoClimax"]: context["DramaturgicalFactor"] += 3 * subject_changes
            else: context["DramaturgicalFactor"] += subject_changes
        else: context["DramaturgicalFactor"] = 0
        return [context["DramaturgicalFactor"]]

    def getText(self):
        return "Dramaturgischer-Spannungsfaktor: " + str(self.numbers[0])

    def getNames(self):
        return ["Dramaturgischer-Spannungsfaktor"]


class A05_MiniDramaturgyFactor(Feature):
    """
    In vielen Fällen entsteht Spannung durch die Interaktion zwischen den Figuren.
    Daher wird der Dramaturgische Faktor immer hochgezählt, wenn eine Handlung einer
    Figur eine Reaktion auf die Handlung einer anderen Gigur sein könnte. Gezählt
    werden Actions, Expressions und Says. Während einer Höhepunktphase wird nichts
    erhöht, da sich dann die Spannung nicht mehr steigern kann.
    """
    def calculateNumbers(self, context, block):
        subject_changes = 0
        prev_subject = None
        i = -1
        while not prev_subject:
            try:
                previous_block = context["BygoneBlocks"][i]
            except IndexError:
                break
            for beat in previous_block:
                if beat.type in [ACTION, EXPRESS, SAYS]:
                    prev_subject = beat.subject
            i -= 1
        for beat in block:
            if beat.type in [ACTION, EXPRESS, SAYS]:
                if prev_subject != beat.subject:
                    subject_changes += 1
                prev_subject = beat.subject

        if not context["NoConflictIntroduction"]:
            if context["NoClimax"]: context["DramaturgicalFactor"] += subject_changes
        else: context["MiniDramaturgicalFactor"] = 0
        return [context["MiniDramaturgicalFactor"]]

    def getText(self):
        return "Minidramaturgiefaktor: " + str(self.numbers[0])

    def getNames(self):
        return ["Minidramaturgiefaktor"]


class X_Dialogue(Feature):
    def calculateNumbers(self, context, block):
        """
        Dialogue returns 1 if there were two SAY-Beats from different subjects and not more than one ACT-Beat in
        between.
        """
        i = -1
        act_counter = 0
        say_subject = None
        while -i < len(context["BeatList"]):
            beat = context["BeatList"][i]
            if beat.type == ACTION and not beat.invisible:
                act_counter += 1
            if act_counter >= 2: return [0] # Too many ACTS
            if beat.type == SAYS:
                if say_subject and say_subject != beat.subject:
                    return [1] # Found the second SAYS and there were not more than one ACT
                else: say_subject = beat.subject
            i -= 1
        return [0] # There were

    def getText(self):
        if self.numbers[0]:
            return "Dialogpassage."
        else:
            return "Handlungspassage."

    def getNames(self):
        return ["Dialog- oder Handlungspassage?"]


class X_EmotionalDialogueReaction(Feature):
    def calculateNumbers(self, context, block):
        last_say_subject =None
        dialogue = False
        act_counter = 0
        for beat in context["BeatList"]:
            if beat.type == SAYS:
                if last_say_subject:
                    if act_counter <= 1:
                        if beat.subject != last_say_subject:
                            dialogue = True
                    else:
                        dialogue = False
                last_say_subject = beat.subject
                act_counter = 0
            if beat.type == ACTION and not beat.invisible:
                act_counter += 1
                if act_counter > 1:
                    dialogue = False

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
                 context["BeatList"][-2].subject != context["BeatList"][-1].subject and dialogue and\
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


class X_BlockChangeBeatType(Feature):
    def calculateNumbers(self, context, block):
        bygone_type = -1
        if len(context["BygoneBlocks"]) > 0:
            bygone_type = context["BygoneBlocks"][-1][-1].type
        return [bygone_type, block[-1].type]

    def getText(self):
        if self.numbers[0] < 0:
            bygonePart = "Es gab keinen vorherigen Beat."
        else:
            bygonePart = "Der Typ des vorherigen Beats ist " + BEAT_TYPE_NAMES[self.numbers[0]]
        return bygonePart + "\t Der Typ des ersten Beat des aktuellen Blocks ist " + BEAT_TYPE_NAMES[self.numbers[1]]

    def getNames(self):
        return ["Typ des vorherigen Beats", "Typ des ersten Beats des aktuellen Blocks"]


class X_BlockChangeTargetChange(Feature):
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


class X_PreviousBlockChangeTargetChange(Feature):
    def calculateNumbers(self, context, block):
        if len(context["BygoneBlocks"]) >= 2:
            if context["BygoneBlocks"][-1][-1].subject == context["BygoneBlocks"][-2][-1].subject: return [0]
            else: return [1]
        else: return [-1]

    def getText(self):
        if self.numbers[0] == 1:
            return "Es gab einen Targetwechsel zu beginn des vorherigen Blocks."
        elif not self.numbers[0]:
            return "Target des vorletzten Blocks hat auch den letzten Block begonnen."
        else:
            return "Es gibt noch keinen vorletzten Block."

    def getNames(self):
        return ["Target hat zu beginn des vorherigen Blocks gewechselt"]


class X_PreviousBlockToNowTargetPair(Feature):
    def calculateNumbers(self, context, block):
        bygoneTarget = -1
        if len(context["BygoneBlocks"]) >= 2:
            bygoneTarget = context["BygoneBlocks"][-2][-1].subject
        if bygoneTarget == block[0].subject: return [1]
        else: return [0]

    def getText(self):
        if self.numbers[0]:
            return "Target des vorletzten und des aktuellen Blocks stimmen überein."
        else:
            return "Targets des vorletzten Blocks und des aktuellen Blocks sind unterschiedlich."

    def getNames(self):
        return ["Target des vorletzten Blocks und des aktuellen Blocks stimmen überein"]


class X_LastTwelveBeatTypes(Feature):
    def calculateNumbers(self, context, block):
        types = [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
        for i in range(len(types),0,-1):
            if len(context["BeatList"]) >= i:
                types[-i] = context["BeatList"][-i].type
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


class X_SameSubjectPairs(Feature):
    def calculateNumbers(self, context, block):
        beat_list = copy(context["BeatList"])
        prev = None
        for beat in beat_list:
            if beat.invisible:
                del beat
                continue
            if prev:
                if beat.type == prev.type and beat.subject == prev.subject and beat.type in [ACTION, SAYS]:
                    del beat
                    continue
            prev = beat
        #pairings = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        pairings = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        if len(beat_list) >= 2:
            if beat_list[-1].subject == beat_list[-2].subject: pairings[0] = 1
        if len(beat_list) >= 3:
            if beat_list[-1].subject == beat_list[-3].subject: pairings[1] = 1
            if beat_list[-2].subject == beat_list[-3].subject: pairings[2] = 1
        if len(beat_list) >= 4:
            if beat_list[-1].subject == beat_list[-4].subject: pairings[3] = 1
            if beat_list[-2].subject == beat_list[-4].subject: pairings[4] = 1
            if beat_list[-3].subject == beat_list[-4].subject: pairings[5] = 1
        if len(beat_list) >= 5:
            if beat_list[-1].subject == beat_list[-5].subject: pairings[6] = 1
            if beat_list[-2].subject == beat_list[-5].subject: pairings[7] = 1
            if beat_list[-3].subject == beat_list[-5].subject: pairings[8] = 1
            if beat_list[-4].subject == beat_list[-5].subject: pairings[9] = 1
        if len(beat_list) >= 6:
            if beat_list[-1].subject == beat_list[-6].subject: pairings[10] = 1
            if beat_list[-2].subject == beat_list[-6].subject: pairings[11] = 1
            if beat_list[-3].subject == beat_list[-6].subject: pairings[12] = 1
            if beat_list[-4].subject == beat_list[-6].subject: pairings[13] = 1
            if beat_list[-5].subject == beat_list[-6].subject: pairings[14] = 1
        if len(beat_list) >= 7:
            if beat_list[-1].subject == beat_list[-7].subject: pairings[15] = 1
            if beat_list[-2].subject == beat_list[-7].subject: pairings[16] = 1
            if beat_list[-3].subject == beat_list[-7].subject: pairings[17] = 1
            if beat_list[-4].subject == beat_list[-7].subject: pairings[18] = 1
            if beat_list[-5].subject == beat_list[-7].subject: pairings[19] = 1
            if beat_list[-6].subject == beat_list[-7].subject: pairings[20] = 1
        if len(beat_list) >= 8:
            if beat_list[-1].subject == beat_list[-8].subject: pairings[21] = 1
            if beat_list[-2].subject == beat_list[-8].subject: pairings[22] = 1
            if beat_list[-3].subject == beat_list[-8].subject: pairings[23] = 1
            if beat_list[-4].subject == beat_list[-8].subject: pairings[24] = 1
            if beat_list[-5].subject == beat_list[-8].subject: pairings[25] = 1
            if beat_list[-6].subject == beat_list[-8].subject: pairings[26] = 1
            if beat_list[-6].subject == beat_list[-8].subject: pairings[27] = 1
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
            out += "Subjects -6 und -7 sind gleich.\t"
        else:
            out += "Subjects -6 und -7 sind nicht gleich.\t"
        if self.numbers[21]:
            out += "Subjects -1 und -8 sind gleich.\t"
        else:
            out += "Subjects -1 und -8 sind nicht gleich.\t"
        if self.numbers[21]:
            out += "Subjects -2 und -8 sind gleich.\t"
        else:
            out += "Subjects -2 und -8 sind nicht gleich.\t"
        if self.numbers[21]:
            out += "Subjects -3 und -8 sind gleich.\t"
        else:
            out += "Subjects -3 und -8 sind nicht gleich.\t"
        if self.numbers[21]:
            out += "Subjects -4 und -8 sind gleich.\t"
        else:
            out += "Subjects -4 und -8 sind nicht gleich.\t"
        if self.numbers[21]:
            out += "Subjects -5 und -8 sind gleich.\t"
        else:
            out += "Subjects -5 und -8 sind nicht gleich.\t"
        if self.numbers[21]:
            out += "Subjects -6 und -8 sind gleich.\t"
        else:
            out += "Subjects -6 und -8 sind nicht gleich.\t"
        if self.numbers[21]:
            out += "Subjects -7 und -8 sind gleich."
        else:
            out += "Subjects -7 und -8 sind nicht gleich."
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
                "Subjects -6 und -7 sind gleich?",
                "Subjects -1 und -8 sind gleich?",
                "Subjects -2 und -8 sind gleich?",
                "Subjects -3 und -8 sind gleich?",
                "Subjects -4 und -8 sind gleich?",
                "Subjects -5 und -8 sind gleich?",
                "Subjects -6 und -8 sind gleich?",
                "Subjects -7 und -8 sind gleich?"]


class X_InvisibleCount(Feature):
    def calculateNumbers(self, context, block):
        i = 0
        for beat in block:
            if beat.invisible: i += 1
        return [i, 100*float(i)/len(block)]

    def getText(self):
        return "Im Block sind " + str(self.numbers[0]) + " unsichtbare beats, also "+str(self.numbers[1])+"%."

    def getNames(self):
        return ["Anzahl unsichtbarer Beats im aktuellen Block", "Anteil unsichtbarer Beats im aktuellen Block"]


class C01_PersonAnalyzer(Feature):
    def calculateNumbers(self, context, block):
        person_histogram = {}
        person_beat_count = 0
        for beat in context["BeatList"]:
            if beat.subject.type == PERSON:
                person_beat_count += 1
                if beat.subject in person_histogram:
                    person_histogram[beat.subject] += 1
                else:
                    person_histogram[beat.subject] = 1
        main_characters = set()
        protagonist_beat_count = 0
        protagonist = block[-1].subject
        for person in person_histogram:
            if person_histogram[person] >= person_beat_count / len(person_histogram):
                main_characters.add(person)
            if person_histogram[person] >= protagonist_beat_count:
                protagonist = person
                protagonist_beat_count = person_histogram[person]
        if protagonist_beat_count > 0 and "protagonist" in context:
            if context["protagonist"] != protagonist:
                protagonistChange = 1
            else: protagonistChange = 0
        else: protagonistChange = 0
        context["protagonist"] = protagonist
        main_character_block_beat_count = 0
        protagonist_block_beat_count = 0
        for beat in block:
            if beat.subject in main_characters:
                main_character_block_beat_count += 1
            if beat.subject == protagonist:
                protagonist_block_beat_count += 1
        lastBeatsFeatureProtagonist = [0,0,0]
        if len(context["BeatList"]) >= 3:
            if context["BeatList"][-3].subject == protagonist:
                lastBeatsFeatureProtagonist[0]=1
        if len(context["BeatList"]) >= 2:
            if context["BeatList"][-2].subject == protagonist:
                lastBeatsFeatureProtagonist[1]=1
        if context["BeatList"][-1].subject == protagonist:
            lastBeatsFeatureProtagonist[2]=1
        protagonist_ratio = 0
        if person_beat_count > 0: protagonist_ratio = float(protagonist_beat_count) / person_beat_count
        return [len(person_histogram), len(main_characters),
                float(main_character_block_beat_count) / len(block),
                protagonist_ratio, protagonistChange,
                float(protagonist_block_beat_count) / len(block)] + lastBeatsFeatureProtagonist


    def getText(self):
        out = "Bisher kamen " + str(self.numbers[0]) + " Figuren vor.\t"
        out += "Es gibt " + str(self.numbers[1]) + " Hauptfiguren.\t"
        out += str(round(self.numbers[2]*100)) + "% der Beats im aktuellen Block handeln von Hauptfiguren.\t"
        out += "Der Protagonist kommt in " + str(round(self.numbers[3]*100)) + "% der Beats vor.\t"
        if self.numbers[4]:
            out += "Der Protagonist hat sich in diesem Block geändert.\t"
        else:
            out += "Es ist der gleiche Protagonist wie bisher.\t"
        out += "Der Protagonist kommt in " + str(round(self.numbers[5]*100)) + "% der Beats des aktuellen Blocks vor.\t"
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


class X_DecidedShots(Feature):
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


class X_ShotHistogram(Feature):
    def calculateNumbers(self, context, block):
        shot_histogram = [0, 0, 0, 0, 0, 0, 0]
        #shot_histogram[context["BeatList"][0].shot] += 1
        total = 0
        for block in context["BygoneBlocks"]:
                shot_histogram[block[-1].shot] += 1
                total += 1
        for i in range(0, len(shot_histogram)):
            if total > 0: shot_histogram[i] = float(shot_histogram[i]) / total
        return shot_histogram

    def getText(self):
        out = ""
        for i in range(0, 7):
            out += str(round(self.numbers[i]*100)) + "% " + SHOT_NAMES[i] + ".\t"
        return out.strip("\t")

    def getNames(self):
        return ["Anteil " + SHOT_NAMES[0], "Anteil " + SHOT_NAMES[1], "Anteil " + SHOT_NAMES[2],
                "Anteil " + SHOT_NAMES[3], "Anteil " + SHOT_NAMES[4], "Anteil " + SHOT_NAMES[5],
                "Anteil " + SHOT_NAMES[6]]


class X_PersonsInTheShot(Feature):
    def calculateNumbers(self, context, block):
        beat_list = copy(context["BeatList"])
        last_shot_id = beat_list[-1].shotId
        emo_persons = {}
        say_persons = {}
        act_persons = {}
        for beat in beat_list:
            if beat.shotId == last_shot_id:
                if beat.subject in emo_persons.keys():
                    if beat.type == EXPRESS:
                        emo_persons[beat.subject] += 1
                else:
                    emo_persons[beat.subject] = 0
                if beat.subject in say_persons.keys():
                    if beat.type == SAYS:
                        say_persons[beat.subject] += 1
                else:
                    say_persons[beat.subject] = 0
                if beat.subject in act_persons.keys():
                    if beat.type == ACTION:
                        act_persons[beat.subject] += 1
                else:
                    act_persons[beat.subject] = 0
        last_five = []
        i = 1
        while i < len(beat_list) and len(last_five) < 5:
            if not beat_list[-i].subject in last_five:
                last_five.append(beat_list[-i].subject)
            i += 1
        emo_persons_array = []
        say_persons_array = []
        act_persons_array = []
        for person in last_five:
            if person in emo_persons.keys():
                emo_persons_array.append(emo_persons[person])
            if person in say_persons.keys():
                say_persons_array.append(say_persons[person])
            if person in act_persons.keys():
                act_persons_array.append(act_persons[person])
        while len(emo_persons_array) < 5:
            emo_persons_array.append(0)
        while len(say_persons_array) < 5:
            say_persons_array.append(0)
        while len(act_persons_array) < 5:
            act_persons_array.append(0)
        return emo_persons_array + say_persons_array + act_persons_array

    def getText(self):
        out = ""
        for i in range(0, 5):
            out += "Die " + str(i) + ".letzte Figur hat seit dem letzten Schnitt " + str(
                self.numbers[i]) + " mal Emotionen gezeigt.\t"
        for i in range(5, 10):
            out += "Die " + str(i - 5) + ".letzte Figur hat seit dem letzten Schnitt " + str(
                self.numbers[i]) + " mal geredet.\t"
        for i in range(10, 15):
            out += "Die " + str(i - 10) + ".letzte Figur hat seit dem letzten Schnitt " + str(
                self.numbers[i]) + " mal gehandelt.\t"
        return out.strip("\t")

    def getNames(self):
        names = []
        for i in range(0, 5):
            names.append("Anzahl der Emotionalen Beats der " + str(i) + ".letzten Figur seit dem letzten Schnitt")
        for i in range(0, 5):
            names.append("Anzahl der Speak-Beats der " + str(i) + ".letzten Figur seit dem letzten Schnitt")
        for i in range(0, 5):
            names.append("Anzahl der Act-Beats der " + str(i) + ".letzten Figur seit dem letzten Schnitt")
        return names


class X_ShowingObject(Feature):
    def calculateNumbers(self, context, block):
        showing_only_objects = True
        no_visible_beats = True
        for beat in block:
            if not((beat.type in [INTRODUCE, SHOW] and beat.subject.type == OBJECT) or beat.invisible):
                showing_only_objects = False
            if beat.type in [INTRODUCE, SHOW] and not beat.invisible:
                no_visible_beats = False
        if showing_only_objects and not no_visible_beats:
            if len(context["BygoneBlocks"]) > 0:
                if context["BygoneBlocks"][-1][-1].shot != DETAIL:
                    return [2]
                else:
                    return [-1]
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


class X_ShowingPlace(Feature):
    def calculateNumbers(self, context, block):
        showing_no_place = True
        no_visible_beats = True
        for beat in block:
            if not((beat.type in [INTRODUCE, SHOW] and beat.subject.type == PLACE) or beat.invisible):
                showing_no_place = False
            if beat.type in [INTRODUCE, SHOW] and not beat.invisible:
                no_visible_beats = False
        if showing_no_place and not no_visible_beats:
            if len(context["BygoneBlocks"]) > 0:
                if context["BygoneBlocks"][-1][-1].shot in range(FULL_SHOT,EXTREME_LONG_SHOT+1):
                    return [2]
                else:
                    return [-1]
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


class X_ShowingPerson(Feature):
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


class C02_Linetargets(Feature):
    def calculateNumbers(self, context, block):
        person_histogram = {}
        person_beat_count = 0
        for beat in context["BeatList"]:
            if beat.subject.type == PERSON:
                person_beat_count += 1
                if beat.subject in person_histogram:
                    person_histogram[beat.subject] += 1
                else:
                    person_histogram[beat.subject] = 1
        main_characters = set()
        protagonist_beat_count = 0
        protagonist = context["BeatList"][0].subject
        for person in person_histogram:
            if person_histogram[person] >= person_beat_count / len(person_histogram):
                main_characters.add(person)
            if person_histogram[person] >= protagonist_beat_count:
                protagonist = person
                protagonist_beat_count = person_histogram[person]

        number_of_linetargets = 0
        last_linetarget = None
        for beat in block:
            if beat.linetarget:
                number_of_linetargets += 1
                last_linetarget = beat.linetarget
        last_linetarget_is_subjects = []
        for i in range(1, 9):
            if len(context["BeatList"]) > i:
                if context["BeatList"][-i].subject is last_linetarget:
                    last_linetarget_is_subjects.append(1)
                else: last_linetarget_is_subjects.append(0)
            else: last_linetarget_is_subjects.append(0)
        if last_linetarget:
            return last_linetarget_is_subjects + [number_of_linetargets, last_linetarget.type != PERSON,
                                               last_linetarget in main_characters,
                                               last_linetarget == protagonist]
        else:
            return last_linetarget_is_subjects + [number_of_linetargets, 0, last_linetarget in main_characters,
                                               last_linetarget == protagonist]

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


class X_HandwrittenCutCriteria(Feature): #TODO: aktuellen Block berücksichtigen! Ist alles um einen Block verschoben? - Nein, shot wird benutzt.
    def calculateNumbers(self, context, block):
        cut_criteria = []
        if len(context["BygoneBlocks"]) >= 2:
            if context["BygoneBlocks"][-1][0].subject == context["BygoneBlocks"][-2][-1].subject and (
                context["BygoneBlocks"][-2][-1].shot >= MEDIUM_SHOT and
                context["BygoneBlocks"][-1][0].type in [SAYS, ACTION]) or (
                context["BygoneBlocks"][-2][-1].shot >= CLOSEUP and context["BygoneBlocks"][-1][0].type == SAYS):
                cut_criteria.append(0)
            else:
                cut_criteria.append(1)
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
                if cut: cut_criteria.append(1)
                else: cut_criteria.append(0)
            else: cut_criteria.append(1)
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
                if cut: cut_criteria.append(1)
                else: cut_criteria.append(0)
            else: cut_criteria.append(1)
            if context["BygoneBlocks"][-1][0].subject != context["BygoneBlocks"][-2][0].subject and\
               context["BygoneBlocks"][-1][0].type == SAYS and context["BygoneBlocks"][-2][0].type == SAYS:
                cut_criteria.append(1)
            else: cut_criteria.append(0)
        else:
            cut_criteria.append(1)
            cut_criteria.append(1)
            cut_criteria.append(1)
            cut_criteria.append(0)
        if len(context["BygoneBlocks"]) >= 2:
            if context["BygoneBlocks"][-2][-1].shot == DETAIL:
                cut_criteria.append(1)
            else: cut_criteria.append(0)
        else: cut_criteria.append(0)
        if len(context["BygoneBlocks"]) >= 1:
            if context["BygoneBlocks"][-1][0].type == EXPRESS:
                cut_criteria.append(1)
            else: cut_criteria.append(0)
        else: cut_criteria.append(0)
        return cut_criteria

    def getText(self):
        return "Die Handarbeit sagt " + str(self.numbers)

    def getNames(self):
        return ["Handgeschriebenes Schnittkriterium 1.", "Handgeschriebenes Schnittkriterium 2.",
                "Handgeschriebenes Schnittkriterium 3.", "Handgeschriebenes Schnittkriterium 4.",
                "Handgeschriebenes Schnittkriterium 5.", "Handgeschriebenes Schnittkriterium 6."]


class D01_ExpositoryPhaseOfTheScene(Feature):
    def calculateNumbers(self, context, block):
        if context["ExpositoryPhase"]:
            shown_place = False
            emotionally_situated_persons = set()
            all_persons = set()
            for beat in block: all_persons.add(beat.subject)
            beat_list = copy(context["BeatList"])
            for beat in beat_list:
                all_persons.add(beat.subject)
                if beat.linetarget and beat.linetarget.type == PERSON: all_persons.add(beat.linetarget)
                if beat.type == EXPRESS: emotionally_situated_persons.add(beat.subject)
                if beat.type == SHOW and beat.subject.type == PERSON: emotionally_situated_persons.add(beat.subject)
                if beat.type in [INTRODUCE, SHOW] and beat.subject.type == PLACE: shown_place = True
            if (shown_place and emotionally_situated_persons is all_persons) or (shown_place and len(beat_list) > 15):
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


class X_TalkersGoSilent(Feature):
    def calculateNumbers(self, context, block):
        talkers_go_silent_value = max(context["TalkersGoSilentValue"]-1,0)
        if block[-1].type == EXPRESS:
            beat_list = context["BeatList"]
            i = 1
            expresses = 1
            actor = None
            while len(beat_list) > i:
                i += 1
                if not actor and beat_list[-i].type == EXPRESS:
                    expresses += 1
                    continue
                if beat_list[-i].type == ACTION:
                    actor = beat_list[-i].subject
                    continue
                if actor:
                    if (beat_list[-i].type == SAYS) and (beat_list[-i].subject != actor):
                        context["TalkersGoSilentValue"] = expresses+5
                        return [expresses+5]
                    else: return [talkers_go_silent_value]
                else: return [talkers_go_silent_value]
            return [talkers_go_silent_value]
        else: return [talkers_go_silent_value]

    def getText(self):
        return "Der 'Tratscher-werden-leise-Wert' ist "+str(self.numbers[0])

    def getNames(self):
        return ["Tratscher-werden-leise-Wert"]


class X_WhatDidSubjectDo(Feature):
    def calculateNumbers(self, context, block):
        beats_with_this_subject_count = [0, 0, 0, 0, 0]
        subject_was_linetarget_count = 0
        for beat in context["BeatList"]:
            if beat.subject == block[-1].subject:
                beats_with_this_subject_count[beat.type] += 1
            if beat.linetarget and beat.linetarget == block[-1].subject:
                subject_was_linetarget_count += 1
        return beats_with_this_subject_count + [subject_was_linetarget_count]

    def getText(self):
        out = ""
        for i, type in enumerate(BEAT_TYPE_NAMES):
            out += "Das letzte Subject ist in " + str(
                self.numbers[i]) + " " + type + "-Beats als Subject vorgekommen.\t"
        return out + "Das letzte Subject war " + str(self.numbers[5]) + " mal Linetarget."

    def getNames(self):
        return ["Anzahl " + type + "-Beats, in denen das letzte Subject auch Subject war" for type in
                BEAT_TYPE_NAMES] + ["Anzahl Beats in denen das Subject des letzten Beats Linetarget war"]


class X_BlockSimilarity(Feature):
    def calculateNumbers(self, context, block):
        similarity_factors = []
        blocks_to_compare = 7
        for i in range(1, min(blocks_to_compare, len(context["BygoneBlocks"]))):
            factor = 0
            block_index = 0
            bygone_index = 0
            while len(block) > block_index and len(context["BygoneBlocks"][-i]) > bygone_index:
                if block[block_index].type == context["BygoneBlocks"][-i][bygone_index].type:
                    factor += 1
                    block_index += 1
                    bygone_index += 1
                else:
                    if len(context["BygoneBlocks"][-i]) > bygone_index + 1 and\
                       block[block_index].type == context["BygoneBlocks"][-i][bygone_index + 1].type:
                        bygone_index += 1
                    elif len(block) > block_index + 1 and\
                         block[block_index + 1].type == context["BygoneBlocks"][-i][bygone_index].type:
                        block_index += 1
                    else:
                        block_index += 1
                        bygone_index += 1
            similarity_factors.append(factor)
        while len(similarity_factors) < blocks_to_compare: similarity_factors.append(0)
        return similarity_factors

    def getText(self):
        out = ""
        for i, factor in enumerate(self.numbers):
            out += "Der " + str(i) + ". letzte Block hat eine Ähnlichkeit von " + str(factor) + "\t"
        return out.strip("\t")

    def getNames(self):
        return ["Ähnlichkeit des " + str(x) + ". letzten Blocks zum aktuellen Block" for x in range(self.numbers)]


class X_SameShotSince(Feature):
    def calculateNumbers(self, context, block):
        lastShot = None
        if len(context["BygoneBlocks"]) >= 1:
            lastShot = context["BygoneBlocks"][-1][0].shot
        count = 1
        while len(context["BygoneBlocks"]) > count and context["BygoneBlocks"][-1 * count - 1][0].shot == lastShot:
            count += 1
        return [count]

    def getText(self):
        return "Eine andere Einstellungsgröße liegt " + str(self.numbers[0]) + " Blöcke zurück."

    def getNames(self):
        return ["Anzahl Blöcke seit denen die letzte Einstellungsgröße zu sehen war"]


class X_AppearanceAnalyzer(Feature):
    def calculateNumbers(self, context, block):
        introduce_since = 0
        appearance_counter = 0
        for bygone_block in context["BygoneBlocks"]:
            person_introduce = False
            for beat in bygone_block:
                if beat.type == INTRODUCE and beat.subject.type == PERSON:
                    person_introduce = True
            if person_introduce:
                introduce_since = 0
                appearance_counter += 1
            else:
                introduce_since += 1
        person_introduce = False
        for beat in block:
            if beat.type == INTRODUCE and beat.subject.type == PERSON:
                person_introduce = True
        if person_introduce:
            introduce_since = 0
            appearance_counter += 1
        else:
            introduce_since += 1
        return [appearance_counter, introduce_since]

    def getText(self):
        return "Es gab "+str(self.numbers[0])+" Auftritte.\tDer letzte Auftritt liegt "+\
               str(self.numbers[1])+" Blöcke zurück."

    def getNames(self):
        return ["Anzahl Auftritte", "Anzahl Blöcke seit letztem Auftritt"]


class X_ShowAnalyzer(Feature):
    def calculateNumbers(self, context, block):
        shows_since = 0
        shows_counter = 0
        for bygone_block in context["BygoneBlocks"]:
            shows_in_the_block = False
            for beat in bygone_block:
                if beat.type == SHOW:
                    shows_in_the_block = True
            if shows_in_the_block:
                shows_since = 0
                shows_counter += 1
            else:
                shows_since += 1
        shows_in_the_block = False
        for beat in block:
            if beat.type == SHOW:
                shows_in_the_block = True
        if shows_in_the_block:
            shows_since = 0
            shows_counter += 1
        else:
            shows_since += 1
        return [shows_counter, shows_since]

    def getText(self):
        return "Es gab "+str(self.numbers[0])+" Blöcke mit Show-Beats.\tDer Show-Beat liegt "+\
               str(self.numbers[1])+" Blöcke zurück."

    def getNames(self):
        return ["Anzahl Blöcke mit Show-Beat", "Anzahl Blöcke seit letztem Show-Beat"]


class X_DialogueBlocks(Feature):
    def calculateNumbers(self, context, block):
        dialogue_blocks = []
        subjects = set()
        for beat in block:
            subjects.add(beat.subject)
            if beat.linetarget and beat.linetarget.type == PERSON:
                subjects.add(beat.linetarget)
        if len(subjects) == 2: dialogue_blocks.append(1)
        else: dialogue_blocks.append(0)
        for i in range(-1,-4,-1):
            if len(context["BygoneBlocks"]) >= -i:
                subjects = set()
                for beat in context["BygoneBlocks"][i]:
                    subjects.add(beat.subject)
                    if beat.linetarget and beat.linetarget.type == PERSON:
                        subjects.add(beat.linetarget)
                if len(subjects) == 2: dialogue_blocks.append(1)
                else: dialogue_blocks.append(0)
            else: dialogue_blocks.append(0)
        return dialogue_blocks

    def getText(self):
        if self.numbers[0]: out = "Der aktuelle Block ist ein Dialogblock."
        else: out = "Der aktuelle Block ist kein Dialogblock."
        for i in range(1,len(self.numbers)):
            if self.numbers[i]: out += "\tDer "+str(i)+". letzte Block war ein Dialogblock."
            else: out += "\tDer "+str(i)+". letzte Block war kein Dialogblock."
        return out

    def getNames(self):
        names = ["Aktueller Block ist Dialogblock?"]
        for i in range(1,len(self.numbers)): names.append(str(i)+". letzter Block war Dialogblock?")
        return names


class X_DialogueAnswerExpected(Feature):
    def calculateNumbers(self, context, block):
        subjects = set()
        for beat in block:
            subjects.add(beat.subject)
        if block[-1].type == SAYS and block[-1].linetarget and not block[-1].linetarget in subjects:
            return [1]
        elif len(block) >= 2 and block[-1].type == EXPRESS and block[-2].type == SAYS and block[-2].linetarget and\
            not block[-2].linetarget in subjects:
            return [2]
        else: return [0]

    def getText(self):
        if self.numbers[0]: return "Der aktuelle Block lässt eine Antwort im Dialog erwarten."
        else: return "Die Struktur des aktuellen Blocks lässt nicht unbedingt eine Antwort in einem Dialog erwarten."

    def getNames(self):
        return ["Aktueller Block lässt Antwort erwarten?"]


class X_DialogueAnswerWasExpected(Feature):
    def calculateNumbers(self, context, block):
        if len(context["BygoneBlocks"]) >= 1:
            answering_subjects = set()
            for beat in block:
                if beat.type == SAYS:
                    answering_subjects.add(beat.subject)
            previous_subjects = set()
            for beat in context["BygoneBlocks"][-1]:
                previous_subjects.add(beat.subject)
            if context["BygoneBlocks"][-1][-1].type == SAYS and context["BygoneBlocks"][-1][-1].linetarget and\
               not context["BygoneBlocks"][-1][-1].linetarget in previous_subjects:
                if context["BygoneBlocks"][-1][-1].linetarget and\
                   context["BygoneBlocks"][-1][-1].linetarget in answering_subjects:
                    return [1, 1]
                else: return [1, 0]
            elif len(context["BygoneBlocks"][-1]) >= 2 and context["BygoneBlocks"][-1][-1].type == EXPRESS and\
                 context["BygoneBlocks"][-1][-2].type == SAYS and context["BygoneBlocks"][-1][-2].linetarget and\
                 (len(block) < 2 or not block[-2].linetarget in previous_subjects):
                if context["BygoneBlocks"][-1][-2].linetarget and\
                   context["BygoneBlocks"][-1][-2].linetarget in answering_subjects:
                    return [2, 1]
                else: return [2, 0]
            else: return [0, 0]
        else: return [0, 0]

    def getText(self):
        if self.numbers[0] and self.numbers[1]:
            return "Der letzte vergangene Block lässt eine Antwort im Dialog erwarten und diese Antwort kommt im aktuellen Block."
        elif self.numbers[0] and not self.numbers[1]:
            return "Der letzte vergangene Block lässt eine Antwort im Dialog erwarten, was aber durch den aktuellen Block als falsche Annahme entlarvt wird."
        else: return "Die Struktur des letzten vergangenen Blocks lässt ohnehin nicht unbedingt eine Antwort in einem Dialog erwarten."

    def getNames(self):
        return ["Letzter vergangener Block lässt Antwort erwarten?", "Erwartete Antwort wird im aktuellen Block gegeben?"]


class X_NumberOfPersonInTheBlock(Feature):
    def calculateNumbers(self, context, block):
        persons = set()
        for beat in block:
            if beat.subject.type == PERSON: persons.add(beat.subject)
            if beat.linetarget and beat.linetarget.type == PERSON: persons.add(beat.linetarget)
        return [len(persons),float(len(persons)*100)/len(block)]

    def getText(self):
        return "Im aktuellen Block kommen "+str(self.numbers[0])+" Personen vor. Das sind " + str(
            self.numbers[1]) + "% der Beatzahl."

    def getNames(self):
        return ["Anzahl Personen im aktuellen Block", "Anteil Personenzahl an den Gesamtbeats"]


class X_KnownSubjectsInBlock(Feature):
    def calculateNumbers(self, context, block):
        subjects = set()
        for bygone_block in context["BygoneBlocks"]:
            for beat in bygone_block:
                subjects.add(beat.subject)
        number_of_beats_with_known_subjects_in_the_block = 0
        for beat in block:
            if beat.subject in subjects: number_of_beats_with_known_subjects_in_the_block += 1
        return [number_of_beats_with_known_subjects_in_the_block,
                float(100 * number_of_beats_with_known_subjects_in_the_block) / len(block)]

    def getText(self):
        return "Im aktuellen Block handeln " + str(
            self.numbers[0]) + " Beats von vorher bekannten Personen, was " + str(self.numbers[1]) + "% der Beats sind."

    def getNames(self):
        return ["Anzahl Beats im aktuellen Block mit vorher bekannten Subjects",
                "Anteil Beats mit vorher bekannten Subjects"]


class X_CutInTheSentence(Feature):
    def calculateNumbers(self, context, block):
        last_say_subject = None
        if len(context["BygoneBlocks"]) >= 1:
            for beat in context["BygoneBlocks"][-1]:
                if beat.type == SAYS:
                    last_say_subject = beat.subject
        cut_in_the_sentence = 0
        for beat in block:
            if not beat.type in [SAYS, EXPRESS] and not beat.invisible:
                last_say_subject = None
            if beat.type == SAYS:
                if beat.subject == last_say_subject:
                    cut_in_the_sentence = 1
                else:
                    last_say_subject = beat.subject
        return [cut_in_the_sentence]

    def getText(self):
        if self.numbers[0]: return "Es gab eine Unterbrechung im Satz."
        else: return "Es gab keine Unterbechung im Satz."

    def getNames(self):
        return ["Unterbrechung im Satz?"]


class X_ChangeInExpression(Feature):
    def calculateNumbers(self, context, block):
        expressers = {}
        for i in range(len(block)):
            beat = block[-i]
            if beat.type == EXPRESS:
                if beat.subject in expressers:
                    expressers[beat.subject] += 1
                else: expressers[beat.subject] = 0
        results = [len([x for x in expressers if x > 0])]
        if len(context["BygoneBlocks"]) >= 1:
            for i in range(len(context["BygoneBlocks"][-1])):
                beat = context["BygoneBlocks"][-1][-i]
                if beat.type == EXPRESS:
                    if beat.subject in expressers:
                        expressers[beat.subject] += 1
                    else: expressers[beat.subject] = 0
        results.append(len([expressers[x] for x in expressers if expressers[x] > 0]))
        return results

    def getText(self):
        return str(self.numbers[0]) + " Personen haben ihre Expression im aktuellen Block verändert und " + str(
            self.numbers[1]) + " Personen seit dem vorherigen Block."

    def getNames(self):
        return ["Anzahl Subjects die ihre Expression im aktuellen Block geändert haben.",
                "Anzahl Subjects die ihre Expression seit dem vorherigen Block geändert haben."]


class X_BackgroundAction(Feature):
    def calculateNumbers(self, context, block):
        subjects = {}
        if len(context["BygoneBlocks"]) >= 1:
            for beat in context["BygoneBlocks"][-1]:
                if beat.type == ACTION:
                    if beat.subject in subjects:
                        subjects[beat.subject] += 1
                    else: subjects[beat.subject] = 1
        for beat in block:
            if beat.type == ACTION:
                if beat.subject in subjects:
                    subjects[beat.subject] += 1
                else: subjects[beat.subject] = 1
        main_count = 0
        main_subject = None
        for subject in subjects:
            if subjects[subject] >= main_count:
                main_count = subjects[subject]
                main_subject = subject
        background_action = 0
        background_acter = None
        for beat in block:
            if beat.type == ACTION and beat.subject != main_subject:
                background_action = 1
                background_acter = beat.subject
        if background_action:
            for beat in block:
                if beat.type == ACTION and beat.linetarget and\
                   beat.linetarget != background_acter and not beat.invisible:
                    background_action = 0
        return [background_action]

    def getText(self):
        text = ["Im aktuellen Block gibt es ","keine ","Handlung im Hintergrund."]
        return "".join([text[x] for x in range(3) if not x%2*self.numbers[0]])

    def getNames(self):
        return ["Handlung im Hintergrund?"]


# =============================== Helper Methods ===============================
def getAllFeatureClasses():
    """
    Returns a list of all subclasses of Feature defined in, or imported into this module.
    """
    featureClassList = []
    for name, obj in inspect.getmembers(CURRENT_MODULE):
        if inspect.isclass(obj) and issubclass(obj, Feature) and (obj != Feature):
            featureClassList.append(obj)
    return featureClassList


def createBeatList(context, block):
    """
    This function reconstructs a beatList from the BygoneBlocks in the context and the given new block.
    The beatList is saved in the context. It is necessary to do this before calculating a featureLine,
     because otherwise there is no correct BeatList in the context, which is used by the Feature-Classes.
    """
    context["BeatList"] = [b for b in itertools.chain(*context["BygoneBlocks"])] + block
    return context