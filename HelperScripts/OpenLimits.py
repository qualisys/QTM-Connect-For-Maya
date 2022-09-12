import maya.cmds as cmds

#
# Make the limits -360 to 360 on all selected joints
# This is to avoid Solver problems with getting stuck
# at a joint limit
#
def IsLeaf(node):
    bIs = True
    children = cmds.listRelatives(node,c=True)
    if children:
        bIs = False
    return bIs
    
def OpenLimits():

    dags = cmds.ls(selection=True)
    #dags = cmds.ls(selection=True,ca=True) # Select just cameras
    for nodes in dags:
        n = str(nodes)
        if not IsLeaf(n):
            cmds.setAttr("%s.XRotDoF_LowerBound" %n, -360)
            cmds.setAttr("%s.YRotDoF_LowerBound" %n, -360)
            cmds.setAttr("%s.ZRotDoF_LowerBound" %n, -360)
            cmds.setAttr("%s.XRotDoF_UpperBound" %n, 360)
            cmds.setAttr("%s.YRotDoF_UpperBound" %n, 360)
            cmds.setAttr("%s.ZRotDoF_UpperBound" %n, 360)

    
OpenLimits()
