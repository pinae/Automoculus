#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================== Imports ======================================
from __future__ import division
#from matplotlib.patches import Patch
from pylab import *
import numpy as np

# ============================== Functions =====================================
def personFitnessByImage(x, y):
    x2 = x * x
    y2 = y * y
    return (np.exp(-0.5 * x2 * x2 * x2 * x2 * x2 - 0.5 * y2 * y2 * y2 * y2 * y2) *
            (((7 * x2 - 4.5) * x2 - 9) + ((10 * y2 - 4.5) * y2 - 2 * y - 9)) + 21.2) * (1 + (abs(x) + abs(y)) * 0.1)

def distanceFitnessByRange(x):
    x2 = x * x
    return (1000 - 1000 * np.exp(-0.5 * x2 * x2)) * (abs(x) * 0.1 + 0.9)

def range0to1(x):
    x2 = x * x
    x4 = x2 * x2
    return (1000 - 1000 * np.exp(-0.5 * x4 * x4 * x2)) * (abs(x) * 0.001 + 0.999)

def lineQualityFunction(x):
    #return (500*(1+np.tanh(-50*x)))*(-10*x+1)
    return (50 - 50 * x / (0.001 + abs(x))) * (2 - 5*x)

def occultationWeight(x):
    x2 = x * x
    return 3 * np.exp(-0.5 * x2 * x2)

# ================================ Plots =======================================
def main():
    # make these smaller to increase the resolution
    dx, dy = 0.013, 0.013
    ra = 0.90
    x = np.arange(-ra, ra + 0.0001, dx)
    y = np.arange(-ra, ra + 0.0001, dy)
    X, Y = np.meshgrid(x, y)

    Z = personFitnessByImage(X, Y)

    pcolor(X, Y, Z)
    colorbar()
    axis([-ra, ra, -ra, ra])

    show()

if __name__ == "__main__":
    main()