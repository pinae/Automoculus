#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================== Imports ======================================
from math import sqrt, pi
import scipy.optimize as opt
import numpy as np
import sys
from multiprocessing import Queue, Process
from FitnessWeightFunctions import personFitnessByImage
from FitnessWeightFunctions import distanceFitnessByRange
from FitnessWeightFunctions import range0to1
from FitnessWeightFunctions import lineQualityFunction
from FitnessWeightFunctions import occultationWeight

# ============================= Person class ===================================
class PersonAddition:
    def __init__(self, name, location):
        self.name = name
        self.location = location
        self.radius = 0


class Person:
    def __init__(self, name, location, height, left_eye_loc, right_eye_loc):
        self.name = name
        self.location = location
        self.height = height
        self.eye_L = PersonAddition(name + "_eye.L", left_eye_loc)
        self.eye_R = PersonAddition(name + "_eye.R", right_eye_loc)
        self.radius = 1.0#0.1

# ============================= Object class ===================================

class Object:
    def __init__(self, name, location):
        self.name = name
        self.location = location
        self.radius = 0.1

# ============================= Camera class ===================================
class Camera:
    def __init__(self, angle, resolution_x, resolution_y):
        self.angle = angle
        self.resolution_x = resolution_x
        self.resolution_y = resolution_y

# ================================ Methods =====================================

def location(genome):
    loc = np.array([genome[0], genome[1], genome[2]])
    loc.reshape(-1, 1)
    return loc


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
#    # koordinatensystem der Kamera
#    U = np.eye(3)
#    U[2,2] = -1
#
#    # rotationsmatrix
#    R = rotate(genome)
#
#    # gedreht
#    Ur = U.dot(R)
#
#    # vektor von kamera nach objekt
#    p = object.location.flatten() - location(genome).flatten()
#
#    # vektor im Koordinatensystem der Kamera
#    x, y, z = p.dot(Ur)
#
#    pl = np.sqrt(p.dot(p))
#
#    x_angle = np.arctan(y / x)
#    #y_angle = np.arctan(y / z)
#    #x_angle = -np.arccos(x/pl)+pi/2
#    y_angle = -np.arccos(z/pl)+pi/2

    c = np.array([0, 0, -1])
    e = np.array([1, 0, 0])
    rotmatrix = rotate(genome)
    c = c.dot(rotmatrix)
    e = e.dot(rotmatrix)
    p = object.location.reshape(-1) - location(genome)
    ps = p.dot(c) * c + p.dot(e) * e
    if object.location is location(genome):
        print("Kamerposition ist Objektposition")
        return 10, 10
    if ps.dot(ps) > 0:
        x_angle = angle(c, ps)
    else:
        #print("ps x ist < 0")
        x_angle = 10
    y_angle = angle(p, ps)
    #e = np.array([0, 1, 0])
    #e = e.dot(rotmatrix)
    #if p.dot(c)<=0: print("p.dot(c): "+str(p.dot(c))+" c="+str(c))
    #if p.dot(e)<=0: print("p.dot(e): "+str(p.dot(e))+" e="+str(e))
    #ps = np.absolute(p.dot(c)) * c + np.absolute(p.dot(e)) * e
    #ps = p.dot(c) * c + p.dot(e) * e
    #if ps.dot(ps) > 0:
    #y_angle = (angle(c, ps)+pi/2)%pi-pi/2
    #y_angle = angle(c, ps)
    #print(str(ps)+"  :  "+str(c))
    #if y_angle > 2: print("###########")
    #else:
    #print("ps y ist < 0: ps="+str(ps))
    #y_angle = 10
    #sp = np.array([0, 0, -1])
    if (p - ps)[2] < 0: y_angle *= -1
    #if x_angle > pi/2: y_angle *= -1
    return x_angle, y_angle


def getVisibilityFactor(genome, target, object):
    v = object.location.flatten() - target.location.flatten()
    dist = sqrt(v.dot(v))
    if dist < object.radius: dist = object.radius
    alpha = angle(v, location(genome) - target.location.flatten())
    beta = np.arcsin(object.radius / dist)
    return alpha / beta

