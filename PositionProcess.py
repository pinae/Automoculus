#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================== Imports ======================================
from math import sqrt, pi
import pickle
import sys

import numpy as np
from multiprocessing import Queue, Process
import scipy.optimize as opt

from FitnessWeightFunctions import personFitnessByImage, distanceFitnessByRange, range0to1, lineQualityFunction, occultationWeight

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

# ================================ Methods =====================================


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
    lv1 = sqrt(v1.dot(v1))
    lv2 = sqrt(v2.dot(v2))
    if not lv1 or not lv2: return 0
    div = v1.dot(v2) / (lv1 * lv2)
    if div > 1.0: div = 1.0
    if div < -1.0: div = -1.0
    return np.arccos(div)


def getImageAngles(genome, object):
    c = np.array([0, 0, -1])
    e = np.array([1, 0, 0])
    rotmatrix = rotate(genome)
    c = c.dot(rotmatrix)
    e = e.dot(rotmatrix)
    p = object.location - location(genome)
    ps = p.dot(c) * c + p.dot(e) * e
    if object.location is location(genome):
        print("Kamerposition ist Objektposition")
        return 10, 10
    if ps.dot(ps) > 0:
        x_angle = angle(c, ps)
    else:
        x_angle = 10
    y_angle = angle(p, ps)
    if (p - ps)[2] < 0: y_angle *= -1
    return x_angle, y_angle


def getVisibilityFactor(genome, target, object):
    v = object.location - target.location
    dist = max(sqrt(v.dot(v)), object.radius)
    alpha = angle(v, location(genome) - target.location)
    beta = np.arcsin(object.radius / dist)
    return alpha / beta

