"""
Fit the selected QTM Animation skeleton to the matching marker cloud.
"""

import maya.cmds as cmds
import numpy as np
import math
#import scipy
import importlib
import os, sys
here = "C:/Program Files/Autodesk/Maya2023/bin/qtm_connect_maya/"
if not here in sys.path:
    sys.path.append("C:/Program Files/Autodesk/Maya2023/bin/qtm_connect_maya/")

import qscipy
importlib.reload(qscipy)

def normalize(n):
    l = np.linalg.norm(n)
    return n/l
def OrthogonalizeV2(v1,v2):
    c = np.cross(v1,v2)
    o = normalize(np.cross(c,v1))
    return o
def MarkerPos(markername,markerset):
    fullname = f"{markerset}:{markername}"
    node = cmds.ls(fullname)
    retval = np.array([0.0,0.0,0.0])
    if node is None:
        print(f"Could not find marker position for {fullname}")
        return retval
    a = f"{markerset}:{markername}.translateX"
    retval[0] = cmds.getAttr(a)
    a = f"{markerset}:{markername}.translateY"
    retval[1] = cmds.getAttr(a)
    a = f"{markerset}:{markername}.translateZ"
    retval[2] = cmds.getAttr(a)
    return retval

def JointPos(jointname, markerset):
    fullname = f"{markerset}:ModelPose:{jointname}"
    world_mat = cmds.xform(fullname, q=True, m=True, ws=True)
    #print(f"{fullname} world matrix is {world_mat}")
    retval = np.array(world_mat[12:15])
    return retval
def JointPosLocal(jointname, markerset):
    fullname = f"{markerset}:ModelPose:{jointname}"
    p = np.array([0.0,0.0,0.0])
    p[0] =  cmds.getAttr(f"{markerset}:ModelPose:{jointname}.translateX")
    p[1] =  cmds.getAttr(f"{markerset}:ModelPose:{jointname}.translateY")
    p[2] =  cmds.getAttr(f"{markerset}:ModelPose:{jointname}.translateZ")
    return p
    
def JointRot(jointname,markerset):
    fullname = f"{markerset}:ModelPose:{jointname}"
    e = np.array([0.0,0.0,0.0])
    e[0] =  cmds.getAttr(f"{markerset}:ModelPose:{jointname}.rotateX")
    e[1] =  cmds.getAttr(f"{markerset}:ModelPose:{jointname}.rotateY")
    e[2] =  cmds.getAttr(f"{markerset}:ModelPose:{jointname}.rotateZ")
    R = qscipy.QRotation.from_euler("xyz",e)
    return R

def RotationFromReference(v_up, v_front):
    """ 
    Return the global rotation from the given reference frame described by an up vector
    and a front vector.  These two do not have to be perfectly orthogonal nor unit vectors.
    The up vector maps to Z, the front vector to Y.
    """
    Z = normalize(v_up)
    X = normalize(np.cross(v_front,Z))
    Y = normalize(np.cross(Z,X))
    R = scipy.spatial.transform.Rotation.from_matrix([X,Y,Z])
    return R.inv()

def QRotationFromReference(v_up, v_front):
    """ 
    Return the global rotation from the given reference frame described by an up vector
    and a front vector.  These two do not have to be perfectly orthogonal nor unit vectors.
    The up vector maps to Z, the front vector to Y.
    """
    Z = normalize(v_up)
    X = normalize(np.cross(v_front,Z))
    Y = normalize(np.cross(Z,X))
    R = qscipy.QRotation.from_matrix([X,Y,Z])
    return R

def RotationBetweenVectors(v1,v2):
    axis = np.cross(v1,v2)
    l = np.linalg.norm(axis)
    if l < 0.0001:
        R = scipy.spatial.transform.Rotation.from_euler("xyz",np.array([0.0,0.0,0.0]))
    else:
        theta = np.arcsin(l)
        rotvec = normalize(axis)*theta
        R = scipy.spatial.transform.Rotation.from_rotvec(rotvec)
    return R