# =========================== Optimizer class ==================================
class CameraOptimizer:
    def __init__(self, target, linetarget, camera, personlist, objectlist, oldConfiguration, shot):
        self.target = target
        self.linetarget = linetarget
        self.camera = camera
        self.personlist = personlist
        self.objectlist = objectlist
        self.oldConfiguration = oldConfiguration
        self.shot = shot

    def getShotLimits(self, shot):
        if shot == 1: # closeup
            return 0.3 * self.target.height, 1.15 * self.target.height
        elif shot == 2: # medium shot
            return 1.15 * self.target.height, 2.06 * self.target.height
        elif shot == 3: # american shot
            return 2.06 * self.target.height, 3.62 * self.target.height
        elif shot == 4: # full shot
            return 3.62 * self.target.height, 5.35 * self.target.height
        elif shot == 5: # long shot
            return 5.35 * self.target.height, 7.2 * self.target.height
        elif shot == 6: # extreme long shot
            return 7.2 * self.target.height, 28 * self.target.height
        else: # detail
            return 0 * self.target.height, 3.87 * self.target.height # Details sind ganz zu sehen.

    def getPersonQuality(self, genome, person, intensity, weightfunction, occultationfunction):
        ax, ay = getImageAngles(genome, person)
        x = ax * 2.0 / self.camera.angle
        y = ay * 2.0 * self.camera.resolution_x / (self.camera.angle * self.camera.resolution_y)
        occultation = 0
        for object in self.objectlist:
            occultation += occultationfunction(getVisibilityFactor(genome, person, object))
        for somebody in self.personlist:
            if not somebody is person:
                occultation += occultationfunction(getVisibilityFactor(genome, person, somebody))
        return (weightfunction(x, y) + occultation) * intensity

    def getObjectQuality(self, genome, object):
        angles = getImageAngles(genome, object)
        if angles[0] > self.camera.angle / 2.0 or\
           angles[1] > self.camera.angle / 2.0 *\
                       self.camera.resolution_y / self.camera.resolution_x:
            return 4 + 0.01 * angles[0] + 0.01 * angles[1]
        else:
            return 0.01 * angles[0] + 0.01 * angles[1]

    def getDistQuality(self, genome, shot, weightfunction):
        camera_location = location(genome)
        camera_location = camera_location.reshape(-1, 1)
        target_location = self.target.location
        v = camera_location - target_location
        v = v.reshape(-1)
        dist = sqrt(v.dot(v))
        minDist, maxDist = self.getShotLimits(shot)
        #if dist < minDist or dist > maxDist: print("Dist ist außerhalb des Bereichs: " + str(dist) + " : " + str(
        #    2 * (dist - minDist) / (maxDist - minDist) -1) + " : " + str(
        #    distanceFitnessByRange(2 * (dist - minDist) / (maxDist - minDist) -1)))
        return weightfunction(2 * (dist - minDist) / (maxDist - minDist) - 1)

    def getHeightQuality(self, genome):
        heightdiff = abs(genome[2] - self.target.location[2])
        return float(100 * heightdiff * heightdiff)

    def getXAngleQuality(self, genome, weightfunction):
        return weightfunction(genome[3] / pi)

    def getLineQuality(self, genome):
        if self.target is self.linetarget or not self.linetarget: return 0
        if self.target.location.flatten() is location(genome): return 10000
        targettolinetarget = self.linetarget.location.flatten() - self.target.location.flatten()
        normalvector = np.cross(np.array([0, 0, -1]), targettolinetarget)
        olddiffvector = self.target.location.flatten() - location(self.oldConfiguration).flatten()
        angletoold = angle(olddiffvector, normalvector)
        diffvector = self.target.location.flatten() - location(genome).flatten()
        lineangle = angle(diffvector, normalvector)
        if angletoold > pi / 2:
            lineangle = pi - lineangle
        return lineQualityFunction(pi / 2 - lineangle)

    def fitness(self, genome):
        quality = 0.1
        #Personen im Bild
        for person in self.personlist:
            if person is self.target:
                targetFactor = 1.0
            else:
                targetFactor = 0.1
            quality += targetFactor * self.getPersonQuality(genome, person, targetFactor * 12,
                personFitnessByImage, occultationWeight)
            quality += targetFactor * self.getPersonQuality(genome, person.eye_L, targetFactor * 12,
                personFitnessByImage, occultationWeight)
            quality += targetFactor * self.getPersonQuality(genome, person.eye_R, targetFactor * 12,
                personFitnessByImage, occultationWeight)

        #Objekte im Bild
        #for object in self.objectlist:
        #    quality += getObjectQuality(genome, object)

        #Entfernung zur Kamera
        quality += self.getDistQuality(genome, self.shot, distanceFitnessByRange)

        #Höhe der Kamera
        quality += self.getHeightQuality(genome)

        #Kein Überdrehen der X-Rotation
        quality += self.getXAngleQuality(genome, range0to1)

        #Ebener Blick
        quality += genome[4] * genome[4] * 0.01

        #Achsenspruenge?
        quality += self.getLineQuality(genome)

        #Sprunghaftigkeit?
        #diffvector = location(genome).reshape(-1) - location(self.oldConfiguration).reshape(-1)
        #quality += sqrt(diffvector.dot(diffvector)) * 3
        quality += float((genome[3] - self.oldConfiguration[3]) * (genome[3] - self.oldConfiguration[3]) +\
                         (genome[4] - self.oldConfiguration[4]) * (genome[4] - self.oldConfiguration[4]))
        return quality

    def optimize(self):
        def runoptimizer(function, startvector, returnqueue):
            o = opt.fmin_powell(func=function, x0=startvector)
            #o = opt.fmin_cg(f=function, x0=startvector)
            #o = opt.fmin_bfgs(f=function, x0=startvector)
            #o = opt.anneal(func=function, x0=startvector)
            returnqueue.put(o)
            returnqueue.put(self.fitness(o))

        start = np.array([self.oldConfiguration[0], self.oldConfiguration[1], self.oldConfiguration[2],
                          self.oldConfiguration[3], self.oldConfiguration[4]])
        oldQueue = Queue(maxsize=2)
        oldProcess = Process(target=runoptimizer, args=(self.fitness, start, oldQueue))
        oldProcess.start()
        if self.linetarget:
            start = np.array([self.linetarget.location[0], self.linetarget.location[1], self.linetarget.location[2],
                              self.oldConfiguration[3], self.oldConfiguration[4]])
        else:
            start = np.array([0, 0, 0, self.oldConfiguration[3], self.oldConfiguration[4]])
        litQueue = Queue(maxsize=2)
        litProcess = Process(target=runoptimizer, args=(self.fitness, start, litQueue))
        litProcess.start()
        o_old = oldQueue.get()
        f_o_old = oldQueue.get()
        o_lit = litQueue.get()
        f_o_lit = litQueue.get()
        oldProcess.join()
        litProcess.join()
        if f_o_lit < f_o_old:
            return o_lit, f_o_lit, self.shot
        else:
            return o_old, f_o_old, self.shot


