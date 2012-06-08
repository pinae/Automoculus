#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================== Imports ======================================
import pickle
import sys

import numpy as np
from multiprocessing import Queue, Process
import scipy.optimize as opt

from FitnessFunction import fitness

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

    def optimize(self):
        def runoptimizer(function, startvector, returnqueue):
            o = opt.fmin_powell(func=function, x0=startvector, args=(self,))
            #o = opt.fmin_cg(f=function, x0=startvector)
            #o = opt.fmin_bfgs(f=function, x0=startvector)
            #o = opt.anneal(func=function, x0=startvector)
            returnqueue.put((o, fitness(o, self)))

        start = self.oldConfiguration
        oldQueue = Queue(maxsize=1)
        oldProcess = Process(target=runoptimizer, args=(fitness, start, oldQueue))
        oldProcess.start()
        if self.linetarget:
            start = np.hstack((self.linetarget.location, self.oldConfiguration[3:5]))
        else:
            start = np.array([0, 0, 0, self.oldConfiguration[3], self.oldConfiguration[4]])
        litQueue = Queue(maxsize=1)
        litProcess = Process(target=runoptimizer, args=(fitness, start, litQueue))
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