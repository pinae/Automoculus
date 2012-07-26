#!/usr/bin/python
# -*- coding: utf-8 -*-
from os import path


# =============================== Constants ====================================

DELIMITER = "\t"
INTRODUCE, EXPRESS, SAYS, ACTION, SHOW = range(0, 5)
BEAT_TYPE_NAMES = ["introduce", "expresses", "says", "action", "show"]
DETAIL, CLOSEUP, MEDIUM_SHOT, AMERICAN_SHOT, FULL_SHOT, LONG_SHOT, EXTREME_LONG_SHOT = range(0, 7)
SHOT_NAMES = ["detail", "closeup", "medium_shot", "american_shot", "full_shot", "long_shot", "extreme_long_shot"]
PERSON, OBJECT, PLACE = range(0, 3)
DEMONSTRAT_TYPE_NAMES = ["person", "object", "place"]
TRAIN_FILES = ["Berg der Versuchung - Schwere Stelle.csv", "Double Indemnity - Eingang.csv",
               "Double Indemnity - Identifikation.csv", "Double Indemnity - Leiche.csv",
               "Double Indemnity - Telefonat.csv",
               "Ivanhoe - Ende.csv", "Ivanhoe - Endkampf.csv",
               "Ivanhoe - Gefangennahme.csv", "Ivanhoe - Taverne.csv",
               "Ivanhoe - Turnier.csv",
               "The Count of Monte Christo - Messerkampf.csv", "The Count of Monte Christo - Verschwörer.csv",
               "The Maltese Falcon - Beginn.csv",
               "The Treasure of the Sierra Madre - Ausbeuter.csv",
               "The Treasure of the Sierra Madre - Banditen.csv",
               "The Woman in the Window - Abenteuerlust.csv",
               "The Woman in the Window - Ampel.csv",
               "The Woman in the Window - Bar.csv"]

PROJECT_PATH = path.dirname(path.abspath(__file__))

TRAIN_FILES = [path.abspath(path.join(PROJECT_PATH, "beatscripts", f)) for f in TRAIN_FILES]



