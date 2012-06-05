#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================== Imports ======================================
from __future__ import division
import sys
sys.path.append("..")

import unittest
from pylab import *

import PositionProcess
# ================================ Tests =======================================
class TestPositionProcessFunctions(unittest.TestCase):
    def test_angle(self):
        v1 = np.array([1, 0, 0])
        v1.reshape(-1, 1)
        v2 = np.array([1, 1, 0])
        v1.reshape(-1, 1)
        v3 = np.array([1, -1, 0])
        v1.reshape(-1, 1)
        v4 = np.array([0, 1, 0])
        v1.reshape(-1, 1)
        self.assertAlmostEqual(PositionProcess.angle(v1, v1), 0, 5)
        self.assertAlmostEqual(PositionProcess.angle(v1, v2), 1.5707969665527344 / 2, 5)
        self.assertAlmostEqual(PositionProcess.angle(v1, v3), 1.5707969665527344 / 2, 5)
        self.assertAlmostEqual(PositionProcess.angle(v1, v4), 1.5707969665527344, 5)

    def test_rotate(self):
        v1 = np.array([0, 0, -1])
        v1.reshape(-1, 1)
        genome = np.array([0, 0, 0, math.pi/2, 0])
        v2 = v1.dot(PositionProcess.rotate(genome))
        self.assertAlmostEqual(v2[0], 0, 5)
        self.assertAlmostEqual(v2[1], 1, 5)
        self.assertAlmostEqual(v2[2], 0, 5)
        genome = np.array([0, 0, 0, 0, math.pi/2])
        v2 = v1.dot(PositionProcess.rotate(genome))
        self.assertAlmostEqual(v2[0], 0, 5)
        self.assertAlmostEqual(v2[1], 0, 5)
        self.assertAlmostEqual(v2[2], -1, 5)
        genome = np.array([0, 0, 0, 0, math.pi*2.5])
        v2 = v1.dot(PositionProcess.rotate(genome))
        self.assertAlmostEqual(v2[0], 0, 5)
        self.assertAlmostEqual(v2[1], 0, 5)
        self.assertAlmostEqual(v2[2], -1, 5)
        genome = np.array([0, 0, 0, math.pi/2, math.pi])
        v2 = v1.dot(PositionProcess.rotate(genome))
        self.assertAlmostEqual(v2[0], 0, 5)
        self.assertAlmostEqual(v2[1], -1, 5)
        self.assertAlmostEqual(v2[2], 0, 5)
        genome = np.array([0, 0, 0, math.pi/2, math.pi*1.5])
        v2 = v1.dot(PositionProcess.rotate(genome))
        self.assertAlmostEqual(v2[0], 1, 5)
        self.assertAlmostEqual(v2[1], 0, 5)
        self.assertAlmostEqual(v2[2], 0, 5)
        genome = np.array([0, 0, 0, math.pi/2, math.pi*2.5])
        v2 = v1.dot(PositionProcess.rotate(genome))
        self.assertAlmostEqual(v2[0], -1, 5)
        self.assertAlmostEqual(v2[1], 0, 5)
        self.assertAlmostEqual(v2[2], 0, 5)
        genome = np.array([0, 0, 0, math.pi/2, math.pi/2])
        v2 = v1.dot(PositionProcess.rotate(genome))
        self.assertAlmostEqual(v2[0], -1, 5)
        self.assertAlmostEqual(v2[1], 0, 5)
        self.assertAlmostEqual(v2[2], 0, 5)
        v1 = np.array([0, 0, -1])
        v1.reshape(-1, 1)
        genome = np.array([0, 0, 0, math.pi/2, math.pi/4])
        v2 = v1.dot(PositionProcess.rotate(genome))
        self.assertAlmostEqual(PositionProcess.angle(v2, np.array([-1, 1, 0])), 0, 5)
        it = 1.0
        for x in range(0,int(it*math.pi)):
            for y in range(0,int(it*math.pi)):
                genome = np.array([0,0,0,y/it,x/it])
                v2 = v1.dot(PositionProcess.rotate(genome))
                self.assertAlmostEqual(np.sqrt(v2.dot(v2)),1,5)

    def test_angles(self):
        c = PositionProcess.Camera(math.pi/2, 1920, 1080)
        genome = np.array([0, 0, 0, math.pi/2, 0])
        o1 = PositionProcess.Object("o1", np.array([1, 1, 0]))
        xa, ya = PositionProcess.getImageAngles(genome, o1)
        x = xa * 2.0 / c.angle
        y = ya * 2.0 * c.resolution_x / (c.angle * c.resolution_y )
        self.assertAlmostEqual(x, 1, 5)
        self.assertAlmostEqual(y, 0, 5)
        o2 = PositionProcess.Object("o2", np.array([0, 1, tan(c.angle / 2 * c.resolution_y / c.resolution_x)]))
        xa, ya = PositionProcess.getImageAngles(genome, o2)
        x = xa * 2.0 / c.angle
        y = ya * 2.0 * c.resolution_x / (c.angle * c.resolution_y )
        self.assertAlmostEqual(x, 0, 5)
        self.assertAlmostEqual(y, 1, 5)
        o3 = PositionProcess.Object("o3", np.array([0.5, 1, 0.5 * tan(c.angle / 2 * c.resolution_y / c.resolution_x)]))
        xa, ya = PositionProcess.getImageAngles(genome, o3)
        x = xa * 2.0 / c.angle
        y = ya * 2.0 * c.resolution_x / (c.angle * c.resolution_y )
        self.assertAlmostEqual(x, arctan(0.5) / (c.angle / 2), 2)
        self.assertAlmostEqual(y, arctan(0.5) / (c.angle * c.resolution_y / c.resolution_x), 0)
        genome = np.array([0, 0, 0, math.pi/2, -math.pi/4])
        xa, ya = PositionProcess.getImageAngles(genome, o1)
        x = xa * 2.0 / c.angle
        y = ya * 2.0 * c.resolution_x / (c.angle * c.resolution_y )
        self.assertAlmostEqual(x, 0, 5)
        self.assertAlmostEqual(y, 0, 5)
        genome = np.array([0, 0, 0, math.pi/2, math.pi/4])
        xa, ya = PositionProcess.getImageAngles(genome, o1)
        x = xa * 2.0 / c.angle
        y = ya * 2.0 * c.resolution_x / (c.angle * c.resolution_y )
        self.assertAlmostEqual(x, 2, 5)
        self.assertAlmostEqual(y, 0, 5)
        genome = np.array([0, 0, 0, math.pi/2, math.pi/2])
        xa, ya = PositionProcess.getImageAngles(genome, o1)
        x = xa * 2.0 / c.angle
        y = ya * 2.0 * c.resolution_x / (c.angle * c.resolution_y )
        self.assertAlmostEqual(x, 3, 5)
        self.assertAlmostEqual(y, 0, 5)
        genome = np.array([0, 0, 0, math.pi/2, math.pi])
        xa, ya = PositionProcess.getImageAngles(genome, o1)
        x = xa * 2.0 / c.angle
        y = ya * 2.0 * c.resolution_x / (c.angle * c.resolution_y )
        self.assertAlmostEqual(x, 3, 5)
        self.assertAlmostEqual(y, 0, 5)

    def test_plot_rotation(self):
        c = PositionProcess.Camera(0.48271098732948303, 1920, 1080)
        genome = np.array([5, 0, 0, math.pi / 2, 0, math.pi])
        t = PositionProcess.Person('Max Mustermann', np.array([0, 0, 0]).reshape(-1, 1), 1,
            np.array([0.7, -0.2, 0]).reshape(-1, 1), np.array([0.7, 0.2, 0]).reshape(-1, 1))
        lt = PositionProcess.Person('Agnes Angeschaute', np.array([2, 0, 0]).reshape(-1, 1), 1,
            np.array([1.3, -0.2, 0]).reshape(-1, 1), np.array([1.3, 0.2, 0]).reshape(-1, 1))
        #PositionProcess.optimizeAllShots(t, t, c, [t], [], genome, [2])
        optimizer = PositionProcess.CameraOptimizer(t, lt, c, [t, lt], [], genome, 2)
        #optimizer.fitness(genome)
        winkel = arange(-math.pi, math.pi, 0.01)
        s = arange(-math.pi, math.pi, 0.01)
        startposition = np.array([5, 0, 0])
        #startposition.reshape(-1, 1)
        for i in range(0, len(winkel)):
            p = startposition.dot(PositionProcess.rotate(np.array([0, 0, 0, math.pi / 2, winkel[i]])))
            s[i] = optimizer.fitness(np.array([p[0],p[1],p[2],math.pi/2,winkel[i]+0.5*math.pi]))
            #s[i] = optimizer.fitness(np.array([5,0,0,math.pi/2,winkel[i]+math.pi/2]))
            #s[i] = optimizer.getPersonQuality(np.array([p[0],p[1],p[2], math.pi / 2, winkel[i] + math.pi/2]), t, 1.2,
            #    personFitnessByImage, occultationWeight)
            #s[i] = optimizer.getPersonQuality(np.array([5,0,0, math.pi / 2, winkel[i] + math.pi/2]), t, 1.2,
            #    personFitnessByImage, occultationWeight)
            #s[i] = PositionProcess.getImageAngles(np.array([p[0],p[1],p[2], math.pi / 2, winkel[i] + math.pi*0.5]), t)[0]
            #s[i] = PositionProcess.getImageAngles(np.array([5,0,0,winkel[i]+math.pi / 2, math.pi/2]), t)[0]
        ax = subplot(111)
        ax.plot(winkel, s)
        ax.grid(True)
        ticklines = ax.get_xticklines()
        ticklines.extend(ax.get_yticklines())
        gridlines = ax.get_xgridlines()
        gridlines.extend(ax.get_ygridlines())
        ticklabels = ax.get_xticklabels()
        ticklabels.extend(ax.get_yticklabels())
        for line in ticklines:
            line.set_linewidth(3)
        for line in gridlines:
            line.set_linestyle('-')
        for label in ticklabels:
            label.set_color('r')
            label.set_fontsize('medium')
        show()

suite = unittest.TestLoader().loadTestsFromTestCase(TestPositionProcessFunctions)
unittest.TextTestRunner(verbosity=2).run(suite)

