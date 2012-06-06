#!/usr/bin/python3
# -*- coding: utf-8 -*-

from os import path
from mathutils import Vector, Euler
import bpy

import subprocess
import pickle

from Config import PROJECT_PATH, SHOT_NAMES
from SceneSnapshot import Object, Person, Place, Camera, SceneSnapshot

position_process_filename = path.abspath(path.join(PROJECT_PATH, "PositionProcess.py"))
beatscript_classifier_filename = path.abspath(path.join(PROJECT_PATH, "BeatscriptClassifier.sh"))

def getDistFromStr(diststr):
    return [float(x) for x in diststr.split('\t')]
    #return [0.14, 0.14, 0.14, 0.14, 0.14, 0.14, 0.14]

def getShotDistribution(classificationProcess):
    classificationProcess.stdin.write(b'p\n')
    classificationProcess.stdin.flush()
    return getDistFromStr(classificationProcess.stdout.readline().decode('utf-8').rstrip())

def getTargets(classificationProcess):
    classificationProcess.stdin.write(b't\n')
    classificationProcess.stdin.flush()
    targetstr = classificationProcess.stdout.readline().decode('utf-8').rstrip()
    splitstr = targetstr.split('\t')
    target = bpy.data.objects[splitstr[0]]
    linetarget = bpy.data.objects[splitstr[1]]
    return target, linetarget

def shouldCut(classificationProcess):
    classificationProcess.stdin.write(b'c\n')
    classificationProcess.stdin.flush()
    cut = classificationProcess.stdout.readline().decode('utf-8').rstrip() == "yes"
    return cut

def createPersonObject(person):
    try:
        personEyeL = bpy.data.objects[person.name + "_eye.L"].location
        personEyeR = bpy.data.objects[person.name + "_eye.R"].location
    except KeyError:
        personEyeL = person.location
        personEyeR = person.location
    return Person(person.name, person.location, person.dimensions.z, personEyeL, personEyeR)


