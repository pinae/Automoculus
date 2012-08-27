#!/usr/bin/python
# -*- coding: utf-8 -*-

from sklearn import preprocessing
import numpy as np
from pylab import *

from Classify import getDataMatrix
from Config import TRAIN_FILES
from XValidation import ParallelXValidation

# =============================== Main =========================================
def main():
    files = TRAIN_FILES[:30]
    reference_data, _ = getDataMatrix(files)
    scaler = preprocessing.Scaler()
    scaler.fit(reference_data)
    lines = []

    for C in [1,10,100,1000,2000,3000,4000,5000,7000,10000]:
        line = ""
        for gamma in [10,1,1e-1,1e-2,1e-3,1e-4,1e-5,1e-6,1e-7,1e-8]:
            line += str(ParallelXValidation(files, scaler, True, C=C, gamma=gamma))+"\t"
            print("C: "+str(C)+"\tgamma: "+str(gamma)+"\t:: "+line.split("\t")[-2])
        lines.append(line.rstrip("\t")+"\n")
    file = open("GridSearch_results.csv","w")
    file.writelines(lines)
    file.close()

if __name__ == "__main__":
    main()