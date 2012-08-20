#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
from sklearn import preprocessing
import scipy.optimize as opt

from Classify import getDataMatrix
from Config import TRAIN_FILES
from XValidation import ParallelXValidation

def tuneParametersForSVM(files, scaler, reference_data, fake_decisions=False):
    def fitnessFunction(parameters, files, scaler, fake_decisions):
        return ParallelXValidation(files, scaler, fake_decisions, C=max(0.0,parameters[0]), gamma=max(1e-323,parameters[1]))

    #start_vector = np.array([len(reference_data), 1.0/len(reference_data[0])])
    start_vector = np.array([2582.61517656, 0.00036375303213])
    print("Starting optimization.")
    tuned_parameters = opt.fmin_powell(func=fitnessFunction, x0=start_vector, args=(files, scaler, fake_decisions))
    print("____________________________________")
    print("Results:")
    print("\tC="+str(tuned_parameters[0]))
    print("\tgamma="+str(tuned_parameters[1]))

# =============================== Main =========================================
def main():
    reference_data, _ = getDataMatrix(TRAIN_FILES)
    scaler = preprocessing.Scaler()
    scaler.fit(reference_data)
    tuneParametersForSVM(TRAIN_FILES, scaler, reference_data, True)

if __name__ == "__main__":
    main()