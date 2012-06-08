#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================== Imports ======================================
import sys

sys.path.append("..")

import unittest

import Beatscript
import Config
import ConvertData


# ================================ Tests =======================================
class TestConvertDataFunctions(unittest.TestCase):
    def test_entityList(self):
        context = ConvertData.createContext()
        Beatscript.addEntityList(context, "person§Karl, person§Hugo,\tobject§Table,place§Home,\t")
        self.assertTrue("Table" in context["Entities"] and context["Entities"]["Table"].type == Config.OBJECT)
        self.assertTrue("Karl" in context["Entities"] and context["Entities"]["Karl"].type == Config.PERSON)
        self.assertTrue("Hugo" in context["Entities"] and context["Entities"]["Hugo"].type == Config.PERSON)
        self.assertTrue("Home" in context["Entities"] and context["Entities"]["Home"].type == Config.PLACE)
        self.assertFalse("Peter" in context["Entities"])
        self.assertTrue(len(context["Entities"]) == 4)

    def test_initialContext(self):
        context = ConvertData.createContext()
        Beatscript.addInitialContext(context, "person§Peter, person§Hugo,\tobject§Table,place§Home, person§Lord Harthorne,")
        Beatscript.addEntityList(context, "person§Karl, person§Hugo,\tobject§Table,place§Home, ")
        self.assertTrue(context["Entities"]["Table"] in context["KnownEntities"])
        self.assertTrue(context["Entities"]["Hugo"] in context["KnownEntities"])
        self.assertTrue(context["Entities"]["Home"] in context["KnownEntities"])
        self.assertFalse(context["Entities"]["Karl"] in context["KnownEntities"])
        self.assertTrue(len(context["KnownEntities"]) == 5)
        for entity in context["KnownEntities"]:
            if entity.name not in context["Entities"]:
                self.assertTrue(False)
        for entityName in context["Entities"]:
            if context["Entities"][entityName] not in context["KnownEntities"]:
                self.assertTrue(entityName=="Karl" and context["Entities"][entityName].type == Config.PERSON)

    def test_readContext(self):
        textfile = ["#Film:\tTestfilm",
                    "#Scene:\tTestszene",
                    "#FPS:\t25",
                    "#Context:\tperson§Hugo, person§Alexander the Great",
                    "#EntityList:\tobject§Rope, place§Room, object§Hugos Thing"]
        context = ConvertData.readContext(textfile)
        self.assertTrue(context["Film"]=="Testfilm")
        self.assertTrue(context["Scene"]=="Testszene")
        self.assertTrue(context["FPS"]==25)
        self.assertTrue(context["Entities"]["Hugo"].type == Config.PERSON)
        self.assertTrue(context["Entities"]["Alexander the Great"].type == Config.PERSON)
        self.assertTrue(context["Entities"]["Rope"].type == Config.OBJECT)
        self.assertTrue(context["Entities"]["Room"].type == Config.PLACE)
        self.assertTrue(context["Entities"]["Hugos Thing"].type == Config.OBJECT)

suite = unittest.TestLoader().loadTestsFromTestCase(TestConvertDataFunctions)
unittest.TextTestRunner(verbosity=2).run(suite)

