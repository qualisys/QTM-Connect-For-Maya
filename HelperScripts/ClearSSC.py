import maya.cmds as cmds

def ClearSegmentScaleCompensate():

    dags = cmds.ls(selection=True)
    for nodes in dags:
        n = str(nodes)
        

        cmds.setAttr("%s.segmentScaleCompensate" % n, 0)

            
ClearSegmentScaleCompensate()