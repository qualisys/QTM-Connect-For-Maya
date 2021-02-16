import xml.etree.ElementTree as ET
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import math
import os
from pymel.all import *
import pymel.core.datatypes as dt

def WashLocators():

    nodes = cmds.ls( selection=True, type='dagNode')
    
    for oldloc in nodes:
        cn = xform( str(oldloc), q=True, matrix=True, ws=True)
        cm = dt.Matrix(cn)
        x = cm[3][0]
        y = cm[3][1]
        z = cm[3][2]
        #print x, y, z
        NewLoc = "New_"+str(oldloc)
        loc = cmds.spaceLocator(name=NewLoc)
        #cmds.select(ParentNode, add=True)
        cmds.setAttr("%s.overrideEnabled" % NewLoc, 1)
        cmds.setAttr("%s.overrideColor" % NewLoc, 22)
        cmds.select(loc)
        cmds.move(x,y,z)
        cmds.scale(3,3,3)