def QRotationBetweenVectors(v1,v2):
    axis = np.cross(v1,v2)
    l = np.linalg.norm(axis)
    if not math.isclose(l+1.0,1.0):
        theta = np.arcsin(l)
        R = qscipy.QRotation.from_axis_angle(normalize(axis), theta)
    else:
        R = qscipy.QRotation()
    return R
def SetJointLocal(jointname,markerset,pos,rot):
    fullname = f"{markerset}:ModelPose:{jointname}"
    if pos is not None:
        cmds.setAttr(f"{fullname}.translateX", pos[0])
        cmds.setAttr(f"{fullname}.translateY", pos[1])
        cmds.setAttr(f"{fullname}.translateZ", pos[2])
    cmds.setAttr(f"{fullname}.rotateX", rot[0])
    cmds.setAttr(f"{fullname}.rotateY", rot[1])
    cmds.setAttr(f"{fullname}.rotateZ", rot[2])

def SetJointGlobal(jointname,markerset,pos,rot):
    fullname = f"{markerset}:ModelPose:{jointname}"
    if pos is not None:
        cmds.xform(fullname, ws=True, ro=(rot[0],rot[1],rot[2]), t=(pos[0],pos[1],pos[2]))
    else:
        cmds.xform(fullname, ws=True, ro=(rot[0],rot[1],rot[2]))

#
# The aim of each rule is to find the Z (up) axis and the
# Y (front) axis.  From this a global rotation value is
# computed and then set in the node.
def _Hips_rule(joint,markers,markerset):
    WRB = MarkerPos("WaistRBack",markerset)
    WLB = MarkerPos("WaistLBack",markerset)
    CenterBack = np.add(WRB,WLB) * 0.5
    WRF = MarkerPos("WaistRFront",markerset)
    WLF = MarkerPos("WaistLFront",markerset)
    CenterFront = np.add(WRF,WLF) * 0.5
    CenterVec = normalize(np.subtract(CenterFront, CenterBack))
    HipsEnd = np.add(CenterBack,CenterVec * 5)

    BackL = MarkerPos("BackL",markerset)
    BackR = MarkerPos("BackR",markerset)
    MidBack = np.add(BackL,BackR)*0.5
    DownVec = np.array([0.0,0.0,-1.0])
    HipsStart = np.add(HipsEnd, DownVec * 10)
    
    HipsUp = normalize(np.subtract(HipsEnd, HipsStart))
    HipsForward = OrthogonalizeV2(HipsUp,CenterVec)

    #RTotal = RotationFromReference(HipsUp,HipsForward)
    QRTotal = QRotationFromReference(HipsUp,HipsForward)
    #e = RTotal.as_euler("xyz",degrees =True)
    qe = QRTotal.as_euler("xyz")
    #print(f"scipy euler {e}")
    #print(f"QScipy euler {qe}")
    SetJointGlobal("Hips", markerset, HipsStart,qe)
    
