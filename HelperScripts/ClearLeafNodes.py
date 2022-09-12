import maya.cmds as cmds

#
# Leaf nodes usually don't get solved.  This script
# turns off the dof for all leaf nodes
#

def IsLeaf(node):
    bIs = True
    children = cmds.listRelatives(node,c=True)
    if children:
        bIs = False
    return bIs
    
def ClearLeafNodes():

    dags = cmds.ls(selection=True)
    #dags = cmds.ls(selection=True,ca=True) # Select just cameras
    for nodes in dags:
        n = str(nodes)
        
        if IsLeaf(nodes):
            cmds.setAttr("%s.ZRotDoF" %n, 0)
            cmds.setAttr("%s.YRotDoF" %n, 0)
            cmds.setAttr("%s.XRotDoF" %n, 0)

    
ClearLeafNodes()