class AutomoculusCameraman(bpy.types.Operator):
    bl_idname = "marker.automoculus"
    bl_label = "Automoculus - position camera"

    def setConfiguration(self, newConfiguration):
        self.camera.location = newConfiguration[0]
        self.camera.rotation_euler = newConfiguration[1]
        self.camera.keyframe_insert(data_path="rotation_euler")
        self.camera.keyframe_insert(data_path="location")




    def calculateForNewBeats(self, classificationProcess, shot, frame, last_cut, initial_cut, scenicContext):
        # New Beats! That changes the situation: what's the distribution now?
        dist = getShotDistribution(classificationProcess)

        # For new beats we have to update the targets
        target, linetarget = getTargets(classificationProcess)
        print(target.name + "\t" + linetarget.name)

        # Should we cut? Ask the classificationProcess
        cut = shouldCut(classificationProcess)
        print("Cut: " + str(cut))

        # Determine which shot fits best, regarding the classified propability
        best_ratio = 0
        best_config = (self.camera.location, self.camera.rotation_euler)
        best_shot_candidate = shot
        no_cut_ratio = 0
        no_cut_config = (self.camera.location, self.camera.rotation_euler)
        correction = [141, 42, 59, 130, 130, 130, 130]
        #correction = [100, 100, 100, 100, 100, 100, 100]
        shots = [s for s in range(len(SHOT_NAMES)) if dist[s] > 0.1 or s == shot]
        print("Es kommen folgende Einstellungsgrößen in Frage: " + ", ".join([SHOT_NAMES[s] for s in shots]))
        #>>
        results = self.cameraOptimizer(scenicContext, target, linetarget, shots)
        for result in results:
            configuration = result[0]
            fitness = result[1]
            shot_number = result[2]
            print("Fitness " + str(fitness) + " for " + SHOT_NAMES[shot_number] + ".")
            ratio = 1 / fitness * dist[shot_number] * correction[shot_number]
            print("Ratio " + str(ratio) + " for " + SHOT_NAMES[shot_number] + ".")
            if shot_number == shot:
                no_cut_ratio = ratio
                no_cut_config = configuration
            if ratio > best_ratio:
                best_ratio = ratio
                best_config = configuration
                best_shot_candidate = shot_number

        # Should we Cut?
        if best_ratio - 0.1 > no_cut_ratio or initial_cut or cut: # We want to cut, the ratio gets much better
            shot = best_shot_candidate
            if (best_config[0] - self.camera.location).length < 0.8:
                new_configuration = self.springConfigurator(best_config)
                #new_configuration = best_config
                print("Es sollte geschnitten werden, die Abweichung war jedoch zu gering. Wir bleiben bei " +
                      SHOT_NAMES[shot])
            else:
                new_configuration = best_config
                last_cut = frame
                self.setInitialVelocity(target)
                print("Schnitt auf: " + SHOT_NAMES[shot])
        else: # We don't want to cut because the ratio doesn't get significantly better
            new_configuration = self.springConfigurator(no_cut_config)
            #new_configuration = no_cut_config
            print("Kein Schnitt. Wir bleiben bei " + SHOT_NAMES[shot])

        # Tell our decision to the classifier
        classificationProcess.stdin.write(b'd\n')
        classificationProcess.stdin.flush()
        classificationProcess.stdin.write((str(shot) + "\n").encode('utf-8'))
        classificationProcess.stdin.flush()
        if classificationProcess.stdout.readline().decode('utf-8').rstrip() != "decision recieved":
            print("Could not Write decision.")
        return new_configuration, shot, last_cut, target, linetarget


    def setCurrentFrame(self, frame_nr):
        bpy.data.scenes['Scene'].frame_current = frame_nr
        bpy.ops.object.paths_calculate()

    def setInitialVelocity(self, target):
        # Geschwindigkeit des Targets auf die Kamera übertragen.
        current_frame = bpy.data.scenes['Scene'].frame_current
        target_previous_position = Vector(target.location)
        self.setCurrentFrame(current_frame - 1)
        target_velocity = (target_previous_position - target.location) * 1.333333
        self.setCurrentFrame(current_frame)
        self.velocity = (target_velocity, Euler((0, 0, 0), 'XYZ'))

    def createScenicContext(self, process):
        context = {"persons": [], "objects": [], "places": []}
        process.stdin.write(b'e\n')
        process.stdin.flush()
        entities = pickle.load(process.stdout)
        context["persons"] = [bpy.data.objects[e.name] for e in entities["Persons"] if e.name]
        context["objects"] = [bpy.data.objects[e.name] for e in entities["Objects"] if e.name]
        context["places"] = [bpy.data.objects[e.name] for e in entities["Places"] if e.name]
        return context

    def createCameraObject(self):
        aperture = bpy.data.scenes['Scene'].camera.data.angle
        res_x = bpy.context.scene.render.resolution_x
        res_y = bpy.context.scene.render.resolution_y
        location = self.camera.location
        rotation = self.camera.rotation_euler
        return Camera(aperture, res_x, res_y, location, rotation)


    def cameraOptimizer(self, context, target, linetarget, shots):
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

        camera = self.createCameraObject()
        persons = [createPersonObject(p) for p in context['persons']]
        objects = [Object(o.name, o.location) for o in context['objects']]
        places = [Place(p.name, p.location) for p in context['places']]
        target_object = persons[context['persons'].index(target)]
        if linetarget in context['persons'] :
            linetarget_object = persons[context['persons'].index(linetarget)]
        elif linetarget in context['objects'] :
            linetarget_object = objects[context['objects'].index(linetarget)]
        else : # in places
            linetarget_object =places[context['places'].index(linetarget)]
        snapshot = SceneSnapshot(target_object, linetarget_object, camera, persons, objects, places, shots)
        pickle.dump(snapshot, optimizationProcess.stdin, protocol=2)
        #initStr = target.name + "\t" + linetarget.name + "\t"
        #initStr += str(bpy.data.scenes['Scene'].camera.data.angle) + "\t"
        #initStr += str(bpy.context.scene.render.resolution_x) + "\t"
        #initStr += str(bpy.context.scene.render.resolution_y) + "\t"
#        for person in context['persons']:
#            try:
#                personEyeL = bpy.data.objects[person.name + "_eye.L"].location
#                personEyeR = bpy.data.objects[person.name + "_eye.R"].location
#            except KeyError:
#                personEyeL = person.location
#                personEyeR = person.location
#            initStr += person.name + "§" + vectorToStr(person.location) + "§" + str(person.dimensions.z) +\
#                       "§" + vectorToStr(personEyeL) + "§" + vectorToStr(personEyeR) + ","
#        initStr = initStr.rstrip(",") + "\t"


#        for object in context['objects']:
#            initStr += object.name + "§" + vectorToStr(object.location) + ","
#        initStr = initStr.rstrip(",") + "\t"
        #initStr += vectorToStr(self.camera.location) + "," + vectorToStr(self.camera.rotation_euler) + "\t"
