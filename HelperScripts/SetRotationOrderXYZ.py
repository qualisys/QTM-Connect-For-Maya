import maya.cmds as cmds

#
# QTM streaming only supports the default rotation order
# this script sets the selected joints to the correct order.
#
def SetRotationOrderXYZ():

    dags = cmds.ls(selection=True)
    #dags = cmds.ls(selection=True,ca=True) # Select just cameras
    for nodes in dags:
        n = str(nodes)
        
        cmds.setAttr ("%s.rotateOrder" %n, 0);
        
    
SetRotationOrderXYZ()