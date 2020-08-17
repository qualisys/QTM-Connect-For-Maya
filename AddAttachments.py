import maya.cmds as cmds

def AddAttachments():
    nodes = cmds.ls( selection=True, type='dagNode')
    #print nodes
    j = nodes[0]
    jointName = str(j)
    
    for m in nodes:
        if m != j:
            #markerName = str(m)
            #remove namespaces and leave just the marker name
            markerName = str(m).split(":")[-1]
            a = jointName+"."+markerName
            if cmds.attributeQuery(markerName,node=jointName, exists=True):
                print "Attachment", markerName, "already exists"
            else:
                a = jointName + "." + markerName
                print a
                cmds.addAttr(jointName,ln=markerName, defaultValue=1.0)
        

