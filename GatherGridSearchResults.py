#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
import sys, os
import numpy as np
from matplotlib.colors import LogNorm
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
    Cs = []
    for C in results.keys():
        Cs.append(C)
    Cs.sort()
    gammas = []
    for gamma in results[max([results.keys()[x] for x in range(len(Cs))])]:
        gammas.append(gamma)
    gammas.sort(reverse=True)
    m_file = open(path+"../missing_notes.txt",'w')
    for C in Cs:
        result_line = []
        for gamma in gammas:
            if C in results.keys() and gamma in results[C].keys():
                result_line.append(results[C][gamma])
            else:
                print("C="+str(C)+" gamma="+str(gamma)+" Result fehlt!")
                if (gamma < 0.144) and (gamma > 1.72e-09):
                    m_file.write(str(C)+";"+str(gamma)+"\n")
                result_line.append(2.647)
        result_table.append(np.array(result_line))
    m_file.close()
    data = np.array(result_table)
    print Cs
    print gammas
    print data
    X,Y = meshgrid(np.array(gammas), np.array(Cs))
    pcolor(X, Y, data)
    ax = subplot(111)
    im = imshow(data, cmap=cm.jet)
    im.set_interpolation('nearest')
    #im.set_interpolation('bicubic')
    #im.set_interpolation('bilinear')
    colorbar()#shrink=0.3)
    autoscale(False)
    axis([gammas[0],gammas[-1],Cs[0],Cs[-1]])
    semilogx(gammas[-1],gammas[0],basex=10,label="gamma")
    #ax.set_ylim(Cs[0],Cs[-1])
    show()

if __name__ == "__main__":
    gather_results(sys.argv[1])