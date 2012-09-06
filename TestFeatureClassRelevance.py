#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os

from sklearn import preprocessing

from Classify import getDataMatrix
from Config import TRAIN_FILES
from XValidation import ParallelXValidation
from Features import getAllFeatureClasses
from TuneParametersWithOptimizer import tuneParametersForSVM

def TestFeatureClassRelevance(number = None):
    files = TRAIN_FILES[:2]
    feature_Classes = getAllFeatureClasses()
    results = []
    if number:
        reference_data, _ = getDataMatrix(files, leave_out_class=feature_Classes[number])
        scaler = preprocessing.Scaler()
        scaler.fit(reference_data)
        optimized_parameters = tuneParametersForSVM(files, scaler, reference_data, True, leave_out_class=feature_Classes[number])
        results.append((feature_Classes[number], ParallelXValidation(files, scaler, True, C=optimized_parameters[0],
            gamma=optimized_parameters[1], leave_out_class=feature_Classes[number])))
    else:
        for number in range(len(feature_Classes))[3:]:
            reference_data, _ = getDataMatrix(files, leave_out_class=feature_Classes[number])
            scaler = preprocessing.Scaler()
            scaler.fit(reference_data)
            results.append((feature_Classes[number], ParallelXValidation(files, scaler, True, leave_out_class=feature_Classes[number])))
    for result_class, result in results:
        print(str(result_class).split(".")[1]+":"+"\t".join(["" for _ in range(int(round((50-len(str(result_class).split(".")[1]))/8.0)))])+str(result))
        os.system("wget http://www.pinae.net/automoculus/getText.php?text=FeatureClass_is_" +
                  str(result_class).split(".")[1] + "_Result_is_" + str(result))
        os.system("rm getText*")

if __name__ == "__main__":
    print("If you give a number it should be in the range 3,43.")
    if len(sys.argv) >= 2:
        parameter = int(sys.argv[1])
    else:
        parameter = None
    TestFeatureClassRelevance(parameter)