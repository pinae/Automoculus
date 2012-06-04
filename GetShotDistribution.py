#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================== Imports ======================================
from multiprocessing import Process, Queue, Lock
import cPickle
from Classify import getDomain, classifyForDistribution
from Config import SHOT_NAMES
import orange
import sys

# =============================== Main =========================================
def main():
    domain = getDomain(orange.EnumVariable(name="Shot", values=SHOT_NAMES))
    file = open("/home/jonny/Programmierung/Automoculus - Featurizer/trained_classifiers",'rb')
    classifiers = cPickle.Unpickler(file).load()
    file.close()
    try:
        file = open("/home/jonny/Programmierung/Automoculus - Featurizer/decisionHistory.txt",'r')
        lines = file.readlines()
    except IOError:
        lines = []
    decisionHistory = []
    for line in lines:
        decisionHistory.append(SHOT_NAMES[line])
    file.close()
    dist = classifyForDistribution(domain,sys.argv[1],classifiers,decisionHistory)
    file = open("/home/jonny/Programmierung/Automoculus - Featurizer/decisions.txt",'w')
    diststr = ""
    for value in dist:
        diststr += str(value)+"\t"
    file.write(diststr.strip("\t"))
    file.close()

if __name__ == "__main__":
    main()