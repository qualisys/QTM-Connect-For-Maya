import maya.cmds as cmds

    
# AddEndEffectors()

#
# Adds end effector joints so the solver XML export will have a way of adding
# the endpoint attribute to the leaf segments.
#
# Originally written to augment end joints on 
# Metahuman skeletons
#

def is_leaf(jointNode):
    children = cmds.listRelatives(jointNode,c=True)
    if children:
        return False
    return True

def add_end_joint(dag):
    parent = str(dag)
    name = parent + "_end"
    x = cmds.getAttr("%s.translateX" % parent)
    cmds.select(dag)
    j = cmds.joint(name = name)
    cmds.setAttr("%s.translateX" % name, x) 


def AddEndEffectors():

    dags = cmds.ls(selection=True)
    for dag in dags:
        if is_leaf(dag):
            add_end_joint(dag)

            
AddEndEffectors()
