import maya.cmds as cmds


    
def ClearSelectedNodes():

    dags = cmds.ls(selection=True)
    #dags = cmds.ls(selection=True,ca=True) # Select just cameras
    for nodes in dags:
        n = str(nodes)
        

        cmds.setAttr("%s.ZRotDoF" %n, 0)
        cmds.setAttr("%s.YRotDoF" %n, 0)
        cmds.setAttr("%s.XRotDoF" %n, 0)

    
ClearSelectedNodes()
