#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================== Imports ======================================
from multiprocessing import Process, Queue, Lock
import cPickle
from Classify import getDomain, classifyForCutting
from Config import SHOT_NAMES, PROJECT_PATH
import orange
import sys
from os import path

# =============================== Main =========================================
def main():
    domain = getDomain(orange.EnumVariable(name="Shot", values=SHOT_NAMES))
    file = open(path.join(PROJECT_PATH, "trained_classifiers_cutting"),'rb')
    classifiers = cPickle.Unpickler(file).load()
    file.close()
    try:
        file = open(path.join(PROJECT_PATH, "decisionHistory.txt"),'r')
        lines = file.readlines()
    except IOError:
        lines = []
    decisionHistory = []
    for line in lines:
        decisionHistory.append(int(line.split("_")[0]))
    file.close()
    dist = classifyForCutting(domain,sys.argv[1],classifiers,decisionHistory)
    file = open(path.join(PROJECT_PATH, "cut_decisions.txt"),'w')
    diststr = ""
    for value in dist:
        diststr += str(value)+"\t"
    file.write(diststr.strip("\t"))
    file.close()

if __name__ == "__main__":
    main()
