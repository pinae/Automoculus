#!/usr/bin/python3
# -*- coding: utf-8 -*-

from os import path
from mathutils import Vector, Euler
import bpy
#from multiprocessing import Process, Queue, Lock, Manager
import subprocess
#import random
#import math
import time

from Config import PROJECT_PATH

class AutomoculusCameraman(bpy.types.Operator):
    bl_idname = "marker.automoculus"
    bl_label = "Automoculus - position camera"

    def createScenicContext(self, process):
        context = {"persons": [], "objects": []}
        process.stdin.write(b'e\n')
        process.stdin.flush()
        entityStr = process.stdout.readline().decode('utf-8').rstrip()
        entityStrByType = entityStr.split("§")
        for personName in entityStrByType[0].strip("\t").split("\t"):
            if len(personName) > 0:
                context["persons"].append(bpy.data.objects[personName])
        for objectName in entityStrByType[1].strip("\t").split("\t"):
            if len(objectName) > 0:
                context["objects"].append(bpy.data.objects[objectName])
        return context

    def cameraOptimizer(self, context, target, linetarget, shots, oldConfiguration):
        def vectorToStr(vector):
            return str(vector[0]) + "|" + str(vector[1]) + "|" + str(vector[2])

        def strToConfiguration(configstr):
            parts = configstr.split(",")
            vectorCoordStrings = parts[0].split("|")
            location = Vector(
                (float(vectorCoordStrings[0]), float(vectorCoordStrings[1]), float(vectorCoordStrings[2])))
            vectorCoordStrings = parts[1].split("|")
            return location, Euler(
                (float(vectorCoordStrings[0]), float(vectorCoordStrings[1]), float(vectorCoordStrings[2])), 'XYZ')
        position_process_filename = path.join(PROJECT_PATH, "PositionProcess.py")
        optimizationProcess = subprocess.Popen(
            ['python', position_process_filename]
            , stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        initStr = target.name + "\t" + linetarget.name + "\t"
        initStr += str(bpy.data.scenes['Scene'].camera.data.angle) + "\t"
        initStr += str(bpy.context.scene.render.resolution_x) + "\t"
        initStr += str(bpy.context.scene.render.resolution_y) + "\t"
        for person in context['persons']:
            try:
                personEyeL = bpy.data.objects[person.name + "_eye.L"].location
                personEyeR = bpy.data.objects[person.name + "_eye.R"].location
            except KeyError:
                personEyeL = person.location
                personEyeR = person.location
            initStr += person.name + "§" + vectorToStr(person.location) + "§" + str(person.dimensions.z) +\
                       "§" + vectorToStr(personEyeL) + "§" + vectorToStr(personEyeR) + ","
        initStr = initStr.rstrip(",") + "\t"
        for object in context['objects']:
            initStr += object.name + "§" + vectorToStr(object.location) + ","
        initStr = initStr.rstrip(",") + "\t"
        initStr += vectorToStr(oldConfiguration[0]) + "," + vectorToStr(oldConfiguration[1]) + "\t"
        shotstr = ""
        for shot in shots:
            shotstr += str(shot) + ","
        initStr += shotstr.rstrip(",")
        optimizationProcess.stdin.write((initStr + "\n").encode('utf-8'))
        optimizationProcess.stdin.flush()
        returnstr = optimizationProcess.stdout.readline().decode('utf-8').rstrip()
        while returnstr != "OK":
            if len(returnstr) > 0:
                print(returnstr)
            returnstr = optimizationProcess.stdout.readline().decode('utf-8').rstrip()
        returnStrings = optimizationProcess.stdout.readline().decode('utf-8').rstrip().split("\t")
        while returnStrings[0] != "Result:":
            if returnStrings != ['']:
                print(returnStrings)
            returnStrings = optimizationProcess.stdout.readline().decode('utf-8').rstrip().split("\t")
        resultlist = []
        for returnString in returnStrings:
            if returnString != "Result:":
                resultparts = returnString.split("§")
                resultlist.append((strToConfiguration(resultparts[0]), float(resultparts[1]), int(resultparts[2])))
        return resultlist

    def springConfigurator(self, opt, now):
        opt[1].make_compatible(now[1])
        #print(self.velocity)
        vloc = self.velocity[0]
        vrot = self.velocity[1]
        aloc = (opt[0] - now[0]) * 14
        arot = Euler(((opt[1][0] - now[1][0]) * 9, 0, (opt[1][2] - now[1][2]) * 12), 'XYZ')
        #aloc = Vector((0,0,0))
        #arot = Euler((0,0,0),'XYZ')
        vloc += aloc * (1.0 / bpy.data.scenes['Scene'].render.fps)
        vrot = Euler((vrot[0] + arot[0] * (1.0 / bpy.data.scenes['Scene'].render.fps), 0,
                      vrot[2] + arot[2] * (1.0 / bpy.data.scenes['Scene'].render.fps)), 'XYZ')
        loc = now[0] + vloc * (1.0 / bpy.data.scenes['Scene'].render.fps)
        rot = Euler((now[1][0] + vrot[0] * (1.0 / bpy.data.scenes['Scene'].render.fps), 0,
                     now[1][2] + vrot[2] * (1.0 / bpy.data.scenes['Scene'].render.fps)), 'XYZ')
        self.velocity = (vloc * 0.75, Euler((vrot[0] * 0.75, 0, vrot[2] * 0.75), 'XYZ'))
        return loc, rot

    def getDistFromStr(self, diststr):
        dist = []
        for valstr in diststr.split('\t'):
            dist.append(float(valstr))
        return dist

    def getTargetsFromStr(self, targetstr):
        splitstr = targetstr.split('\t')
        target = bpy.data.objects[splitstr[0]]
        linetarget = bpy.data.objects[splitstr[1]]
        return target, linetarget


    def invoke(self, context, event):
        def setInitialVelocity(target):
            # Geschwindigkeit des Targets auf die Kamera übertragen.
            target_tmp_loc = Vector((target.location[0], target.location[1], target.location[2]))
            bpy.data.scenes['Scene'].frame_current -= 1
            bpy.ops.object.paths_calculate()
            target_velocity = (target_tmp_loc - target.location) * 1.333333
            bpy.data.scenes['Scene'].frame_current += 1
            bpy.ops.object.paths_calculate()
            self.velocity = (target_velocity, Euler((0, 0, 0), 'XYZ'))

        def setConfiguration(newConfiguration):
            camera.location = newConfiguration[0]
            camera.rotation_euler = newConfiguration[1]
            camera.keyframe_insert(data_path="rotation_euler")
            camera.keyframe_insert(data_path="location")

        def calculateForNewBeats(classificationProcess, shot, frame, lastcut, initialcut):
            # New Beats! That changes the situation: what's the distribution now?
            classificationProcess.stdin.write(b'p\n')
            classificationProcess.stdin.flush()
            dist = self.getDistFromStr(classificationProcess.stdout.readline().decode('utf-8').rstrip())
            #print(str(classificationProcess.stdout.readline(), encoding='utf-8').rstrip())
            #dist = [0.14, 0.14, 0.14, 0.14, 0.14, 0.14, 0.14]

            # For new beats we have to update the targets
            classificationProcess.stdin.write(b't\n')
            classificationProcess.stdin.flush()
            target, linetarget = self.getTargetsFromStr(
                classificationProcess.stdout.readline().decode('utf-8').rstrip())
            #target = bpy.data.objects["Green"]
            #linetarget = bpy.data.objects["Red"]
            print(target.name + "\t" + linetarget.name)

            # Should we cut? Ask the classificationProcess
            classificationProcess.stdin.write(b'c\n')
            classificationProcess.stdin.flush()
            cut = classificationProcess.stdout.readline().decode('utf-8').rstrip() == "yes"
            print("Cut: " + str(cut))

            # Calculate optimal positions for all shots in the distribution with a propability > 0
            #processes = []
            #returnqueues = []
            #for i in range(0, len(SHOT_NAMES)):
            #    if dist[i] > 0:
            #        returnqueues.append(Queue())
            #        returnqueues[i].put(i)
            #        processes.append(Process(target=calculatePosition, args=(i != shot or cut, i, returnqueues[i])))
            #        processes[i].start()

            # Determine which shot fits best, regarding the classified propability
            bestratio = 0
            bestconfig = (camera.location, camera.rotation_euler)
            bestShotCandidate = shot
            noCutRatio = 0
            noCutConfig = (camera.location, camera.rotation_euler)
            correction = [141, 42, 59, 130, 130, 130, 130]
            #correction = [100, 100, 100, 100, 100, 100, 100]
            shots = []
            for i in range(0, len(SHOT_NAMES)):
                if dist[i] > 0.1 or i == shot:
                    shots.append(i)
            candidatestr = "Es kommen folgende Einstellungsgrößen in Frage: "
            for shot in shots:
                candidatestr += SHOT_NAMES[shot]+", "
            print(candidatestr)
            results = self.cameraOptimizer(scenicContext, target, linetarget, shots,
                (camera.location, camera.rotation_euler))
            for result in results:
                configuration = result[0]
                fitness = result[1]
                shot_number = result[2]
                print("Fitness " + str(fitness) + " for " + SHOT_NAMES[shot_number] + ".")
                ratio = 1 / fitness * dist[shot_number] * correction[shot_number]
                print("Ratio " + str(ratio) + " for " + SHOT_NAMES[shot_number] + ".")
                if shot_number == shot:
                    noCutRatio = ratio
                    noCutConfig = configuration
                if ratio > bestratio:
                    bestratio = ratio
                    bestconfig = configuration
                    bestShotCandidate = shot_number

            # Should we Cut?
            if bestratio - 0.1 > noCutRatio or initialcut or cut: # We want to cut, the ratio gets much better
                shot = bestShotCandidate
                if (bestconfig[0] - camera.location).length < 0.8:
                    #newConfiguration = self.springConfigurator(bestconfig,
                    #    (camera.location, camera.rotation_euler))
                    newConfiguration = bestconfig
                    print("Es sollte geschnitten werden, die Abweichung war jedoch zu gering. Wir bleiben bei " +
                          SHOT_NAMES[shot])
                else:
                    newConfiguration = bestconfig
                    lastcut = frame
                    setInitialVelocity(target)
                    print("Schnitt auf: " + SHOT_NAMES[shot])
            else: # We don't want to cut because the ratio doesn't get significantly better
                #newConfiguration = self.springConfigurator(noCutConfig,
                #    (camera.location, camera.rotation_euler))
                newConfiguration = noCutConfig
                print("Kein Schnitt. Wir bleiben bei " + SHOT_NAMES[shot])
                # Tell our decision to the classifier
            classificationProcess.stdin.write(b'd\n')
            classificationProcess.stdin.flush()
            classificationProcess.stdin.write((str(shot) + "\n").encode('utf-8'))
            classificationProcess.stdin.flush()
            if classificationProcess.stdout.readline().decode('utf-8').rstrip() != "decision recieved":
                print("Could not Write decision.")
            return newConfiguration, shot, lastcut, target, linetarget

        SHOT_NAMES = ["detail", "closeup", "medium_shot", "american_shot", "full_shot", "long_shot",
                      "extreme_long_shot"]
        beatscriptFile = path.join(PROJECT_PATH, beatscript)
        print(beatscriptFile)
        time.sleep(5)
        #blockcount = 0
        classification_process_filename = path.join(PROJECT_PATH, "BeatscriptClassifier.py")
        classificationProcess = subprocess.Popen(
            [classification_process_filename,
             beatscriptFile], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        camera = bpy.data.scenes['Scene'].camera
        shot = 0
        lastcut = 0
        while True:
            input = classificationProcess.stdout.readline()
            print(input.decode('utf8').rstrip())
            if input.decode('utf8').rstrip() == "Training finished.":
                break
        scenicContext = self.createScenicContext(classificationProcess)
        classificationProcess.stdin.write(b't\n')
        classificationProcess.stdin.flush()
        target, linetarget = self.getTargetsFromStr(classificationProcess.stdout.readline().decode('utf-8').rstrip())
        setInitialVelocity(target)
        bpy.data.scenes['Scene'].frame_current = 1
        bpy.ops.object.paths_calculate()
        newConfiguration, shot, lastcut, target, linetarget = calculateForNewBeats(classificationProcess, shot, 1,
            lastcut, True)
        setConfiguration(newConfiguration)
        print("Szenenkontext erzeugt.")
        for frame in range(2, 750):
            bpy.data.scenes['Scene'].frame_current = frame
            bpy.ops.object.paths_calculate()
            print("Bearbeite Frame No. " + str(bpy.data.scenes['Scene'].frame_current))
            if frame - lastcut >= 19: # It's been 19 frames or more since the last cut
                # Are there new beats?
                classificationProcess.stdin.write(b'f\n')
                classificationProcess.stdin.flush()
                classificationProcess.stdin.write((str(frame) + "\n").encode('utf-8'))
                classificationProcess.stdin.flush()
                if classificationProcess.stdout.readline().decode('utf-8').rstrip() == "yes": # there are new beats
                    print("Neue Beats, neues Glück!")
                    newConfiguration, shot, lastcut, target, linetarget = calculateForNewBeats(classificationProcess,
                        shot, frame, lastcut,
                        False)
                else: # There were no new beats
                    print("Keine neuen Beats.")
                    optimalConfiguration, fitness, notused = self.cameraOptimizer(scenicContext, target, linetarget,
                        [shot], (camera.location, camera.rotation_euler))[0]
                    #optimalConfiguration, fitness = self.geneticConfigurator(scenicContext, target, linetarget, shot,
                    #    (camera.location, camera.rotation_euler))
                    newConfiguration = self.springConfigurator(optimalConfiguration,
                        (camera.location, camera.rotation_euler))
                    #newConfiguration = optimalConfiguration
            else: # It's too early to cut
                #optimalConfiguration, fitness = self.geneticConfigurator(scenicContext, target, linetarget, shot,
                #    (camera.location, camera.rotation_euler))
                optimalConfiguration, fitness, notused = self.cameraOptimizer(scenicContext, target, linetarget, [shot],
                    (camera.location, camera.rotation_euler))[0]
                newConfiguration = self.springConfigurator(optimalConfiguration,
                    (camera.location, camera.rotation_euler))
                #newConfiguration = optimalConfiguration
            setConfiguration(newConfiguration)
            bpy.data.scenes['Scene'].camera.data.dof_distance = (target.location - camera.location).length
            camera.data.keyframe_insert(data_path="dof_distance")
        classificationProcess.stdin.write(b'q\n')
        classificationProcess.stdin.flush()
        print("Classification Process: " + classificationProcess.stdout.readline().decode('utf-8').rstrip())
        classificationProcess.wait()
        return {"FINISHED"}

bpy.utils.register_class(AutomoculusCameraman)
