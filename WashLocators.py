import xml.etree.ElementTree as ET
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import math
import os

def WashLocators():

    nodes = cmds.ls( selection=True, type='dagNode')
    
    for oldloc in nodes:
        cn = cmds.xform( str(oldloc), q=True, matrix=True, ws=True)
        x = cn[3][0]
        y = cn[3][1]
        z = cn[3][2]
        #print x, y, z
        NewLoc = "New_"+str(oldloc)
        loc = cmds.spaceLocator(name=NewLoc)
        #cmds.select(ParentNode, add=True)
        cmds.setAttr("%s.overrideEnabled" % NewLoc, 1)
        cmds.setAttr("%s.overrideColor" % NewLoc, 22)
        cmds.select(loc)
        cmds.move(x,y,z)
        cmds.scale(2,2,2)