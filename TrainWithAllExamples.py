#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================== Imports ======================================
from multiprocessing import Process
from BeatscriptClassifier import trainWithAllExamples

# =============================== Main =========================================
def main():
    shotProcess = Process(target=trainWithAllExamples, args=(True))
    shotProcess.start()
    cutProcess = Process(target=trainWithAllExamples, args=(False))
    cutProcess.start()
    shotProcess.join()
    cutProcess.join()

if __name__ == "__main__":
    main()