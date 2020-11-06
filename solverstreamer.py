import hashlib, os
import ast
import xml.etree.ElementTree as ET
import QImportSolver
import QExportSolver

from PySide2 import QtGui
from PySide2 import QtWidgets

import maya.cmds as cmds
import maya.api.OpenMaya as om

from mayaui import load_icon
from mayautil import MayaUtil

def Spaces(level):
    r = ""
    for i in range(0,level):
        r = r + "    "
    return r

def myPrettyPrint(d,level=0):
    if type(d) is dict:
        for x in d:
            dx = d[x]
            if type(dx) is dict:
                print Spaces(level), x
                myPrettyPrint( d[x], level+1)
            else:
                print Spaces(level), type(dx), x, "=", dx
    else:
        print Spaces(level+1), "??", d

class SolverStreamer:
    def __init__(self, qtmrt):
        self._qtm = qtmrt
        self._skeletons = None
        
    def ET_HandlerPull(self, sXML):
        print "QImportSolver Start"

        xml_root = ET.fromstring(sXML)
        if xml_root is not None:
            sV2 = xml_root.find("Skeletons")

            if sV2 is not None:
                QIS = QImportSolver.QImportSolver()
                QIS.SetSceneScale()
                QIS.ImportQTMSkeletonFile(sV2)
                #print "XML Start sV2"
                #print sXML
                #print "XML End sV2"
            else:
                print "No Skeleton"
        else:
            print "No xml_root"
            
        print "QImportSolver End"

    def ET_HandlerPush(self):
        QES = QExportSolver.QExportSolver()
        QES.SetSceneScale()
        sXML = QES.ExportQTMSkeletonFile(None)

        return sXML    
        
    def PrettyPrint(self,lSkeletons):
        self._skeletons = ast.literal_eval(lSkeletons)
        if type(self._skeletons) is list:
            print self._skeletons[0]
        elif type(self._skeletons) is dict:
            for x in self._skeletons:
                print x
                myPrettyPrint(self._skeletons[x])
        else:
            print self._skeletons
        
        
