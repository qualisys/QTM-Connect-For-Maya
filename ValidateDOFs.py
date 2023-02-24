"""
Validate DOFS - Run through all the keyframes and check that the 
joint angles are not too close to their solver limits
"""

import maya.cmds as cmds
def local_rot(n):
    x =  cmds.getAttr(f"{str(n)}.rotateX")
    y =  cmds.getAttr(f"{str(n)}.rotateY")
    z =  cmds.getAttr(f"{str(n)}.rotateZ")
    return x,y,z

def validate_node(dag, time):
    x,y,z = local_rot(dag)
    name = str(dag)
    if cmds.getAttr("%s.XRotDoF" % name):
        lb = cmds.getAttr("%s.XRotDoF_LowerBound" % name)
        ub = cmds.getAttr("%s.XRotDoF_UpperBound" % name)
        if x < lb:
            print(f"At time {time} {name} is out of X range low. {x} < {lb}")
        if x > ub:
            print(f"At time {time} {name} is out of X range high. {x} > {ub}")

    if cmds.getAttr("%s.YRotDoF" % str(dag)):
        lb = cmds.getAttr("%s.YRotDoF_LowerBound" % name)
        ub = cmds.getAttr("%s.YRotDoF_UpperBound" % name)
        if y < lb:
            print(f"{name} is out of Y range low. {y} < {lb}")
        if y > ub:
            print(f"{name} is out of Y range high. {y} > {ub}")

    if cmds.getAttr("%s.ZRotDoF" % str(dag)):
        lb = cmds.getAttr("%s.ZRotDoF_LowerBound" % name)
        ub = cmds.getAttr("%s.ZRotDoF_UpperBound" % name)
        if z < lb:
            print(f"{name} is out of Z range low. {z} < {lb}")
        if z > ub:
            print(f"{name} is out of Z range high. {z} > {ub}")

def IsLeaf(node):
    bIs = True
    children = cmds.listRelatives(node,c=True)
    if children:
        bIs = False
    return bIs

def validate_dofs():
    dags = cmds.ls(selection=True)
    if len(dags) == 0:
        print(f"Please select the joints to validate.")
        return
    dag = dags[0]
    keys = cmds.keyframe(dag,q=True)
    if keys:
        sorted_keys = sorted(keys)
        print(f"Start: {sorted_keys[0]}  End: {sorted_keys[-1]}")        
        for key in sorted_keys:
            cmds.currentTime(key)
            for dag in dags:
                if not IsLeaf(dag):
                    validate_node(dag,key)
validate_dofs()
