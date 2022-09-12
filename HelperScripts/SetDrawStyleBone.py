import maya.cmds as cmds

#
# Sometimes skeletons have bones that are not visible because the draw style
# is set to None.  This sets the selected ones to Bone so they're visible.
# Metahuman finger bones sometimes import with None as the draw style.
#    
def SetDrawStyle():

    dags = cmds.ls(selection=True)
    #dags = cmds.ls(selection=True,ca=True) # Select just cameras
    for nodes in dags:
        n = str(nodes)
        
        cmds.setAttr("%s.drawStyle" %n, 0)
        #cmds.setAttr("%s.radius" %n, .1)

    
SetDrawStyle()