def vectorFromStr(vectorstr):
    coordinateStrings = vectorstr.split("|")
    return np.array([float(coordinateStrings[0]), float(coordinateStrings[1]), float(coordinateStrings[2])])\
    .reshape(-1, 1)


def locationFromStr(locstr):
    return vectorFromStr(locstr)


def eulerFromStr(rotstr):
    return vectorFromStr(rotstr)


def personFromStr(personstr):
    parts = personstr.split("§")
    return Person(parts[0], locationFromStr(parts[1]), float(parts[2]), locationFromStr(parts[3]),
        locationFromStr(parts[4]))


def objectFromStr(objectstr):
    parts = objectstr.split("§")
    return Object(parts[0], locationFromStr(parts[1]))


def shotlistFromStr(shotliststr):
    shotlist = []
    for numberstr in shotliststr.split(","):
        if len(numberstr) > 0:
            shotlist.append(int(numberstr))
    return shotlist


def vectorToStr(vector):
    return str(vector[0]) + "|" + str(vector[1]) + "|" + str(vector[2])


def configurationToStr(configuration):
    return str(configuration[0]) + "|" + str(configuration[1]) + "|" + str(configuration[2]) + "," +\
           str(configuration[3]) + "|" + str(0.0) + "|" + str(configuration[4])


def optimizeAllShots(target, linetarget, camera, personlist, objectlist, oldConfiguration, shots):
    def doOptimization(target, linetarget, camera, personlist, objectlist, oldConfiguration, shot, returnqueue):
        optimizer = CameraOptimizer(target, linetarget, camera, personlist, objectlist, oldConfiguration, shot)
        returnqueue.put(optimizer.optimize())

    processes = []
    for i in range(0, len(shots)):
        q = Queue(1)
        processes.append((Process(target=doOptimization, args=(
            target, linetarget, camera, personlist, objectlist, oldConfiguration, shots[i], q)), q))
        processes[-1][0].start()
    results = []
    for process in processes:
        results.append(process[1].get())
        process[0].join()
    return results

# =============================== Main =========================================
def main():
    # initialization
    initialData = sys.stdin.readline().split("\t")
    targetName = initialData[0]
    linetargetName = initialData[1]
    camera = Camera(float(initialData[2]), int(initialData[3]), int(initialData[4]))
    personlist = []
    target = False
    linetarget = False
    for personstr in initialData[5].split(","):
        personlist.append(personFromStr(personstr))
        if personlist[-1].name == targetName:
            target = personlist[-1]
        if personlist[-1].name == linetargetName:
            linetarget = personlist[-1]
            #print(personlist)
    objectlist = []
    for objectstr in initialData[6].split(","):
        if len(objectstr) > 0:
            objectlist.append(objectFromStr(objectstr))
    configurationStrings = initialData[7].split(",")
    location = locationFromStr(configurationStrings[0])
    rotation = eulerFromStr(configurationStrings[1])
    oldConfiguration = np.array([location[0], location[1], location[2], rotation[0], rotation[2]])
    shots = shotlistFromStr(initialData[8])
    # optimization
    results = optimizeAllShots(target, linetarget, camera, personlist, objectlist, oldConfiguration, shots)
    # returning results
    sys.stdout.write("OK\n")
    sys.stdout.flush()
    resultstr = ""
    for result in results:
        resultstr += configurationToStr(result[0]) + "§" + str(result[1]) + "§" + str(result[2]) + "\t"
    sys.stdout.write("Result:\t" + resultstr.rstrip("\t") + "\n")
    sys.stdout.flush()

if __name__ == "__main__":
    main()