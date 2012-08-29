#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os

from sklearn import preprocessing
import numpy as np

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

    for C in [1,10,100,1000,2000,3000,4000,5000,6000,7000,8000,10000]:
        line = ""
        for gamma in [10,1,1e-1,1e-2,1e-3,1e-4,1e-5,1e-6,1e-7,1e-8]:
            line += str(ParallelXValidation(files, scaler, True, C=C, gamma=gamma))+"\t"
            print("C: "+str(C)+"\tgamma: "+str(gamma)+"\t:: "+line.split("\t")[-2])
        lines.append(line.rstrip("\t")+"\n")
    file = open("GridSearch_results.csv","w")
    file.writelines(lines)
    file.close()

def specific_line(number):
    files = TRAIN_FILES
    reference_data, _ = getDataMatrix(files)
    scaler = preprocessing.Scaler()
    scaler.fit(reference_data)
    C = [1,10,100,1000,2000,3000,4000,5000,6000,7000,8000,10000]
    for gamma in [100,10,1,5e-1,1e-1,5e-2,1e-2,5e-3,1e-3,5e-4,1e-4,5e-5,1e-5,5e-6,1e-6,5e-7,1e-7,5e-8,1e-8,5e-9,1e-9,1e-10,1e-12,1e-15,1e-20]:
        os.system("wget http://www.pinae.net/automoculus/getText.php?text=C_is_" + str(C[number]) + "_gamma_is_" + str(
            gamma) + "_Result_is_" + str(ParallelXValidation(files, scaler, True, C=C[number], gamma=gamma)))
        os.system("rm getText*")

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        specific_line(int(sys.argv[1]))
    else:
        main()