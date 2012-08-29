#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
import sys, os
import numpy as np
from matplotlib.patches import Patch
from pylab import *

def gather_results(path):
    listing = os.listdir(path)
    results = {}
    for filename in listing:
        print "current file is: " + path+filename
        result_file = open(path+filename, 'r')
        result_str = result_file.read()
        result_file.close()
        C = float(result_str.decode('utf-8').split("_gamma_is_")[0].split("C_is_")[1])
        gamma = float(result_str.decode('utf-8').split("_Result_is_")[0].split("_gamma_is_")[1])
        result = float(result_str.decode('utf-8').split("_Result_is_")[1])
        if C in results.keys():
            results[C][gamma] = result
        else:
            results[C] = {gamma: result}
    result_table = []
    gammas = []
    for gamma in results[results.keys()[0]]:
        gammas.append(gamma)
    Cs = []
    for C in results.keys():
        Cs.append(C)
    Cs.sort()
    gammas.sort(reverse=True)
    for C in Cs:
        result_line = []
        for gamma in gammas:
            if C in results.keys() and gamma in results[C].keys():
                result_line.append(results[C][gamma])
            else:
                print("C="+str(C)+" gamma="+str(gamma)+" Result fehlt!")
                result_line.append(2.7)
        result_table.append(np.array(result_line))
    data = np.array(result_table)
    print Cs
    print gammas
    print data
    X,Y = meshgrid(np.array(range(len(gammas)+1)), np.array(range(len(Cs)+1)))
    #pcolor(X, Y, data)
    #ax = subplot(111)
    im = imshow(data, cmap=cm.jet)
    im.set_interpolation('nearest')
    #im.set_interpolation('bicubic')
    #im.set_interpolation('bilinear')
    colorbar()
    show()

if __name__ == "__main__":
    gather_results(sys.argv[1])