# =========================== Optimizer class ==================================
class CameraOptimizer:
    def __init__(self,scene_snapshot, shot):
        self.target = convertToNumpy(scene_snapshot.target)
        self.linetarget = convertToNumpy(scene_snapshot.linetarget)
        self.camera = scene_snapshot.camera
        self.personlist = [convertToNumpy(p) for p in scene_snapshot.persons]
        self.objectlist = [convertToNumpy(o) for o in scene_snapshot.objects]
        self.oldConfiguration = np.array(scene_snapshot.camera.getConfiguration())
        self.shot = shot

    def getShotLimits(self, shot):
        return SHOT_LIMITS[shot] * self.target.height


    def getPersonQuality(self, genome, person, intensity):
        ax, ay = getImageAngles(genome, person)
        x = ax * 2.0 / self.camera.aperture_angle
        y = ay * 2.0 * self.camera.resolution_x / (self.camera.aperture_angle * self.camera.resolution_y)
        occultation = 0
        for object in self.objectlist:
            occultation += occultationWeight(getVisibilityFactor(genome, person, object))
        for somebody in self.personlist:
            if not somebody is person:
                occultation += occultationWeight(getVisibilityFactor(genome, person, somebody))
        return (personFitnessByImage(x, y) + occultation) * intensity

    def getObjectQuality(self, genome, object):
        angles = getImageAngles(genome, object)
        if angles[0] > self.camera.aperture_angle / 2.0 or\
           angles[1] > self.camera.aperture_angle / 2.0 *\
                       self.camera.resolution_y / self.camera.resolution_x:
            return 4 + 0.01 * angles[0] + 0.01 * angles[1]
        else:
            return 0.01 * angles[0] + 0.01 * angles[1]

    def getDistQuality(self, genome, shot):
        v = location(genome) - self.target.location
        dist = sqrt(v.dot(v))
        minDist, maxDist = self.getShotLimits(shot)
        return distanceFitnessByRange(2 * (dist - minDist) / (maxDist - minDist) - 1)

    def getHeightQuality(self, genome):
        heightdiff = genome[2] - self.target.location[2]
        return float(100 * heightdiff * heightdiff)

    def getXAngleQuality(self, genome):
        return range0to1(genome[3] / pi)

    def getLineQuality(self, genome):
        if not self.linetarget or self.target is self.linetarget: return 0
        if (self.target.location == location(genome)).all(): return 10000
        targettolinetarget = self.linetarget.location - self.target.location
        normalvector = np.cross(np.array([0, 0, -1]), targettolinetarget)
        olddiffvector = self.target.location - location(self.oldConfiguration)
        angletoold = angle(olddiffvector, normalvector)
        diffvector = self.target.location - location(genome)
        lineangle = angle(diffvector, normalvector)
        lineangle = pi - lineangle if angletoold > pi / 2 else lineangle
        return lineQualityFunction(pi / 2 - lineangle)

    def fitness(self, genome):
        quality = 0.1
        #Personen im Bild
        for person in self.personlist:
            targetFactor = 1.0 if person is self.target else 0.1
            quality += targetFactor * self.getPersonQuality(genome, person, targetFactor * 12)
            quality += targetFactor * self.getPersonQuality(genome, person.eye_L, targetFactor * 12)
            quality += targetFactor * self.getPersonQuality(genome, person.eye_R, targetFactor * 12)
        #Objekte im Bild
        #for object in self.objectlist:
        #    quality += getObjectQuality(genome, object)
        #Entfernung zur Kamera
        quality += self.getDistQuality(genome, self.shot)
        #Höhe der Kamera
        quality += self.getHeightQuality(genome)
        #Kein Überdrehen der X-Rotation
        quality += self.getXAngleQuality(genome)
        #Ebener Blick
        quality += genome[4] * genome[4] * 0.01
        #Achsenspruenge?
        quality += self.getLineQuality(genome)
        #Sprunghaftigkeit?
        #diffvector = location(genome).reshape(-1) - location(self.oldConfiguration).reshape(-1)
        #quality += sqrt(diffvector.dot(diffvector)) * 3
        quality += np.sum((genome[3:] - self.oldConfiguration[3:])**2)
        return quality

    def optimize(self):
        def runoptimizer(function, startvector, returnqueue):
            o = opt.fmin_powell(func=function, x0=startvector)
            #o = opt.fmin_cg(f=function, x0=startvector)
            #o = opt.fmin_bfgs(f=function, x0=startvector)
            #o = opt.anneal(func=function, x0=startvector)
            returnqueue.put((o, self.fitness(o)))

        start = self.oldConfiguration
        oldQueue = Queue(maxsize=1)
        oldProcess = Process(target=runoptimizer, args=(self.fitness, start, oldQueue))
        oldProcess.start()
        if self.linetarget:
            start = np.hstack((self.linetarget.location, self.oldConfiguration[3:5]))
        else:
            start = np.array([0, 0, 0, self.oldConfiguration[3], self.oldConfiguration[4]])
        litQueue = Queue(maxsize=1)
        litProcess = Process(target=runoptimizer, args=(self.fitness, start, litQueue))
        litProcess.start()
        o_old, f_o_old = oldQueue.get()
        o_lit, f_o_lit = litQueue.get()
        oldProcess.join()
        litProcess.join()
        if f_o_lit < f_o_old:
            return o_lit, f_o_lit, self.shot
        else:
            return o_old, f_o_old, self.shot


def convertToNumpy(o):
    if hasattr(o, "location"):
        o.location = np.array(o.location)
    if hasattr(o, "rotation"):
        o.rotation = np.array(o.rotation)
    if hasattr(o, "eye_L"):
        o.eye_L.location = np.array(o.eye_L.location)
    if hasattr(o, "eye_R"):
        o.eye_R.location = np.array(o.eye_R.location)
    return o


def optimizeAllShots(scene_snapshot):
    def doOptimization(scene_snapshot, shot, return_queue):
        optimizer = CameraOptimizer(scene_snapshot, shot)
        return_queue.put(optimizer.optimize())

    processes = []
    for shot in scene_snapshot.shots:
        q = Queue(1)
        p = Process(target=doOptimization, args=(scene_snapshot, shot, q))
        processes.append((p, q))
        p.start()
    results = []
    for process, queue in processes:
        results.append(queue.get())
        process.join()
    return results

# =============================== Main =========================================

def main():
    initial_data = pickle.load(sys.stdin)
    results = optimizeAllShots(initial_data)
    sys.stdout.write("OK\n")
    sys.stdout.flush()
    #remove all traces of numpy before pickling
    result_list = [(r[0].tolist(), float(r[1]), int(r[2])) for r in results]
    pickle.dump(result_list, sys.stdout)


if __name__ == "__main__":
    main()