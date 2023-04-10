"""
Fit the selected Metahuman skeleton to the QTM animation markerset cloud.
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

# Constants, global variables and pre-computed values
# 
# Assumes world up axis is Z
#
# FACING_VECTOR is the direction the markerset is facing.  Needs to
# be level (orthogonal to world up Z axis).  Is to be computed before calling
# the rules functions.
#
MARKER_SIZE = 1.0
WORLD_UP = np.array([0.0,0.0,1.0])
FACING_VECTOR = np.array([0.0,1.0,0.0])
RIGHT_FOOT = np.array([0.0,0.0,0.0])
LEFT_FOOT = np.array([0.0,0.0,0.0])


def normalize(n):
    l = np.linalg.norm(n)
    return n/l

def OrthogonalizeV2(v1,v2):
    """
    Return v2 made orthogonal to v1
    """
    c = np.cross(v1,v2)
    o = normalize(np.cross(c,v1))
    return o

def closest_line_seg_line_seg(p1, p2, p3, p4):
    """
    Return the line segment whose endpoints are the closest
    points on each line closest to each other
    """
    P1 = p1
    P2 = p3
    V1 = p2 - p1
    V2 = p4 - p3
    V21 = P2 - P1

    v22 = np.dot(V2, V2)
    v11 = np.dot(V1, V1)
    v21 = np.dot(V2, V1)
    v21_1 = np.dot(V21, V1)
    v21_2 = np.dot(V21, V2)
    denom = v21 * v21 - v22 * v11

    if np.isclose(denom, 0.):
        s = 0.
        t = (v11 * s - v21_1) / v21
    else:
        s = (v21_2 * v21 - v22 * v21_1) / denom
        t = (-v21_1 * v21 + v11 * v21_2) / denom

    s = max(min(s, 1.), 0.)
    t = max(min(t, 1.), 0.)

    p_a = P1 + s * V1
    p_b = P2 + t * V2

    return p_a, p_b

def MarkerPos(markername,markerset):
    """
    Local marker position, but since its parent hasn't moved
    it's like a global position.
    """
    fullname = f"{markerset}:{markername}"
    node = cmds.ls(fullname)
    retval = np.array([0.0,0.0,0.0])
    if node is None:
        print(f"Could not find marker position for {fullname}")
        return retval
    retval[0] = cmds.getAttr(f"{markerset}:{markername}.translateX")
    retval[1] = cmds.getAttr(f"{markerset}:{markername}.translateY")
    retval[2] = cmds.getAttr(f"{markerset}:{markername}.translateZ")
    return retval

def JointPos(jointname, markerset):
    """
    Global joint position
    """
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
    """
    Global joint orientation
    """
    fullname = f"{markerset}:ModelPose:{jointname}"
    world_rot = cmds.xform(fullname, q=True, rotation=True, ws=True)

    return world_rot

def JointRotLocal(jointname,markerset):
    fullname = f"{markerset}:ModelPose:{jointname}"
    e = np.array([0.0,0.0,0.0])
    e[0] =  cmds.getAttr(f"{markerset}:ModelPose:{jointname}.rotateX")
    e[1] =  cmds.getAttr(f"{markerset}:ModelPose:{jointname}.rotateY")
    e[2] =  cmds.getAttr(f"{markerset}:ModelPose:{jointname}.rotateZ")
    R = qscipy.QRotation.from_euler("xyz",e)
    return R

def QRotationFromReference(XVec, YVec):
    """ 
    Return the global rotation from the given reference frame described by an up vector
    and a front vector.  These two do not have to be perfectly orthogonal nor unit vectors.
    The up vector maps to X, the front vector to Y.

    The difference in this function relative the QFitAnimation file is how this routine fills
    the rotation matrix because of the differing "up" vectors.
    """
    X = normalize(XVec)
    Z = normalize(np.cross(X, YVec))
    Y = normalize(np.cross(Z,X))
    R = qscipy.QRotation.from_matrix([X,Y,Z])
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

def QFitBooleanAttribute(joint, attr, default : bool = False) -> bool:
    """
    Retrives the given attribute, if it doesn't exist then
    create it for the node and return a default value
    """
    retval = default
    fullAttr = f"QFit_{attr}"
    jointAttr = f"{str(joint)}.{fullAttr}"
    if cmds.attributeQuery(fullAttr,node=str(joint), exists=True):
        retval = cmds.getAttr(jointAttr)
    else:
        cmds.addAttr(str(joint),ln=fullAttr,at="bool")
        cmds.setAttr(jointAttr,retval)
    return retval

def QFitFloatAttribute(joint, attr, default : float = 0.0) -> float:
    """
    Retrives the given attribute, if it doesn't exist then
    create it for the node and return a default value
    """
    retval = default
    fullAttr = f"QFit_{attr}"
    jointAttr = f"{str(joint)}.{fullAttr}"
    if cmds.attributeQuery(fullAttr,node=str(joint), exists=True):
        retval = cmds.getAttr(jointAttr)
    else:
        cmds.addAttr(str(joint),ln=fullAttr,defaultValue = default)
        cmds.setAttr(jointAttr,retval)
    return retval

#
# The aim of each rule is to find the X (up) axis and the
# Y (front) axis.  From this a global rotation value is
# computed and then set in the node.
# 
# Note that the "front" Y axis is actually facing the rear for
# the left side of the body.
#
# Likewise, the "up" X vector is actually -X for the right side
# of the body.
#
def _ZERO_rule(joint,markerset):
    """
    Default rule.  Zero out the rotations.
    """
    my_name = str(joint).split(':')[-1]
    e = np.array([0.0,0.0,0.0])
    SetJointLocal(my_name, markerset, None,e)

def _NOOP_rule(joint,markerset):
    pass

def _pelvis_rule(joint,markerset):
    """
    Rule for fitting the position and orientation of the pelvis.
    Also, as a side effect, pre-computes some global values to be
    used by other rules.  Assumes this is the first rule to be 
    invoked.
    """
    my_name = str(joint).split(':')[-1]
    LShoulderTop = MarkerPos("LShoulderTop",markerset)
    RShoulderTop = MarkerPos("RShoulderTop",markerset)
    MidShoulder = np.add(LShoulderTop,RShoulderTop) * 0.5
    
    WRB = MarkerPos("WaistRBack",markerset)
    WLB = MarkerPos("WaistLBack",markerset)
    CenterBack = np.add(WRB,WLB) * 0.5
    WRF = MarkerPos("WaistRFront",markerset)
    WLF = MarkerPos("WaistLFront",markerset)
    forwardOffset =  QFitFloatAttribute(joint,"ForwardOffset", 10.0)
    verticalOffset =  QFitFloatAttribute(joint,"VerticalOffset", 5.0)

    CenterFront = np.add(WRF,WLF) * 0.5
    CenterVec = normalize(np.subtract(CenterFront, CenterBack))
    HipsEnd = np.add(CenterBack,CenterVec * forwardOffset)

    BackL = MarkerPos("BackL",markerset)
    BackR = MarkerPos("BackR",markerset)
    MidBack = np.add(BackL,BackR)*0.5
    DownVec = np.array([0.0,0.0,-1.0])
    HipsStart = np.add(HipsEnd, DownVec * verticalOffset)
    
    HipsUp = normalize(np.subtract(MidShoulder,HipsStart))
    HipsForward = OrthogonalizeV2(HipsUp,CenterVec) * -1

    #RTotal = RotationFromReference(HipsUp,HipsForward)
    QRTotal = QRotationFromReference(HipsUp,HipsForward)

    qe = QRTotal.as_euler("xyz")

    SetJointGlobal(my_name, markerset, HipsStart,qe)
    
def _spine_01_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    e = np.array([0.0,0.0,-10.95])
    SetJointLocal(my_name, markerset, None,e)

def _spine_02_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    e = np.array([0.0,0.0,7.321])
    SetJointLocal(my_name, markerset, None,e)

def _spine_03_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    LShoulderTop = MarkerPos("LShoulderTop",markerset)
    RShoulderTop = MarkerPos("RShoulderTop",markerset)
    MidShoulder = np.add(LShoulderTop,RShoulderTop) * 0.5
    SpineTop = MarkerPos("SpineTop",markerset)

    XVec = normalize(np.subtract(MidShoulder,my_joint))
    YVec = normalize(np.subtract(SpineTop,MidShoulder))
    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")   
    SetJointGlobal(my_name, markerset, None,e)

def _spine_04_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    LShoulderTop = MarkerPos("LShoulderTop",markerset)
    RShoulderTop = MarkerPos("RShoulderTop",markerset)
    MidShoulder = np.add(LShoulderTop,RShoulderTop) * 0.5
    SpineTop = MarkerPos("SpineTop",markerset)

    XVec = normalize(np.subtract(MidShoulder,my_joint))
    YVec = normalize(np.subtract(SpineTop,MidShoulder))
    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")   
    SetJointGlobal(my_name, markerset, None,e)

def _spine_05_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    e = np.array([0.0,0.0,-1.533])
    SetJointLocal(my_name, markerset, None,e)

def _clavicle_l_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    ShoulderTop = MarkerPos("LShoulderTop", markerset)
    ShoulderFloor = np.array([ShoulderTop[0],ShoulderTop[1],0.0])
    LShoulderBack = MarkerPos("LShoulderBack", markerset)
    RShoulderBack = MarkerPos("RShoulderBack", markerset)
    Chest = MarkerPos("Chest", markerset)
    ElbowOut = MarkerPos("LElbowOut", markerset)
    MidShoulderBack = np.add(LShoulderBack,RShoulderBack) * 0.5
    ForwardVec = normalize(np.subtract(Chest,MidShoulderBack))

    #p1,p2 = closest_line_seg_line_seg(ShoulderTop,ShoulderFloor,LShoulderBack, np.add(LShoulderBack,ForwardVec * 20.0))
    p1,p2 = closest_line_seg_line_seg(ShoulderTop,ShoulderFloor,my_joint, ElbowOut)

    XVec = normalize(np.subtract(p1,my_joint))
    YVec = ForwardVec * -1.0

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _upperarm_l_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    ElbowOut = MarkerPos("LElbowOut",markerset)
    ElbowFloor = np.array([ElbowOut[0],ElbowOut[1],0.0])

    Arm = JointPos(my_name,markerset)
    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    WristMid = np.add(WristIn, WristOut)* 0.5
    WristVec = normalize(np.subtract(WristOut,WristIn))
    if QFitBooleanAttribute(joint,"StraightArm", False):
        YVec = FACING_VECTOR * -1.0
        XVec = normalize(np.subtract(WristMid,my_joint))
    else:
        p1,p2 = closest_line_seg_line_seg(ElbowOut,ElbowFloor,Arm, WristMid)
        ArmToElbowVec = normalize(np.subtract(p1,Arm))
        YVec = WristVec
        XVec = ArmToElbowVec

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _lowerarm_l_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    WristVec = normalize(np.subtract(WristOut,WristIn))
    MidWrist = np.add(WristIn,WristOut) * 0.5

    if QFitBooleanAttribute(joint,"StraightArm", False):
        YVec = FACING_VECTOR * -1.0
    else:
        YVec = WristVec
    XVec = normalize(np.subtract(MidWrist, my_joint))

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)


def _hand_l_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    HandOut = MarkerPos("LHandOut",markerset)
    WristVec = normalize(np.subtract(WristOut,WristIn))
    if QFitBooleanAttribute(joint,"PalmDown", False):
        YVec = WORLD_UP * -1.0
        XVec = normalize(np.cross(FACING_VECTOR,YVec))
    else:
        if cmds.objExists(f"{markerset}:LHandIn"):
            HandIn = MarkerPos("LHandIn",markerset)
            HandInRatio =  max(min(QFitFloatAttribute(joint,"HandInRatio", 0.5),1.0),0.0)
            HandMid = np.add(HandIn * HandInRatio, HandOut * (1.0 - HandInRatio))
            # HandMid = np.add(HandIn, HandOut) * 0.5
            HandMid[2] -= MARKER_SIZE
            XVec = normalize(np.subtract(HandMid,my_joint))
        else:
            HandOut[2] -= MARKER_SIZE
            XVec = normalize(np.subtract(HandOut,WristOut))

        YVec = normalize(np.cross(WristVec,XVec))

    RTotal = QRotationFromReference(XVec,YVec)

    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _clavicle_r_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    ShoulderTop = MarkerPos("RShoulderTop", markerset)
    ShoulderFloor = np.array([ShoulderTop[0],ShoulderTop[1],0.0])
    LShoulderBack = MarkerPos("LShoulderBack", markerset)
    RShoulderBack = MarkerPos("RShoulderBack", markerset)
    SpineTop = MarkerPos("SpineTop", markerset)
    ElbowOut = MarkerPos("RElbowOut", markerset)
    MidShoulderBack = np.add(LShoulderBack,RShoulderBack) * 0.5
    ForwardVec = normalize(np.subtract(MidShoulderBack,SpineTop))

    #p1,p2 = closest_line_seg_line_seg(ShoulderTop,ShoulderFloor,RShoulderBack, np.add(RShoulderBack,ForwardVec))
    p1,p2 = closest_line_seg_line_seg(ShoulderTop,ShoulderFloor,my_joint, ElbowOut)

    XVec = normalize(np.subtract(my_joint,p1))
    YVec = ForwardVec

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _upperarm_r_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    ElbowOut = MarkerPos("RElbowOut",markerset)
    ElbowFloor = np.array([ElbowOut[0],ElbowOut[1],0.0])

    Arm = JointPos(my_name,markerset)
    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    WristMid = np.add(WristIn, WristOut)* 0.5
    WristVec = normalize(np.subtract(WristOut,WristIn))

    if QFitBooleanAttribute(joint,"StraightArm", False):
        YVec = FACING_VECTOR
        XVec = normalize(np.subtract(my_joint,WristMid))
    else:
        p1,p2 = closest_line_seg_line_seg(ElbowOut,ElbowFloor,Arm, WristMid)
        ArmToElbowVec = normalize(np.subtract(p1,Arm))
        YVec = WristVec * -1.0
        XVec = ArmToElbowVec * -1.0

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _lowerarm_r_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    WristVec = normalize(np.subtract(WristOut,WristIn))
    MidWrist = np.add(WristIn,WristOut) * 0.5

    if QFitBooleanAttribute(joint,"StraightArm", False):
        YVec = FACING_VECTOR
    else:
        YVec = WristVec * -1.0
    
    XVec = normalize(np.subtract(my_joint,MidWrist))

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)


def _hand_r_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    HandOut = MarkerPos("RHandOut",markerset)
    WristVec = normalize(np.subtract(WristOut,WristIn))
    if QFitBooleanAttribute(joint,"PalmDown", False):
        YVec = WORLD_UP
        XVec = normalize(np.cross(YVec,FACING_VECTOR))
    else:
        if cmds.objExists(f"{markerset}:RHandIn"):
            HandIn = MarkerPos("RHandIn",markerset)
            HandInRatio =  max(min(QFitFloatAttribute(joint,"HandInRatio", 0.5),1.0),0.0)
            HandMid = np.add(HandIn * HandInRatio, HandOut * (1.0 - HandInRatio))
            # HandMid = np.add(HandIn, HandOut) * 0.5
            HandMid[2] -= MARKER_SIZE
            XVec = normalize(np.subtract(HandMid,my_joint)) * -1.0
        else:
            HandOut[2] -= MARKER_SIZE
            XVec = normalize(np.subtract(HandOut,WristOut)) * -1.0

        YVec = normalize(np.cross(WristVec,XVec)) * -1.0

    RTotal = QRotationFromReference(XVec,YVec)

    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _neck_01_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    HeadTop = MarkerPos("HeadTop",markerset)
    HeadFront = MarkerPos("HeadFront",markerset)
    HeadMid = np.add(HeadTop * 0.5, HeadFront * 0.5)

    XVec = normalize(np.subtract(HeadMid,my_joint))
    YVec = normalize(np.subtract(HeadTop,HeadFront))

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _neck_02_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    e = np.array([0.0,0.0,0.0])
    SetJointLocal(my_name, markerset, None,e)

def _head_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    e = np.array([0.0,0.0,0.0])
    SetJointLocal(my_name, markerset, None,e)

def _thigh_l_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    KneeOut = MarkerPos("LKneeOut",markerset)

    HeelBack = MarkerPos("LHeelBack",markerset)
    ToeTip = MarkerPos("LToeTip",markerset)

    if QFitBooleanAttribute(joint,"StraightLeg", False):
        AnkleOut = MarkerPos("LAnkleOut",markerset)
        MidHeel = np.add(AnkleOut * 0.5, HeelBack * 0.5)
        p1,p2 = closest_line_seg_line_seg(HeelBack,ToeTip,my_joint, MidHeel)

        XVec = normalize(np.subtract(my_joint,p1))
        YVec = normalize(np.subtract(HeelBack,ToeTip))
    else:
        p1,p2 = closest_line_seg_line_seg(HeelBack,ToeTip,my_joint, KneeOut)
        XVec = normalize(np.subtract(my_joint,p1))
        YVec = normalize(np.subtract(HeelBack,ToeTip))

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _calf_l_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    AnkleOut = MarkerPos("LAnkleOut",markerset)

    HeelBack = MarkerPos("LHeelBack",markerset)
    ToeTip = MarkerPos("LToeTip",markerset)
    MidHeel = np.add(AnkleOut * 0.5, HeelBack * 0.5)

    p1,p2 = closest_line_seg_line_seg(HeelBack,ToeTip,my_joint, MidHeel)

    XVec = normalize(np.subtract(my_joint,p1))
    YVec = normalize(np.subtract(HeelBack,ToeTip))

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _foot_l_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    if QFitBooleanAttribute(joint,"KeepFlat", False):
        SetJointGlobal(my_name,markerset,None,LEFT_FOOT)
        return

    HeelBack = MarkerPos("LHeelBack",markerset)
    ToeTip = MarkerPos("LToeTip",markerset)
    
    ForefootIn = MarkerPos("LForefootIn",markerset)
    ForefootOut = MarkerPos("LForefootOut",markerset)
    ForefootMid = np.add(ForefootIn, ForefootOut) * 0.5
    XVec = normalize(np.subtract(my_joint,ForefootMid))
    YVec = normalize(np.subtract(HeelBack,ToeTip))
    R = QRotationFromReference(XVec,YVec)
    ball_joint = JointPos("ball_l",markerset)

    SegVec = normalize(np.subtract(ball_joint, my_joint))
    ROrig = qscipy.QRotation.from_euler("xyz", JointRot(my_name,markerset))
    axis = np.cross(SegVec, ROrig.M[0])
    theta = math.degrees(np.arcsin( np.linalg.norm(axis)))

    ROffset = qscipy.QRotation.from_z_rot(-theta)

    RTotal = ROffset * R
    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _ball_l_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    e = np.array([0.0,0.0,-90.0])
    SetJointLocal(my_name, markerset, None,e)

def _thigh_r_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    KneeOut = MarkerPos("RKneeOut",markerset)

    HeelBack = MarkerPos("RHeelBack",markerset)
    ToeTip = MarkerPos("RToeTip",markerset)

    if QFitBooleanAttribute(joint,"StraightLeg", False):
        AnkleOut = MarkerPos("RAnkleOut",markerset)
        MidHeel = np.add(AnkleOut * 0.5, HeelBack * 0.5)
        p1,p2 = closest_line_seg_line_seg(HeelBack,ToeTip,my_joint, MidHeel)

        XVec = normalize(np.subtract(p1,my_joint))
        YVec = normalize(np.subtract(ToeTip,HeelBack))
    else:
        p1,p2 = closest_line_seg_line_seg(HeelBack,ToeTip,my_joint, KneeOut)
        XVec = normalize(np.subtract(p1,my_joint))
        YVec = normalize(np.subtract(ToeTip,HeelBack))

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _calf_r_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    AnkleOut = MarkerPos("RAnkleOut",markerset)

    HeelBack = MarkerPos("RHeelBack",markerset)
    ToeTip = MarkerPos("RToeTip",markerset)
    MidHeel = np.add(AnkleOut * 0.5, HeelBack * 0.5)

    p1,p2 = closest_line_seg_line_seg(HeelBack,ToeTip,my_joint, MidHeel)

    XVec = normalize(np.subtract(p1,my_joint))
    YVec = normalize(np.subtract(ToeTip,HeelBack))

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _foot_r_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    if QFitBooleanAttribute(joint,"KeepFlat", False):
        SetJointGlobal(my_name,markerset,None,RIGHT_FOOT)
        return

    HeelBack = MarkerPos("RHeelBack",markerset)
    ToeTip = MarkerPos("RToeTip",markerset)
    
    ForefootIn = MarkerPos("RForefootIn",markerset)
    ForefootOut = MarkerPos("RForefootOut",markerset)
    ForefootMid = np.add(ForefootIn, ForefootOut) * 0.5
    XVec = normalize(np.subtract(ForefootMid, my_joint))
    YVec = normalize(np.subtract(ToeTip,HeelBack))
    R = QRotationFromReference(XVec,YVec)
    ball_joint = JointPos("ball_r",markerset)

    SegVec = normalize(np.subtract(ball_joint, my_joint))
    ROrig = qscipy.QRotation.from_euler("xyz", JointRot(my_name,markerset))
    axis = np.cross(SegVec, ROrig.M[0])
    theta = math.degrees(np.arcsin( np.linalg.norm(axis)))

    ROffset = qscipy.QRotation.from_z_rot(-theta)

    RTotal = ROffset * R
    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _ball_r_rule(joint,markerset):
    my_name = str(joint).split(':')[-1]
    e = np.array([0.0,0.0,-90.0])
    SetJointLocal(my_name, markerset, None,e)

def _pinky_01_r_rule(joint,markerset):
    if not cmds.objExists(f"{markerset}:RPinkyTip"):
        return
    if not cmds.objExists(f"{markerset}:RHandIn"):
        return
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    PinkyTip = MarkerPos("RPinkyTip",markerset)
    PinkyTip[2] -= MARKER_SIZE
    XVec = normalize(np.subtract(my_joint,PinkyTip))

    HandIn  = MarkerPos("RHandIn",markerset)
    HandOut  = MarkerPos("RHandOut",markerset)
    WristOut  = MarkerPos("RWristOut",markerset)
    V1 = normalize(np.subtract(HandIn,HandOut))
    V2 = normalize(np.subtract(WristOut,HandOut))
    YVec = normalize(np.cross(V1,V2))

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")   
    SetJointGlobal(my_name, markerset, None,e)
def _index_01_r_rule(joint,markerset):
    if not cmds.objExists(f"{markerset}:RIndexTip"):
        return
    if not cmds.objExists(f"{markerset}:RHandIn"):
        return
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    IndexTip = MarkerPos("RIndexTip",markerset)
    IndexTip[2] -= MARKER_SIZE
    XVec = normalize(np.subtract(my_joint,IndexTip))

    HandIn  = MarkerPos("RHandIn",markerset)
    HandOut  = MarkerPos("RHandOut",markerset)
    WristOut  = MarkerPos("RWristOut",markerset)
    V1 = normalize(np.subtract(HandIn,HandOut))
    V2 = normalize(np.subtract(WristOut,HandOut))
    YVec = normalize(np.cross(V1,V2))

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")   
    SetJointGlobal(my_name, markerset, None,e)
def _ring_01_r_rule(joint,markerset):
    if not cmds.objExists(f"{markerset}:RPinkyTip"):
        return
    if not cmds.objExists(f"{markerset}:RIndexTip"):
        return
    if not cmds.objExists(f"{markerset}:RHandIn"):
        return
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    IndexTip = MarkerPos("RIndexTip",markerset)
    PinkyTip = MarkerPos("RPinkyTip",markerset)
    FingerTip = np.add(PinkyTip * 0.6666,IndexTip * 0.3333)
    FingerTip[2] -= MARKER_SIZE
    XVec = normalize(np.subtract(my_joint,FingerTip))

    HandIn  = MarkerPos("RHandIn",markerset)
    HandOut  = MarkerPos("RHandOut",markerset)
    WristOut  = MarkerPos("RWristOut",markerset)
    V1 = normalize(np.subtract(HandIn,HandOut))
    V2 = normalize(np.subtract(WristOut,HandOut))
    YVec = normalize(np.cross(V1,V2))

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")   
    SetJointGlobal(my_name, markerset, None,e)
def _middle_01_r_rule(joint,markerset):
    if not cmds.objExists(f"{markerset}:RPinkyTip"):
        return
    if not cmds.objExists(f"{markerset}:RIndexTip"):
        return
    if not cmds.objExists(f"{markerset}:RHandIn"):
        return
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    IndexTip = MarkerPos("RIndexTip",markerset)
    PinkyTip = MarkerPos("RPinkyTip",markerset)
    FingerTip = np.add(PinkyTip * 0.3333,IndexTip * 0.6666)
    FingerTip[2] -= MARKER_SIZE
    XVec = normalize(np.subtract(my_joint,FingerTip))

    HandIn  = MarkerPos("RHandIn",markerset)
    HandOut  = MarkerPos("RHandOut",markerset)
    WristOut  = MarkerPos("RWristOut",markerset)
    V1 = normalize(np.subtract(HandIn,HandOut))
    V2 = normalize(np.subtract(WristOut,HandOut))
    YVec = normalize(np.cross(V1,V2))

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")   
    SetJointGlobal(my_name, markerset, None,e)

def _thumb_01_r_rule(joint,markerset):
    if not cmds.objExists(f"{markerset}:RThumbTip"):
        return
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    ThumbTip = MarkerPos("RThumbTip",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    WristOut = MarkerPos("RWristOut",markerset)
    ThumbMid = np.add(WristIn * 0.5,ThumbTip * 0.5)
    XVec = normalize(np.subtract(my_joint,ThumbMid))

    YVec = normalize(np.subtract(WristIn,WristOut))

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")   
    SetJointGlobal(my_name, markerset, None,e)

def _thumb_02_r_rule(joint,markerset):
    if not cmds.objExists(f"{markerset}:RThumbTip"):
        return
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    ThumbTip = MarkerPos("RThumbTip",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    WristOut = MarkerPos("RWristOut",markerset)
    ThumbMid = np.add(WristIn * 0.5,ThumbTip * 0.5)
    XVec = normalize(np.subtract(my_joint,ThumbTip))

    YVec = normalize(np.subtract(WristIn,WristOut))

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")   
    SetJointGlobal(my_name, markerset, None,e)

def _pinky_01_l_rule(joint,markerset):
    if not cmds.objExists(f"{markerset}:LPinkyTip"):
        return
    if not cmds.objExists(f"{markerset}:LHandIn"):
        return
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    PinkyTip = MarkerPos("LPinkyTip",markerset)
    PinkyTip[2] -= MARKER_SIZE
    XVec = normalize(np.subtract(my_joint,PinkyTip)) * -1.0

    HandIn  = MarkerPos("LHandIn",markerset)
    HandOut  = MarkerPos("LHandOut",markerset)
    WristOut  = MarkerPos("LWristOut",markerset)
    V1 = normalize(np.subtract(HandIn,HandOut))
    V2 = normalize(np.subtract(WristOut,HandOut))
    YVec = normalize(np.cross(V1,V2)) * -1.0

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")   
    SetJointGlobal(my_name, markerset, None,e)

def _index_01_l_rule(joint,markerset):
    if not cmds.objExists(f"{markerset}:LIndexTip"):
        return
    if not cmds.objExists(f"{markerset}:LHandIn"):
        return
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    IndexTip = MarkerPos("LIndexTip",markerset)
    IndexTip[2] -= MARKER_SIZE
    XVec = normalize(np.subtract(my_joint,IndexTip)) * -1.0

    HandIn  = MarkerPos("LHandIn",markerset)
    HandOut  = MarkerPos("LHandOut",markerset)
    WristOut  = MarkerPos("LWristOut",markerset)
    V1 = normalize(np.subtract(HandIn,HandOut))
    V2 = normalize(np.subtract(WristOut,HandOut))
    YVec = normalize(np.cross(V1,V2)) * -1.0

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")   
    SetJointGlobal(my_name, markerset, None,e)
def _ring_01_l_rule(joint,markerset):
    if not cmds.objExists(f"{markerset}:LPinkyTip"):
        return
    if not cmds.objExists(f"{markerset}:LIndexTip"):
        return
    if not cmds.objExists(f"{markerset}:LHandIn"):
        return
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    IndexTip = MarkerPos("LIndexTip",markerset)
    PinkyTip = MarkerPos("LPinkyTip",markerset)
    FingerTip = np.add(PinkyTip * 0.6666,IndexTip * 0.3333)
    FingerTip[2] -= MARKER_SIZE
    XVec = normalize(np.subtract(my_joint,FingerTip)) * -1.0

    HandIn  = MarkerPos("LHandIn",markerset)
    HandOut  = MarkerPos("LHandOut",markerset)
    WristOut  = MarkerPos("LWristOut",markerset)
    V1 = normalize(np.subtract(HandIn,HandOut))
    V2 = normalize(np.subtract(WristOut,HandOut))
    YVec = normalize(np.cross(V1,V2)) * -1.0

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")   
    SetJointGlobal(my_name, markerset, None,e)
def _middle_01_l_rule(joint,markerset):
    if not cmds.objExists(f"{markerset}:LPinkyTip"):
        return
    if not cmds.objExists(f"{markerset}:LIndexTip"):
        return
    if not cmds.objExists(f"{markerset}:LHandIn"):
        return
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    IndexTip = MarkerPos("LIndexTip",markerset)
    PinkyTip = MarkerPos("LPinkyTip",markerset)
    FingerTip = np.add(PinkyTip * 0.3333,IndexTip * 0.6666)
    FingerTip[2] -= MARKER_SIZE
    XVec = normalize(np.subtract(my_joint,FingerTip)) * -1.0

    HandIn  = MarkerPos("LHandIn",markerset)
    HandOut  = MarkerPos("LHandOut",markerset)
    WristOut  = MarkerPos("LWristOut",markerset)
    V1 = normalize(np.subtract(HandIn,HandOut))
    V2 = normalize(np.subtract(WristOut,HandOut))
    YVec = normalize(np.cross(V1,V2)) * -1.0

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")   
    SetJointGlobal(my_name, markerset, None,e)

def _thumb_01_l_rule(joint,markerset):
    if not cmds.objExists(f"{markerset}:LThumbTip"):
        return
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    ThumbTip = MarkerPos("LThumbTip",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    WristOut = MarkerPos("LWristOut",markerset)
    ThumbMid = np.add(WristIn * 0.5,ThumbTip * 0.5)
    XVec = normalize(np.subtract(my_joint,ThumbMid)) * -1.0

    YVec = normalize(np.subtract(WristIn,WristOut)) * -1.0

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")   
    SetJointGlobal(my_name, markerset, None,e)

def _thumb_02_l_rule(joint,markerset):
    if not cmds.objExists(f"{markerset}:LThumbTip"):
        return
    my_name = str(joint).split(':')[-1]
    my_joint = JointPos(my_name,markerset)
    ThumbTip = MarkerPos("LThumbTip",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    WristOut = MarkerPos("LWristOut",markerset)
    XVec = normalize(np.subtract(my_joint,ThumbTip)) * -1.0

    YVec = normalize(np.subtract(WristIn,WristOut)) * -1.0

    RTotal = QRotationFromReference(XVec,YVec)
    e = RTotal.as_euler("xyz")   
    SetJointGlobal(my_name, markerset, None,e)

MetahumanRules = {
"pelvis":_pelvis_rule,
"spine_01":_spine_01_rule,
"spine_02":_spine_02_rule,
"spine_03":_spine_03_rule,
"spine_04":_spine_04_rule,
"spine_05":_spine_05_rule,
"clavicle_l":_clavicle_l_rule,
"upperarm_l":_upperarm_l_rule,
"lowerarm_l":_lowerarm_l_rule,
"hand_l":_hand_l_rule,
"clavicle_r":_clavicle_r_rule,
"upperarm_r":_upperarm_r_rule,
"lowerarm_r":_lowerarm_r_rule,
"hand_r":_hand_r_rule,
"neck_01":_neck_01_rule,
"neck_02":_neck_02_rule,
"head":_head_rule,
"thigh_l":_thigh_l_rule,
"calf_l":_calf_l_rule,
"foot_l":_foot_l_rule,
"ball_l":_NOOP_rule,
"thigh_r":_thigh_r_rule,
"calf_r":_calf_r_rule,
"foot_r":_foot_r_rule,
"ball_r":_NOOP_rule,
"pinky_01_r":_pinky_01_r_rule,
"pinky_02_r":_ZERO_rule,
"pinky_03_r":_ZERO_rule,
"index_01_r":_index_01_r_rule,
"index_02_r":_ZERO_rule,
"index_03_r":_ZERO_rule,
"ring_01_r":_ring_01_r_rule,
"ring_02_r":_ZERO_rule,
"ring_03_r":_ZERO_rule,
"middle_01_r":_middle_01_r_rule,
"middle_02_r":_ZERO_rule,
"middle_03_r":_ZERO_rule,
"thumb_01_r":_thumb_01_r_rule,
"thumb_02_r":_thumb_02_r_rule,
"thumb_03_r":_ZERO_rule,
"pinky_01_l":_pinky_01_l_rule,
"pinky_02_l":_ZERO_rule,
"pinky_03_l":_ZERO_rule,
"index_01_l":_index_01_l_rule,
"index_02_l":_ZERO_rule,
"index_03_l":_ZERO_rule,
"ring_01_l":_ring_01_l_rule,
"ring_02_l":_ZERO_rule,
"ring_03_l":_ZERO_rule,
"middle_01_l":_middle_01_l_rule,
"middle_02_l":_ZERO_rule,
"middle_03_l":_ZERO_rule,
"thumb_01_l":_thumb_01_l_rule,
"thumb_02_l":_thumb_02_l_rule,
"thumb_03_l":_ZERO_rule,}

AnimMarkers = [
    # "HeadL",
    "HeadTop",
    "HeadR",
    "HeadFront",
    "LShoulderTop",
    "LShoulderBack",
    "LArm",
    "LElbowOut",
    # "LElbowIn",
    # "LeftForeArm",
    "LWristOut",
    "LWristIn",
    "LHandOut",
    # "LHandIn",
    "RShoulderTop",
    "RShoulderBack",
    "RArm",
    # "RElbowIn",
    "RElbowOut",
    # "RightForeArm",
    "RWristOut",
    "RWristIn",
    "RHandOut",
    # "RHandIn",
    # "Clavicle",
    "Chest",
    "SpineTop",
    "BackL",
    "BackR",
    "WaistLFront",
    "WaistRFront",
    # "Hips_LMid",
    "WaistLBack",
    "WaistRBack",
    # "Hips_RMid",
    "LThigh",
    "LKneeOut",
    # "LKneeIn",
    "LShin",
    "LAnkleOut",
    "LHeelBack",
    "LForefootOut",
    "LToeTip",
    "LForefootIn",
    "RThigh",
    "RKneeOut",
    # "RKneeIn",
    "RShin",
    "RAnkleOut",
    "RHeelBack",
    "RForefootOut",
    "RToeTip",
    "RForefootIn"]
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
def AllMarkersPresent(markerset):
    for m in AnimMarkers:
        if not cmds.objExists(f"{markerset}:{m}"):
            print(f"Marker {m} is missing")
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
    
    # Only works when Z is the up axis, matching QTM.
    if cmds.upAxis( q=True, axis=True ) == 'y':
        cmds.confirmDialog(title="Wrong World Up Axis",message="Maya Up axis must be Z",button=["OK"], defaultButton="OK")
        return False       

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
    if not AllMarkersPresent(namespace_parent):
        cmds.confirmDialog(title="Missing Markers", message="Not all required markers are present",button=["OK"], defaultButton="OK")
        return False

    if not VerifyUnitScale(markers):
        print(f"non unit scale factor on markers node.")
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

def _PreCompute(markerset):

    WRB = MarkerPos("WaistRBack",markerset)
    WLB = MarkerPos("WaistLBack",markerset)
    CenterBack = np.add(WRB,WLB) * 0.5
    WRF = MarkerPos("WaistRFront",markerset)
    WLF = MarkerPos("WaistLFront",markerset)
    CenterFront = np.add(WRF,WLF) * 0.5
    CenterVec = normalize(np.subtract(CenterFront, CenterBack))

    # Set global facing for other rules to use
    global FACING_VECTOR
    FACING_VECTOR = OrthogonalizeV2(WORLD_UP,CenterVec)
    print(f"Set Facing to {FACING_VECTOR}")

    global RIGHT_FOOT
    RIGHT_FOOT = JointRot("foot_r", markerset)
    global LEFT_FOOT
    LEFT_FOOT = JointRot("foot_l", markerset)

def _ApplyRules(joint,markerset):
    nodeName = str(joint).rpartition(":")[-1]
    cmds.setAttr(f"{str(joint)}.segmentScaleCompensate", 0)
    if nodeName in MetahumanRules:
        RuleFunc = MetahumanRules[nodeName]
        if RuleFunc:
            RuleFunc(joint, markerset)

    children = cmds.listRelatives(joint,c=True)
    if children:
        for c in children:
            if not IsLeaf(c):
                _ApplyRules(c,markerset)

def _ConditionHierarchy(node):
    """
    Force joints to have no preferred angle and
    no joint orient values.
    """
    n = str(node)
    rot = cmds.xform(n, q=True, rotation=True, ws=True)
    cmds.setAttr("%s.jointOrientX" % n, 0)
    cmds.setAttr("%s.jointOrientY" % n, 0)
    cmds.setAttr("%s.jointOrientZ" % n, 0) 
       
    cmds.setAttr("%s.segmentScaleCompensate" %n, 0)
    
    cmds.xform(n, ws=True, ro=(rot[0],rot[1],rot[2]))

    cmds.setAttr("%s.preferredAngleX" % n, 0)
    cmds.setAttr("%s.preferredAngleY" % n, 0)
    cmds.setAttr("%s.preferredAngleZ" % n, 0)
    children = cmds.listRelatives(node,c=True)
    if children:
        for c in children:
            if not IsLeaf(c):
                _ConditionHierarchy(c)

def _DoFitMetahumanSkeleton():
    """
    Do the actual work of fitting the selected skeleton to the matching
    marker cloud.  Hardcoded to work with a particular skeleton-markerset
    combrination.  In this case the Metahuman skeleton with the QTM 
    animation markerset.
    """
    sel = cmds.ls(selection=True)
    rootJoint = sel[0]
    markerset = str(rootJoint).split(":")[0]
    #PrintJointDict(rootJoint)
    #PrintJointRule(rootJoint)
    _ConditionHierarchy(rootJoint)
    _PreCompute(markerset)
    _ApplyRules(rootJoint,markerset)


def FitSkeleton():
    bOK = SanityCheck()
    if bOK:
        _DoFitMetahumanSkeleton()

#print(f"__name__ is {__name__}")
if __name__ == "__main__":
    FitSkeleton()
    # sel = cmds.ls(selection=True)
    # rootJoint = sel[0]
    #PrintJointRule(rootJoint)
    #PrintJointDict(rootJoint)
