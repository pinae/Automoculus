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
TRAIN_FILES = ["Berg der Versuchung - Schwere Stelle.csv",
               "Double Indemnity - Eingang.csv",
               "Double Indemnity - Identifikation.csv",
               "Double Indemnity - Leiche.csv",
               "Double Indemnity - Telefonat.csv",
               "Double Indemnity - Hinweise.csv",
               "Ivanhoe - Ende.csv",
               "Ivanhoe - Endkampf.csv",
               "Ivanhoe - Gefangennahme.csv",
               "Ivanhoe - Taverne.csv",
               "Ivanhoe - Turnier.csv",
               "The Count of Monte Christo - Elba.csv",
               "The Count of Monte Christo - Diebesgut.csv",
               "The Count of Monte Christo - Messerkampf.csv",
               "The Count of Monte Christo - Verschwoerer.csv",
               "The Count of Monte Christo - Endkampf.csv",
               "The Maltese Falcon - Beginn.csv",
               "The Maltese Falcon - Leiche.csv",
               "The Maltese Falcon - Verfolgung.csv",
               "The Maltese Falcon - Undercover.csv",
               "The Maltese Falcon - Post.csv",
               "The Treasure of the Sierra Madre - Ausbeuter.csv",
               "The Treasure of the Sierra Madre - Banditen.csv",
               "The Treasure of the Sierra Madre - Mieneneinsturz.csv",
               "The Treasure of the Sierra Madre - Misstrauen.csv",
               "The Treasure of the Sierra Madre - Goldverlust.csv",
               "The Woman in the Window - Abenteuerlust.csv",
               "The Woman in the Window - Ampel.csv",
               "The Woman in the Window - Bar.csv",
               "The Woman in the Window - Familienszene.csv",
               "The Woman in the Window - Mord.csv",
               "Quantic Dream - Kara.csv",
               "Assassins Creed Brotherhood - Trailer.csv",
               "Rage - Intro.csv",
               "Dawn of War - Intro.csv",
               "DC Universe Online - Intro.csv",
               "Halo 3 - Trailer.csv",
               "Dragon Age Origins - Sacred Ashes.csv",
               "Warhammer Online - Trailer.csv",
               "Wings of Liberty - Kerrygans Rettung.csv",
               "Wings of Liberty - Kerrygan.csv",
               "Wings of Liberty - Zeratul.csv",
               "World of Warcraft - Wrath of the Lich King.csv",
               "Warcraft III - Arthas betrayal.csv"]

PROJECT_PATH = path.dirname(path.abspath(__file__))

TRAIN_FILES = [path.abspath(path.join(PROJECT_PATH, "beatscripts", f)) for f in TRAIN_FILES]