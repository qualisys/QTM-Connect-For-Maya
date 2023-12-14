import maya.cmds as cmds

def ClearPreferredAngle():

    dags = cmds.ls(selection=True)
    for nodes in dags:
        n = str(nodes)
        

        cmds.setAttr("%s.preferredAngleX" % n, 0)
        cmds.setAttr("%s.preferredAngleY" % n, 0)
        cmds.setAttr("%s.preferredAngleZ" % n, 0)
            
ClearPreferredAngle()