def _Spine_rule(joint,markers,markerset):
    SpineTop = MarkerPos("SpineTop",markerset)
    Chest = MarkerPos("Chest",markerset)
    SpineTopChestVec = normalize(np.subtract(Chest,SpineTop))
    Spine = JointPos("Spine",markerset)

    UpVec = normalize(np.subtract(SpineTop,Spine))
    FrontVec = SpineTopChestVec

    RTotal = QRotationFromReference(UpVec,FrontVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal("Spine", markerset, None,e)

def _Spine1_rule(joint,markers,markerset):
    SpineTop = MarkerPos("SpineTop",markerset)
    Chest = MarkerPos("Chest",markerset)
    SpineTopChestVec = normalize(np.subtract(Chest,SpineTop))
    Spine1 = JointPos("Spine1",markerset)

    UpVec = normalize(np.subtract(SpineTop,Spine1))
    FrontVec = SpineTopChestVec

    RTotal = QRotationFromReference(UpVec,FrontVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal("Spine1", markerset, None,e)

def _Spine2_rule(joint,markers,markerset):
    SpineTop = MarkerPos("SpineTop",markerset)
    Chest = MarkerPos("Chest",markerset)
    SpineTopChestVec = normalize(np.subtract(Chest,SpineTop))
    Spine2 = JointPos("Spine2",markerset)

    UpVec = normalize(np.subtract(SpineTop,Spine2))
    FrontVec = SpineTopChestVec

    RTotal = QRotationFromReference(UpVec,FrontVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal("Spine2", markerset, None,e)

def _LeftShoulder_rule(joint,markers,markerset):
    LArm = MarkerPos("LArm",markerset)
    LElbowOut = MarkerPos("LElbowOut",markerset)
    SpineTop = MarkerPos("SpineTop",markerset)
    LeftShoulder = JointPos("LeftShoulder",markerset)
    Spine2 = JointPos("Spine2",markerset)
    Neck = JointPos("Neck",markerset)
    MidElbow = np.add(LArm, LElbowOut) * 0.5
    ShoulderToElbowVec = normalize(np.subtract(LeftShoulder,MidElbow))

    UpVec = normalize(np.subtract(Neck,Spine2))
    FrontVec = np.cross(UpVec,ShoulderToElbowVec)

    RTotal = QRotationFromReference(UpVec,FrontVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal("LeftShoulder", markerset, None,e)

def _LeftArm_rule(joint,markers,markerset):
    LArm = MarkerPos("LArm",markerset)
    LElbowOut = MarkerPos("LElbowOut",markerset)
    SpineTop = MarkerPos("SpineTop",markerset)
    LeftArm = JointPos("LeftArm",markerset)
    MidElbow = np.add(LArm, LElbowOut) * 0.5
    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    HandOut = MarkerPos("LHandOut",markerset)
    WristVec = normalize(np.subtract(WristOut,WristIn))
    HandVec = normalize(np.subtract(HandOut,WristOut))

    ArmToElbowVec = normalize(np.subtract(MidElbow,LeftArm))

    HandUpVec = normalize(np.cross(HandVec,WristVec))
    FrontVec = np.cross(ArmToElbowVec,HandUpVec)
    UpVec = normalize(np.cross(FrontVec,ArmToElbowVec))

    RTotal = QRotationFromReference(UpVec,FrontVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal("LeftArm", markerset, None,e)

def _LeftForeArm_rule(joint,markers,markerset):
    LeftForeArm = JointPos("LeftForeArm",markerset)
    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    HandOut = MarkerPos("LHandOut",markerset)
    WristVec = normalize(np.subtract(WristOut,WristIn))
    HandVec = normalize(np.subtract(HandOut,WristOut))
    MidWrist = np.add(WristIn,WristOut) * 0.5

    ElbowToWristVec = normalize(np.subtract(LeftForeArm,MidWrist))

    PalmVec = normalize(np.cross(HandVec,WristVec))
    FrontVec = np.cross(PalmVec,ElbowToWristVec)
    UpVec = np.cross(ElbowToWristVec, FrontVec)

    RTotal = QRotationFromReference(UpVec,FrontVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal("LeftForeArm", markerset, None,e)

def _LeftHand_rule(joint,markers,markerset):
    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    HandOut = MarkerPos("LHandOut",markerset)
    WristVec = normalize(np.subtract(WristOut,WristIn))
    HandVec = normalize(np.subtract(HandOut,WristOut))

    UpVec = normalize(np.cross(HandVec,WristVec))
    FrontVec = normalize(np.subtract(WristIn,WristOut))

    XOffsetVec = normalize(JointPosLocal("LeftHand_end",markerset))
    ROffset = QRotationBetweenVectors(XOffsetVec,np.array([-1.0,0.0,0.0]))

    R = QRotationFromReference(UpVec,FrontVec)
    RTotal = R * ROffset

    e = RTotal.as_euler("xyz")
    SetJointGlobal("LeftHand", markerset, None,e)

def _RightShoulder_rule(joint,markers,markerset):
    RArm = MarkerPos("RArm",markerset)
    RElbowOut = MarkerPos("RElbowOut",markerset)
    SpineTop = MarkerPos("SpineTop",markerset)
    RightShoulder = JointPos("RightShoulder",markerset)
    Spine2 = JointPos("Spine2",markerset)
    Neck = JointPos("Neck",markerset)
    MidElbow = np.add(RArm, RElbowOut) * 0.5
    ShoulderToElbowVec = normalize(np.subtract(MidElbow,RightShoulder))

    UpVec = normalize(np.subtract(Neck,Spine2))
    FrontVec = np.cross(UpVec,ShoulderToElbowVec)

    RTotal = QRotationFromReference(UpVec,FrontVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal("RightShoulder", markerset, None,e)

def _RightArm_rule(joint,markers,markerset):
    RArm = MarkerPos("RArm",markerset)
    RElbowOut = MarkerPos("RElbowOut",markerset)
    SpineTop = MarkerPos("SpineTop",markerset)
    RightArm = JointPos("RightArm",markerset)
    MidElbow = np.add(RArm, RElbowOut) * 0.5
    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    HandOut = MarkerPos("RHandOut",markerset)
    WristVec = normalize(np.subtract(WristOut,WristIn))
    HandVec = normalize(np.subtract(HandOut,WristOut))

    ArmToElbowVec = normalize(np.subtract(RightArm,MidElbow))

    HandUpVec = normalize(np.cross(HandVec,WristVec))
    FrontVec = np.cross(HandUpVec,ArmToElbowVec)
    UpVec = normalize(np.cross(FrontVec,ArmToElbowVec))

    RTotal = QRotationFromReference(UpVec,FrontVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal("RightArm", markerset, None,e)

def _RightForeArm_rule(joint,markers,markerset):
    RightForeArm = JointPos("RightForeArm",markerset)
    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    HandOut = MarkerPos("RHandOut",markerset)
    WristVec = normalize(np.subtract(WristOut,WristIn))
    HandVec = normalize(np.subtract(HandOut,WristOut))
    MidWrist = np.add(WristIn,WristOut) * 0.5

    ElbowToWristVec = normalize(np.subtract(MidWrist,RightForeArm))

    PalmVec = normalize(np.cross(WristVec,HandVec))
    FrontVec = np.cross(PalmVec,ElbowToWristVec)
    UpVec = np.cross(ElbowToWristVec, FrontVec)

    RTotal = QRotationFromReference(UpVec,FrontVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal("RightForeArm", markerset, None,e)

def _RightHand_rule(joint,markers,markerset):
    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    HandOut = MarkerPos("RHandOut",markerset)
    WristVec = normalize(np.subtract(WristOut,WristIn))
    HandVec = normalize(np.subtract(HandOut,WristOut))

    UpVec = normalize(np.cross(WristVec,HandVec))
    FrontVec = normalize(np.subtract(WristIn,WristOut))

    XOffsetVec = normalize(JointPosLocal("RightHand_end",markerset))
    ROffset = QRotationBetweenVectors(XOffsetVec,np.array([1.0,0.0,0.0]))
    #eOffset = ROffset.as_euler("xyz", degrees = True)
    #print(f"Right Hand offset is {eOffset}")

    R = QRotationFromReference(UpVec,FrontVec)
    RTotal = R * ROffset

    e = RTotal.as_euler("xyz")
    SetJointGlobal("RightHand", markerset, None,e)

def _Neck_rule(joint,markers,markerset):
    HeadTop = MarkerPos("HeadTop",markerset)
    HeadFront = MarkerPos("HeadFront",markerset)
    SpineTop = MarkerPos("SpineTop",markerset)
    TopToFrontVec = normalize(np.subtract(HeadFront,HeadTop))

    UpVec = normalize(np.subtract(HeadTop,SpineTop))
    FrontVec = TopToFrontVec

    RTotal = QRotationFromReference(UpVec,FrontVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal("Neck", markerset, None,e)

def _Head_rule(joint,markers,markerset):
    HeadTop = MarkerPos("HeadTop",markerset)
    HeadFront = MarkerPos("HeadFront",markerset)
    HeadR = MarkerPos("HeadR",markerset)
    HeadL = MarkerPos("HeadL",markerset)
    MidHead = np.add(HeadR,HeadL)*.5
    Head = JointPos("Head",markerset)

    TopToFrontVec = normalize(np.subtract(HeadFront,HeadTop))
    TopToMidVec = np.subtract(MidHead,HeadTop)
    d = np.dot(TopToFrontVec,TopToMidVec)
    UpGoal = np.add(HeadTop,TopToFrontVec * d)

    UpVec = normalize(np.subtract(UpGoal,Head))
    FrontVec = TopToFrontVec

    RTotal = QRotationFromReference(UpVec,FrontVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal("Head", markerset, None,e)

def _LeftUpLeg_rule(joint,markers,markerset):
    LAnkleOut = MarkerPos("LAnkleOut",markerset)
    LHeelBack = MarkerPos("LHeelBack",markerset)
    LToeTip = MarkerPos("LToeTip",markerset)
    HeelToeVec = normalize(np.subtract(LToeTip,LHeelBack))
    HeelAnkleVec = np.subtract(LAnkleOut,LHeelBack)
    d = np.dot(HeelToeVec,HeelAnkleVec)
    UpGoal = np.add(LHeelBack, HeelToeVec * d)
    LeftUpLeg = JointPos("LeftUpLeg",markerset)
    UpVec = normalize(np.subtract(LeftUpLeg,UpGoal))
    FrontVec = HeelToeVec

    RTotal = QRotationFromReference(UpVec,FrontVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal("LeftUpLeg", markerset, None,e)

def _LeftLeg_rule(joint,markers,markerset):
    SetJointLocal("LeftLeg",markerset,None,np.array([0.0,0.0,0.0]))

def _LeftFoot_rule(joint,markers,markerset):
    SetJointLocal("LeftFoot",markerset,None,np.array([0.0,0.0,0.0]))

def _LeftToeBase_rule(joint,markers,markerset):
    SetJointLocal("LeftToeBase",markerset,None,np.array([0.0,0.0,0.0]))

def _RightUpLeg_rule(joint,markers,markerset):
    RAnkleOut = MarkerPos("RAnkleOut",markerset)
    RHeelBack = MarkerPos("RHeelBack",markerset)
    RToeTip = MarkerPos("RToeTip",markerset)
    HeelToeVec = normalize(np.subtract(RToeTip,RHeelBack))
    HeelAnkleVec = np.subtract(RAnkleOut,RHeelBack)
    d = np.dot(HeelToeVec,HeelAnkleVec)
    UpGoal = np.add(RHeelBack, HeelToeVec * d)
    RightUpLeg = JointPos("RightUpLeg",markerset)
    UpVec = normalize(np.subtract(RightUpLeg,UpGoal))
    FrontVec = HeelToeVec

    RTotal = QRotationFromReference(UpVec,FrontVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal("RightUpLeg", markerset, None,e)


def _RightLeg_rule(joint,markers,markerset):
    SetJointLocal("RightLeg",markerset,None,np.array([0.0,0.0,0.0]))

def _RightFoot_rule(joint,markers,markerset):
    SetJointLocal("RightFoot",markerset,None,np.array([0.0,0.0,0.0]))

def _RightToeBase_rule(joint,markers,markerset):
    SetJointLocal("RightToeBase",markerset,None,np.array([0.0,0.0,0.0]))



AnimRules = {
"Hips":(_Hips_rule,["WaistRFront","WaistLBack","WaistLFront","WaistRBack"]),
"Spine":(_Spine_rule,["WaistLBack","WaistRBack","BackL","BackR"]),
"Spine1":(_Spine1_rule,["BackL","BackR","Chest"]),
"Spine2":(_Spine2_rule,["Chest","SpineTop"]),
"LeftShoulder":(_LeftShoulder_rule,["LShoulderTop","LShoulderBack"]),
"LeftArm":(_LeftArm_rule,["LElbowOut","LArm"]),
"LeftForeArm":(_LeftForeArm_rule,["LElbowOut","LWristOut","LWristIn"]),
"LeftHand":(_LeftHand_rule,["LWristOut","LWristIn","LHandOut","LeftHandExtra"]),
"RightShoulder":(_RightShoulder_rule,["RShoulderTop","RShoulderBack"]),
"RightArm":(_RightArm_rule,["RElbowOut","RArm"]),
"RightForeArm":(_RightForeArm_rule,["RElbowOut","RWristOut","RWristIn"]),
"RightHand":(_RightHand_rule,["RWristOut","RWristIn","RHandOut","RightHandExtra"]),
"Neck":(_Neck_rule,["SpineTop","HeadR","HeadL"]),
"Head":(_Head_rule,["HeadR","HeadL","HeadFront","HeadTop"]),
"LeftUpLeg":(_LeftUpLeg_rule,["LThigh","LKneeOut"]),
"LeftLeg":(_LeftLeg_rule,["LKneeOut","LShin","LAnkleOut"]),
"LeftFoot":(_LeftFoot_rule,["LHeelBack","LForefootIn","LForefootOut"]),
"LeftToeBase":(_LeftToeBase_rule,["LForefootIn","LForefootOut","LToeTip"]),
"RightUpLeg":(_RightUpLeg_rule,["RThigh","RKneeOut"]),
"RightLeg":(_RightLeg_rule,["RKneeOut","RShin","RAnkleOut"]),
"RightFoot":(_RightFoot_rule,["RHeelBack","RForefootIn","RForefootOut"]),
"RightToeBase":(_RightToeBase_rule,["RForefootIn","RForefootOut","RToeTip"])
}

def VerifyUnitScale(node):
    tolerance = 0.0001
    nodeName = str(node)
    s = [0.0,0.0,0.0]
    s[0] = cmds.getAttr("%s.scaleX" % nodeName)
    s[1] = cmds.getAttr("%s.scaleY" % nodeName)
    s[2] = cmds.getAttr("%s.scaleZ" % nodeName)
    if abs(s[0]-1) > tolerance or abs(s[1]-1) > tolerance or abs(s[2]-1) > tolerance:
        return False    
    return True
def VerifyJointChildren(child):
    if not VerifyUnitScale(child):
        print(f"Node {child} has a scale factor applied.")
        return False
    children = cmds.listRelatives(child,c=True)
    if children:
        for c in children:
            if not VerifyJointChildren(c):
                return False
    return True

def SanityCheckSkeletonScale(rootJoint):
    parents = cmds.listRelatives(rootJoint,parent=True)
    if parents:
        parent = parents[0]
        if not VerifyUnitScale(parent):
            print(f"Node {parent} has a scale factor applied.")
            return False
    children = cmds.listRelatives(rootJoint,c=True)
    for child in children:
        if not VerifyJointChildren(child):
            return False
    return True

    
#
# Series of sanity checks to make sure the user picks one and only one
# root joint
#
# Also need to verify namespace construction
#
def SanityCheck():
    
    namespace = u""
    
    sel = cmds.ls(selection=True)
    if len(sel) == 0:
        #print "Nothing was selected"
        cmds.confirmDialog(title="No Root",message="Please select the root joint to fit",button=["OK"], defaultButton="OK")
        return False

    if len(sel) > 1:
        cmds.confirmDialog(title="Only One", message="Please select only one joint",button=["OK"], defaultButton="OK")
        return False
    # now the number of selections == 1, this is what we require
    rootJoint = sel[0]
    t = cmds.nodeType(str(rootJoint))
    if t != "joint":
        cmds.confirmDialog(title="Not a Joint", message="Please select a joint",button=["OK"], defaultButton="OK")
        return False
    namespace = str(rootJoint).rpartition(":")[0]
    namespace_base = cmds.namespaceInfo(namespace,baseName=True)
    if namespace_base != "ModelPose":
        cmds.confirmDialog(title="Namespace ModelPose Error", message="Selected joint must have ModelPose namespace",button=["OK"], defaultButton="OK")
        return False
    namespace_parent = cmds.namespaceInfo(namespace,parent=True)
    namespace_grandparent = cmds.namespaceInfo(namespace_parent,parent=True)
    if namespace_grandparent != ":":
        cmds.confirmDialog(title="Namespace Parent Name Error", message="Selected joint must have a parent namespace",button=["OK"], defaultButton="OK")
        return False
    #print "Markers Node is", namespace_parent+":Markers"
    m = cmds.ls(namespace_parent+":Markers")
    if len(m) == 0:
        cmds.confirmDialog(title="No Markers", message="Markers node was not found in same namespace",button=["OK"], defaultButton="OK")
        return False  
    
    markers = m[0]

    if not VerifyUnitScale(markers):
        print(f"non unit scale factor on markers node.")
        return False
    if not SanityCheckSkeletonScale(rootJoint):
        print(f"non unit scale factor on joint node.")
        return False

    print ("Found", markers, cmds.nodeType(markers))
    parents = cmds.listRelatives(markers,parent=True)

    return True

def ConcatenateMarkerAttachments(node) -> str:
    markersStr = ""
    bFirst = True
    nodeName = str(node)
    namespace = str(node).split(":")[0]
    #print(f"Looking for {namespace}:Markers")
    markersNode = cmds.ls(f"{namespace}:Markers")
    markers = cmds.listRelatives(markersNode,c=True)
    for m in markers:
        markerName = str(m).split(":")[-1]
        a = f"{nodeName}.{markerName}"
        if cmds.attributeQuery(markerName,node=nodeName, exists=True):
            if bFirst:
                markersStr = f"\"{markerName}\""
                bFirst = False
            else:
                markersStr += f",\"{markerName}\""
    return markersStr    

def IsLeaf(jointNode):
    children = cmds.listRelatives(jointNode,c=True)
    if children:
        return False
    return True

def PrintJointDict(node):
    """
    Programming helper function.  Traverse the hierarchy and print out dict entries for the joints.
    """
    markers = ConcatenateMarkerAttachments(node)
    nodeName = str(node).rpartition(":")[-1]
    print(f"\"{nodeName}\":(_{nodeName}_rule,[{markers}]),")
    children = cmds.listRelatives(node,c=True)
    if children:
        for c in children:
            if not IsLeaf(c):
                PrintJointDict(c)


def PrintJointRule(node):
    """
    Programming helper function.  Traverse the hierarchy and print out function stubs
    for each of the joints.
    """
    nodeName = str(node).rpartition(":")[-1]
    print(f"def _{nodeName}_rule(joint,markers):")
    print(f"\tpass\n")
    children = cmds.listRelatives(node,c=True)
    if children:
        for c in children:
            if not IsLeaf(c):
                PrintJointRule(c)

def _ApplyRules(joint,markerset):
    nodeName = str(joint).rpartition(":")[-1]
    (RuleFunc, Markers) = AnimRules[nodeName]
    if RuleFunc:
        RuleFunc(joint, Markers, markerset)
    children = cmds.listRelatives(joint,c=True)
    if children:
        for c in children:
            if not IsLeaf(c):
                _ApplyRules(c,markerset)

def _DoFitAnimationSkeleton():
    """
    Do the actual work of fitting the selected skeleton to the matching
    marker cloud.  Hardcoded to work with a particular skeleton,
    the QTM Animation skeleton in this case.
    """
    sel = cmds.ls(selection=True)
    rootJoint = sel[0]
    markerset = str(rootJoint).split(":")[0]
    #PrintJointDict(rootJoint)
    #PrintJointRule(rootJoint)
    _ApplyRules(rootJoint,markerset)


def FitSkeleton():
    bOK = SanityCheck()
    if bOK:
        _DoFitAnimationSkeleton()

#print(f"__name__ is {__name__}")
if __name__ == "__main__":
    FitSkeleton()
