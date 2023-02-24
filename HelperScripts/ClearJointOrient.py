import maya.cmds as cmds

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
def IsLeaf(node):
    bIs = True
    children = cmds.listRelatives(node,c=True)
    if children:
        bIs = False
    return bIs
    
def ClearJointOrient():

    dags = cmds.ls(selection=True)
    #dags = cmds.ls(selection=True,ca=True) # Select just cameras
    for nodes in dags:
        if not IsLeaf(nodes):
            n = str(nodes)
            #setAttr "Arqus_A12_SL_Shape78.farClipPlane" 100;
            #cmds.setAttr("%s.farClipPlane" %n, 100)
        
            cmds.setAttr("%s.XRotDoF_LowerBound" %n, -360)
            cmds.setAttr("%s.YRotDoF_LowerBound" %n, -360)
            cmds.setAttr("%s.ZRotDoF_LowerBound" %n, -360)
            cmds.setAttr("%s.XRotDoF_UpperBound" %n, 360)
            cmds.setAttr("%s.YRotDoF_UpperBound" %n, 360)
            cmds.setAttr("%s.ZRotDoF_UpperBound" %n, 360)
        #xrot = cmds.getAttr("%s.rotateX" % n)
        #yrot = cmds.getAttr("%s.rotateY" % n)
        #zrot = cmds.getAttr("%s.rotateZ" % n)
        #xrot_jo = cmds.getAttr("%s.jointOrientX" % n)
        #yrot_jo = cmds.getAttr("%s.jointOrientY" % n)
        #zrot_jo = cmds.getAttr("%s.jointOrientZ" % n)
        
        #print("Rot=", xrot, yrot, zrot, "   JointOrient=", xrot_jo, yrot_jo, zrot_jo)
    
        #cmds.setAttr("%s.rotateX" % n, xrot + xrot_jo)
        #cmds.setAttr("%s.rotateY" % n, yrot + yrot_jo)
        #cmds.setAttr("%s.rotateZ" % n, zrot + zrot_jo)
        #cmds.setAttr("%s.jointOrientX" % n, 0)
        #cmds.setAttr("%s.jointOrientY" % n, 0)
        #cmds.setAttr("%s.jointOrientZ" % n, 0) 
        #cmds.setAttr("%s.preferredAngleX" % n, 0)
        #cmds.setAttr("%s.preferredAngleY" % n, 0)
        #cmds.setAttr("%s.preferredAngleZ" % n, 0)         
        
        #cmds.setAttr("%s.segmentScaleCompensate" %n, 0)
        
        #cmds.setAttr("%s.ZRotDoF" %n, 0)
        #cmds.setAttr("%s.YRotDoF" %n, 0)
        #cmds.setAttr("%s.XRotDoF" %n, 0)

    
ClearJointOrient()
