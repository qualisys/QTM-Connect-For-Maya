import maya.cmds as cmds

    
# RemoveFixedJoints()

#
# Removes any joints that don't have rotation DOFS.
# Originally written to remove all the extra joints on 
# Metahuman skeletons
#

def RemoveFixedJoints():

    dags = cmds.ls(selection=True)
    for nodes in dags:
        n = str(nodes)
        bHasAttributes = cmds.attributeQuery("XRotDoF",node=n, exists=True)
        
        if not bHasAttributes:
            cmds.removeJoint(nodes)

            
RemoveFixedJoints()