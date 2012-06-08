#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================== Imports ======================================
from __future__ import division
import cProfile
import pstats
from pylab import *
import numpy as np
from math import sqrt, pi
import tempfile
import os

# ================================ constants =====================================
SHOT_LIMITS = [
    np.array([0.0, 3.87]), # detail
    np.array([0.3, 1.15]), # closeup
    np.array([1.15, 2.06]), # medium shot
    np.array([2.06, 3.62]), # american shot
    np.array([3.62, 5.35]), # full shot
    np.array([5.35, 7.2]), # long shot
    np.array([7.2, 28]) # extreme long shot
]

C = np.array([0, 0, -1])
E = np.array([1, 0, 0])

# ============================== Weight Functions =====================================
def personFitnessByImage(x, y):
    x2 = x * x
    y2 = y * y
    return (np.exp(-0.5 * x2 ** 5 - 0.5 * y2 ** 5) *
            (((7 * x2 - 4.5) * x2 - 9) + ((10 * y2 - 4.5) * y2 - 2 * y - 9)) + 21.2) * (1 + (abs(x) + abs(y)) * 0.1)


def distanceFitnessByRange(x):
    return (1000 - 1000 * np.exp(-0.5 * x ** 4)) * (0.1 * abs(x) + 0.9)


def range0to1(x):
    return (1000 - 1000 * np.exp(-0.5 * x ** 10)) * (0.001 * abs(x) + 0.999)


def lineQualityFunction(x):
    return (50 - 50 * x / (0.001 + abs(x))) * (2 - 5 * x)


def occultationWeight(x):
    return 3 * np.exp(-0.5 * x ** 4)


# ============================== Helper Functions =====================================
def location(genome):
    return genome[:3]


def rotate(genome):
    R = np.zeros((3, 3))
    cx = np.cos(-genome[3])
    cz = np.cos(-genome[4])
    sx = np.sin(-genome[3])
    sz = np.sin(-genome[4])
    R.flat = (cz, -sz, 0,
              cx * sz, cx * cz, -sx,
              sx * sz, sx * cz, cx)
    return R


def angle(v1, v2):
    lv1 = np.sqrt(v1.dot(v1))
    lv2 = np.sqrt(v2.dot(v2))
    if not (lv1 and lv2): return 0
    div = v1.dot(v2) / (lv1 * lv2)
    if div > 1.0: div = 1.0
    if div < -1.0: div = -1.0
    return np.arccos(div)

def getImageAngles(genome, object):
    rotmatrix = rotate(genome)
    c = C.dot(rotmatrix)
    e = E.dot(rotmatrix)
    p = object.location - genome[:3]
    ps = p.dot(c) * c + p.dot(e) * e
    if not p.any():
        print("Kamerposition ist Objektposition")
        return 10, 10
    if ps.any(): #ps.dot(ps) > 0:
        x_angle = angle(c, ps)
    else:
        x_angle = 10
    y_angle = angle(p, ps)
    if (p - ps)[2] < 0: y_angle *= -1
    return x_angle, y_angle

def getVisibilityFactor(genome, target, object):
    v = object.location - target.location
    dist = max(np.sqrt(v.dot(v)), object.radius)
    alpha = angle(v, genome[:3] - target.location)
    beta = np.arcsin(object.radius / dist)
    return alpha / beta

def getShotLimits(cameraOptimizer, shot):
    return SHOT_LIMITS[shot] * cameraOptimizer.target.height

# ============================== Quality Functions =====================================
def getPersonQuality(cameraOptimizer, genome, person, intensity):
    ax, ay = getImageAngles(genome, person)
    x = ax * 2.0 / cameraOptimizer.camera.aperture_angle
    y = ay * 2.0 * cameraOptimizer.camera.resolution_x / (cameraOptimizer.camera.aperture_angle * cameraOptimizer.camera.resolution_y)
    occultation = 0
    for object in cameraOptimizer.objectlist:
        occultation += occultationWeight(getVisibilityFactor(genome, person, object))
    for somebody in cameraOptimizer.personlist:
        if not somebody is person:
            occultation += occultationWeight(getVisibilityFactor(genome, person, somebody))
    return (personFitnessByImage(x, y) + occultation) * intensity

def getObjectQuality(cameraOptimizer, genome, object):
    angles = getImageAngles(genome, object)
    if angles[0] > cameraOptimizer.camera.aperture_angle / 2.0 or\
       angles[1] > cameraOptimizer.camera.aperture_angle / 2.0 *\
                   cameraOptimizer.camera.resolution_y / cameraOptimizer.camera.resolution_x:
        return 4 + 0.01 * angles[0] + 0.01 * angles[1]
    else:
        return 0.01 * angles[0] + 0.01 * angles[1]

def getDistQuality(cameraOptimizer, genome, shot):
    v = location(genome) - cameraOptimizer.target.location
    dist = sqrt(v.dot(v))
    minDist, maxDist = getShotLimits(cameraOptimizer, shot)
    return distanceFitnessByRange(2 * (dist - minDist) / (maxDist - minDist) - 1)

def getHeightQuality(cameraOptimizer, genome):
    heightdiff = genome[2] - cameraOptimizer.target.location[2]
    return float(100 * heightdiff * heightdiff)

def getXAngleQuality(genome):
    return range0to1(genome[3] / pi)

def getLineQuality(cameraOptimizer, genome):
    if not cameraOptimizer.linetarget or cameraOptimizer.target is cameraOptimizer.linetarget: return 0
    if (cameraOptimizer.target.location == location(genome)).all(): return 10000
    targettolinetarget = cameraOptimizer.linetarget.location - cameraOptimizer.target.location
    normalvector = np.cross(np.array([0, 0, -1]), targettolinetarget)
    olddiffvector = cameraOptimizer.target.location - location(cameraOptimizer.oldConfiguration)
    angletoold = angle(olddiffvector, normalvector)
    diffvector = cameraOptimizer.target.location - location(genome)
    lineangle = angle(diffvector, normalvector)
    lineangle = pi - lineangle if angletoold > pi / 2 else lineangle
    return lineQualityFunction(pi / 2 - lineangle)


# ============================== Fitness Function =====================================

def fitness(genome, cameraOptimizer):
    quality = 0.1
    #Personen im Bild
    for person in cameraOptimizer.personlist:
        targetFactor = 1.0 if person is cameraOptimizer.target else 0.1
        quality += targetFactor * getPersonQuality(cameraOptimizer, genome, person, targetFactor * 12)
        quality += targetFactor * getPersonQuality(cameraOptimizer, genome, person.eye_L, targetFactor * 12)
        quality += targetFactor * getPersonQuality(cameraOptimizer, genome, person.eye_R, targetFactor * 12)
        #Objekte im Bild
    #for object in self.objectlist:
    #    quality += getObjectQuality(cameraOptimizer, genome, object)
    #Entfernung zur Kamera
    quality += getDistQuality(cameraOptimizer, genome, cameraOptimizer.shot)
    #Höhe der Kamera
    quality += getHeightQuality(cameraOptimizer, genome)
    #Kein Überdrehen der X-Rotation
    quality += getXAngleQuality(genome)
    #Ebener Blick
    quality += genome[4] * genome[4] * 0.01
    #Achsenspruenge?
    quality += getLineQuality(cameraOptimizer, genome)
    #Sprunghaftigkeit?
    #diffvector = location(genome).reshape(-1) - location(self.oldConfiguration).reshape(-1)
    #quality += sqrt(diffvector.dot(diffvector)) * 3
    quality += np.sum((genome[3:] - cameraOptimizer.oldConfiguration[3:])**2)
    return quality


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