#        shotstr = ""
#        for shot in shots:
#            shotstr += str(shot) + ","
#        initStr += shotstr.rstrip(",")

        #optimizationProcess.stdin.write((initStr + "\n").encode('utf-8'))
        #optimizationProcess.stdin.flush()


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

    def springConfigurator(self, opt):

        opt[1].make_compatible(self.camera.rotation_euler)
        #print(self.velocity)
        vloc = self.velocity[0]
        vrot = self.velocity[1]
        aloc = (opt[0] - self.camera.location) * 14
        arot = Euler(((opt[1][0] - self.camera.rotation_euler[0]) * 9, 0, (opt[1][2] - self.camera.rotation_euler[2]) * 12), 'XYZ')
        #aloc = Vector((0,0,0))
        #arot = Euler((0,0,0),'XYZ')
        vloc += aloc * (1.0 / bpy.data.scenes['Scene'].render.fps)
        vrot = Euler((vrot[0] + arot[0] * (1.0 / bpy.data.scenes['Scene'].render.fps), 0,
                      vrot[2] + arot[2] * (1.0 / bpy.data.scenes['Scene'].render.fps)), 'XYZ')
        loc = self.camera.location + vloc * (1.0 / bpy.data.scenes['Scene'].render.fps)
        rot = Euler((self.camera.rotation_euler[0] + vrot[0] * (1.0 / bpy.data.scenes['Scene'].render.fps), 0,
                     self.camera.rotation_euler[2] + vrot[2] * (1.0 / bpy.data.scenes['Scene'].render.fps)), 'XYZ')
        self.velocity = (vloc * 0.75, Euler((vrot[0] * 0.75, 0, vrot[2] * 0.75), 'XYZ'))
        return loc, rot






    def startClassificationProcess(self):
        classification_process_filename = path.join(PROJECT_PATH, "BeatscriptClassifier.py")
        process = subprocess.Popen(
            [classification_process_filename,
             beatscript], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return process

    def waitForTrainingToFinish(self, classificationProcess):
        while True:
            input = classificationProcess.stdout.readline()
            print(input.decode('utf8').rstrip())
            if input.decode('utf8').rstrip() == "Training finished.":
                return

    def invoke(self, context, event):
        classificationProcess = self.startClassificationProcess()
        self.camera = bpy.data.scenes['Scene'].camera
        shot = 0
        lastcut = 0
        self.waitForTrainingToFinish(classificationProcess)
        scenicContext = self.createScenicContext(classificationProcess)
        target, linetarget = getTargets(classificationProcess)
        self.setCurrentFrame(1)
        self.setInitialVelocity(target)
        # >>
        newConfiguration, shot, lastcut, target, linetarget = self.calculateForNewBeats(classificationProcess, shot, 1,
            lastcut, True, scenicContext)

        self.setConfiguration(newConfiguration)
        print("Szenenkontext erzeugt.")
        for frame in range(2, bpy.context.scene.frame_end):
            self.setCurrentFrame(frame)
            print("Bearbeite Frame No. " + str(bpy.data.scenes['Scene'].frame_current))
            if frame - lastcut >= 19: # It's been 19 frames or more since the last cut
                # Are there new beats?
                classificationProcess.stdin.write(b'f\n')
                classificationProcess.stdin.flush()
                classificationProcess.stdin.write((str(frame) + "\n").encode('utf-8'))
                classificationProcess.stdin.flush()
                if classificationProcess.stdout.readline().decode('utf-8').rstrip() == "yes": # there are new beats
                    print("Neue Beats, neues Glück!")
                    newConfiguration, shot, lastcut, target, linetarget = self.calculateForNewBeats(classificationProcess,
                        shot, frame, lastcut,
                        False, scenicContext)
                else: # There were no new beats
                    print("Keine neuen Beats.")
                    optimalConfiguration, fitness, notused = self.cameraOptimizer(scenicContext, target, linetarget,
                        [shot])[0]
                    newConfiguration = self.springConfigurator(optimalConfiguration)
                    #newConfiguration = optimalConfiguration
            else: # It's too early to cut
                #optimalConfiguration, fitness = self.geneticConfigurator(scenicContext, target, linetarget, shot)
                optimalConfiguration, fitness, notused = self.cameraOptimizer(scenicContext, target, linetarget, [shot])[0]
                newConfiguration = self.springConfigurator(optimalConfiguration)
                #newConfiguration = optimalConfiguration
            self.setConfiguration(newConfiguration)
            bpy.data.scenes['Scene'].camera.data.dof_distance = (target.location - self.camera.location).length
            self.camera.data.keyframe_insert(data_path="dof_distance")
        classificationProcess.stdin.write(b'q\n')
        classificationProcess.stdin.flush()
        print("Classification Process: " + classificationProcess.stdout.readline().decode('utf-8').rstrip())
        classificationProcess.wait()
        return {"FINISHED"}

bpy.utils.register_class(AutomoculusCameraman)
