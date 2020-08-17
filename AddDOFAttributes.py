import xml.etree.ElementTree as ET
import maya.cmds as cmds
import math
import os
from pymel.all import *

def AddDOFAttributes():

    dags = cmds.ls(selection=True)
    for nodes in dags:
        n = str(nodes)

        cmds.addAttr(n,ln="XRotDoF",at="bool")
        cmds.setAttr(n+ ".XRotDoF", True)
        cmds.addAttr(n,ln="XRotDoF_LowerBound", defaultValue=-360)
        cmds.addAttr(n,ln="XRotDoF_UpperBound", defaultValue=360)
    
        cmds.addAttr(n,ln="YRotDoF",at="bool")
        cmds.setAttr(n+".YRotDoF", True)
        cmds.addAttr(n,ln="YRotDoF_LowerBound", defaultValue=-360)
        cmds.addAttr(n,ln="YRotDoF_UpperBound", defaultValue=360)
    
        cmds.addAttr(n,ln="ZRotDoF",at="bool")
        cmds.setAttr(n+".ZRotDoF", True)
        cmds.addAttr(n,ln="ZRotDoF_LowerBound", defaultValue=-360)
        cmds.addAttr(n,ln="ZRotDoF_UpperBound", defaultValue=360)
    
        cmds.addAttr(n,ln="XTransDoF",at="bool")
        cmds.setAttr(n+ ".XTransDoF", False)
        cmds.addAttr(n,ln="YTransDoF",at="bool")
        cmds.setAttr(n+ ".YTransDoF", False)
        cmds.addAttr(n,ln="ZTransDoF",at="bool")
        cmds.setAttr(n+ ".ZTransDoF", False)
    
    
AddDOFAttributes()
