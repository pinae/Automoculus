#!/usr/bin/python
# coding=utf-8
from __future__ import division, print_function, unicode_literals

class Object(object):
    def __init__(self, name, location):
        self.name = name
        self.location = tuple(location)
        self.radius = 0.1

class PersonAddition(object):
    def __init__(self, name, location):
        self.name = name
        self.location = tuple(location)
        self.radius = 0

class Person(object):
    def __init__(self, name, location, height, left_eye_loc, right_eye_loc):
        self.name = name
        self.location = tuple(location)
        self.height = height
        self.eye_L = PersonAddition(name + "_eye.L", left_eye_loc)
        self.eye_R = PersonAddition(name + "_eye.R", right_eye_loc)
        self.radius = 1.0#0.1

class Camera(object):
    def __init__(self, aperture_angle, resolution_x, resolution_y, location, rotation):
        self.aperture_angle = aperture_angle
        self.resolution_x = resolution_x
        self.resolution_y = resolution_y
        self.location = tuple(location)
        self.rotation = tuple(rotation)

    def getConfiguration(self):
        return self.location + (self.rotation[0], self.rotation[2])


class SceneSnapshot(object):
    def __init__(self, target, linetarget, camera, persons, objects, places, shots):
        self.target = target
        self.linetarget = linetarget
        self.camera = camera
        self.persons = persons
        self.objects = objects
        self.places = places
        self.shots = shots

class Place(object):
    def __init__(self, name, location):
        self.name = name
        self.location = tuple(location)