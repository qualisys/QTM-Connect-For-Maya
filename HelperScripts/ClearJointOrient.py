import maya.cmds as cmds

    
# ClearJointOrient()

#
# ClearJointOrient moves the Joint Orient values into the regular 
# rotation channels.  Solver doesn't support the JointOrient value
# so they must all be zero for solving and later streaming onto
# the skeleton.
#
# Segment scale compensate is also set to a value so that
# scaling the hips or pelvis joint does the right thing.
#
# Also note in comments other useful items to set for joints.
#

def ClearJointOrient():

    dags = cmds.ls(selection=True)
    for nodes in dags:
        n = str(nodes)
        
        rot = cmds.xform(n, q=True, rotation=True, ws=True)
        cmds.setAttr("%s.jointOrientX" % n, 0)
        cmds.setAttr("%s.jointOrientY" % n, 0)
        cmds.setAttr("%s.jointOrientZ" % n, 0) 
         
        
        cmds.setAttr("%s.segmentScaleCompensate" %n, 0)
        
        cmds.xform(n, ws=True, ro=(rot[0],rot[1],rot[2]))

        xrot = cmds.getAttr("%s.rotateX" % n)
        yrot = cmds.getAttr("%s.rotateY" % n)
        zrot = cmds.getAttr("%s.rotateZ" % n)
        cmds.setAttr("%s.preferredAngleX" % n, xrot)
        cmds.setAttr("%s.preferredAngleY" % n, yrot)
        cmds.setAttr("%s.preferredAngleZ" % n, zrot)
            
ClearJointOrient()
