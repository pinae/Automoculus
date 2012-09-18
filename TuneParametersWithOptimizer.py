#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
from sklearn import preprocessing
import scipy.optimize as opt

from Classify import getDataMatrix
from Config import TRAIN_FILES
from XValidation import ParallelXValidation

def tuneParametersForSVM(files, scaler, reference_data, fake_decisions=False, leave_out_class=None):
    def fitnessFunction(parameters, files, scaler, fake_decisions, leave_out_class):
        print("C="+str(max(0.0,parameters[0])))
        print("gamma="+str(max(1e-323,parameters[1])))
        return ParallelXValidation(files, scaler, fake_decisions, C=max(0.0,parameters[0]), gamma=max(1e-323,parameters[1]), leave_out_class=leave_out_class)

    #start_vector = np.array([len(reference_data), 1.0/len(reference_data[0])])
    print("C default: "+str(len(reference_data)))
    print("gamma default: "+str(1.0/len(reference_data[0])))
    start_vector = np.array([1999.85770959, 6.30930490772e-07])
    print("Starting optimization.")
    tuned_parameters = opt.fmin_powell(func=fitnessFunction, x0=start_vector, args=(files, scaler, fake_decisions, leave_out_class), maxfun=179)
    print("____________________________________")
    print("Results:")
    print("\tC="+str(tuned_parameters[0]))
    print("\tgamma="+str(tuned_parameters[1]))
    return tuned_parameters

# =============================== Main =========================================
def main():
    reference_data, _ = getDataMatrix(TRAIN_FILES)
    scaler = preprocessing.Scaler()
    scaler.fit(reference_data)
    tuneParametersForSVM(TRAIN_FILES, scaler, reference_data, True)

if __name__ == "__main__":
    main()