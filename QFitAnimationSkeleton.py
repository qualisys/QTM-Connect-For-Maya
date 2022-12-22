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

MARKER_SIZE = 1.0

def normalize(n):
    l = np.linalg.norm(n)
    return n/l
def OrthogonalizeV2(v1,v2):
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

def _LeftArm_rule_old(joint,markers,markerset):
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
def _LeftArm_rule(joint,markers,markerset):
    LElbowOut = MarkerPos("LElbowOut",markerset)
    LElbowFloor = np.array([LElbowOut[0],LElbowOut[1],0.0])

    LeftArm = JointPos("LeftArm",markerset)
    LWristOut = MarkerPos("LWristOut",markerset)
    LWristIn = MarkerPos("LWristIn",markerset)
    LWristMid = np.add(LWristIn, LWristOut)* 0.5
    LHandOut = MarkerPos("LHandOut",markerset)
    WristVec = normalize(np.subtract(LWristOut,LWristIn))
    HandVec = normalize(np.subtract(LHandOut,LWristOut))
    p1,p2 = closest_line_seg_line_seg(LElbowOut,LElbowFloor,LeftArm, LWristMid)

    ArmToElbowVec = normalize(np.subtract(p1,LeftArm))

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
def _LeftForeArmRoll_rule(joint,markers,markerset):
    pass
def _LeftHand_rule(joint,markers,markerset):
    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    HandOut = MarkerPos("LHandOut",markerset)
    WristVec = normalize(np.subtract(WristOut,WristIn))
    HandVec = normalize(np.subtract(HandOut,WristOut))

    UpVec = normalize(np.cross(HandVec,WristVec))
    FrontVec = normalize(np.subtract(WristIn,WristOut))
    if cmds.objExists(f"{markerset}:ModelPose:LeftHand_end"):
        XOffsetVec = normalize(JointPosLocal("LeftHand_end",markerset))
        ROffset = QRotationBetweenVectors(XOffsetVec,np.array([-1.0,0.0,0.0]))
    else:
        ROffset = qscipy.QRotation()

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

def _RightArm_rule_old(joint,markers,markerset):
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

def _RightArm_rule(joint,markers,markerset):
    RElbowOut = MarkerPos("RElbowOut",markerset)
    RElbowFloor = np.array([RElbowOut[0],RElbowOut[1],0.0])

    RWristOut = MarkerPos("RWristOut",markerset)
    RWristIn = MarkerPos("RWristIn",markerset)
    RWristMid = np.add(RWristIn, RWristOut)* 0.5
    RightArm = JointPos("RightArm",markerset)
    RHandOut = MarkerPos("RHandOut",markerset)
    WristVec = normalize(np.subtract(RWristOut,RWristIn))
    HandVec = normalize(np.subtract(RHandOut,RWristOut))

    p1,p2 = closest_line_seg_line_seg(RElbowOut,RElbowFloor,RightArm, RWristMid)
    # print(f"p1 is {p1}")
    # print(f"p2 is {p2}")
    ArmToElbowVec = normalize(np.subtract(RightArm,p1))
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
    print(f"RFA name {str(joint).split(':')[-1]}")
    SetJointGlobal("RightForeArm", markerset, None,e)

def _RightForeArmRoll_rule(joint,markers,markerset):
    pass

def _RightHand_rule(joint,markers,markerset):
    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    HandOut = MarkerPos("RHandOut",markerset)
    WristVec = normalize(np.subtract(WristOut,WristIn))
    HandVec = normalize(np.subtract(HandOut,WristOut))

    UpVec = normalize(np.cross(WristVec,HandVec))
    FrontVec = normalize(np.subtract(WristIn,WristOut))

    if cmds.objExists(f"{markerset}:ModelPose:RightHand_end"):
        XOffsetVec = normalize(JointPosLocal("RightHand_end",markerset))
        ROffset = QRotationBetweenVectors(XOffsetVec,np.array([1.0,0.0,0.0]))
    else:
        ROffset = qscipy.QRotation()

    R = QRotationFromReference(UpVec,FrontVec)
    RTotal = R * ROffset

    e = RTotal.as_euler("xyz")
    #print(f"RH name {str(joint).split(':')[-1]}")
    SetJointGlobal(str(joint).split(':')[-1], markerset, None,e)

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



def _RightInHandThumb_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RThumbTip"):
        return
    my_name = str(joint).split(':')[-1]

    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    ThumbTip = MarkerPos("RThumbTip",markerset)
    MyJoint = JointPos(my_name,markerset)

    ThumbTip[1] -= MARKER_SIZE
    MidLine = np.add(ThumbTip*0.3333,WristIn*0.6666)

    WristVec = normalize(np.subtract(WristOut,WristIn))
    FingerVec = normalize(np.subtract(MidLine,MyJoint))

    UpVec = normalize(np.cross(WristVec,FingerVec))
    FrontVec = normalize(np.cross(UpVec,FingerVec))

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _RightHandThumb1_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RThumbTip"):
        return
    my_name = str(joint).split(':')[-1]

    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    ThumbTip = MarkerPos("RThumbTip",markerset)
    MyJoint = JointPos(my_name,markerset)

    ThumbTip[1] -= MARKER_SIZE
    MidLine = np.add(ThumbTip*0.5,WristIn*0.5)

    WristVec = normalize(np.subtract(WristOut,WristIn))
    FingerVec = normalize(np.subtract(MidLine,MyJoint))

    UpVec = normalize(np.cross(WristVec,FingerVec))
    FrontVec = normalize(np.cross(UpVec,FingerVec))

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _RightHandThumb2_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RThumbTip"):
        return
    my_name = str(joint).split(':')[-1]

    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    ThumbTip = MarkerPos("RThumbTip",markerset)
    MyJoint = JointPos(my_name,markerset)

    #RThumbTip[1] += MARKER_SIZE

    WristVec = normalize(np.subtract(WristOut,WristIn))
    FingerVec = normalize(np.subtract(ThumbTip,MyJoint))

    UpVec = normalize(np.cross(WristVec,FingerVec))
    FrontVec = normalize(np.cross(UpVec,FingerVec))

    if cmds.objExists(f"{markerset}:ModelPose:RightHandThumb3"):
        XOffsetVec = normalize(JointPosLocal("RightHandThumb3",markerset))
        ROffset = QRotationBetweenVectors(np.array([1.0,0.0,0.0]),XOffsetVec)
    else:
        ROffset = qscipy.QRotation()

    R = QRotationFromReference(UpVec,FrontVec)
    RTotal = R * ROffset

    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _RightHandThumb3_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _RightInHandIndex_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RHandIn"):
        return

    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    HandIn = MarkerPos("RHandIn",markerset)
    RHIndex = JointPos("RightInHandIndex",markerset)
    HandIn[2] -= MARKER_SIZE

    WristVec = normalize(np.subtract(WristOut,WristIn))
    IndexVec = normalize(np.subtract(HandIn,RHIndex))

    UpVec = normalize(np.cross(WristVec,IndexVec))
    FrontVec = normalize(np.cross(UpVec,IndexVec))

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(str(joint).split(':')[-1], markerset, None,e)

def _RightHandIndex1_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RHandIn"):
        return
    if not cmds.objExists(f"{markerset}:RIndexTip"):
        return
    my_name = str(joint).split(':')[-1]

    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    HandIn = MarkerPos("RHandIn",markerset)
    IndexTip = MarkerPos("RIndexTip",markerset)
    MyJoint = JointPos(my_name,markerset)

    HandIn[2] -= MARKER_SIZE
    IndexTip[2] -= MARKER_SIZE

    WristVec = normalize(np.subtract(WristOut,WristIn))
    IndexVec = normalize(np.subtract(IndexTip,MyJoint))

    UpVec = normalize(np.cross(WristVec,IndexVec))
    FrontVec = normalize(np.cross(UpVec,IndexVec))

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _RightHandIndex2_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _RightHandIndex3_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _RightInHandMiddle_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RHandIn"):
        return   
    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    HandOut = MarkerPos("RHandOut",markerset)
    HandIn = MarkerPos("RHandIn",markerset)
    RHMiddle = JointPos("RightInHandMiddle",markerset)

    HandOut[2] -= MARKER_SIZE
    HandIn[2] -= MARKER_SIZE
    HandMid = np.add(HandOut*0.3333,HandIn*0.6666)

    WristVec = normalize(np.subtract(WristOut,WristIn))
    FingerVec = normalize(np.subtract(HandMid,RHMiddle))

    UpVec = normalize(np.cross(WristVec,FingerVec))
    FrontVec = normalize(np.cross(UpVec,FingerVec))

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(str(joint).split(':')[-1], markerset, None,e)

def _RightHandMiddle1_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RPinkyTip"):
        return
    if not cmds.objExists(f"{markerset}:RIndexTip"):
        return
    my_name = str(joint).split(':')[-1]

    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    HandOut = MarkerPos("RHandOut",markerset)
    PinkyTip = MarkerPos("RPinkyTip",markerset)
    IndexTip = MarkerPos("RIndexTip",markerset)
    MyJoint = JointPos(my_name,markerset)

    IndexTip[2] -= MARKER_SIZE
    PinkyTip[2] -= MARKER_SIZE
    MidTip = np.add(PinkyTip*0.3333,IndexTip*0.6666)

    WristVec = normalize(np.subtract(WristOut,WristIn))
    FingerVec = normalize(np.subtract(MidTip,MyJoint))

    UpVec = normalize(np.cross(WristVec,FingerVec))
    FrontVec = normalize(np.cross(UpVec,FingerVec))

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _RightHandMiddle2_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _RightHandMiddle3_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _RightInHandRing_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RHandIn"):
        return   
    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    HandOut = MarkerPos("RHandOut",markerset)
    HandIn = MarkerPos("RHandIn",markerset)
    RHRing = JointPos("RightInHandRing",markerset)

    HandOut[2] -= MARKER_SIZE
    HandIn[2] -= MARKER_SIZE
    HandMid = np.add(HandIn*0.3333,HandOut*0.6666)

    WristVec = normalize(np.subtract(WristOut,WristIn))
    FingerVec = normalize(np.subtract(HandMid,RHRing))

    UpVec = normalize(np.cross(WristVec,FingerVec))
    FrontVec = normalize(np.cross(UpVec,FingerVec))

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(str(joint).split(':')[-1], markerset, None,e)

def _RightHandRing1_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RPinkyTip"):
        return
    if not cmds.objExists(f"{markerset}:RIndexTip"):
        return
    my_name = str(joint).split(':')[-1]

    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    HandOut = MarkerPos("RHandOut",markerset)
    PinkyTip = MarkerPos("RPinkyTip",markerset)
    IndexTip = MarkerPos("RIndexTip",markerset)
    MyJoint = JointPos(my_name,markerset)

    IndexTip[2] -= MARKER_SIZE
    PinkyTip[2] -= MARKER_SIZE
    MidTip = np.add(IndexTip*0.3333,PinkyTip*0.6666)

    WristVec = normalize(np.subtract(WristOut,WristIn))
    FingerVec = normalize(np.subtract(MidTip,MyJoint))

    UpVec = normalize(np.cross(WristVec,FingerVec))
    FrontVec = normalize(np.cross(UpVec,FingerVec))

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _RightHandRing2_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _RightHandRing3_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _RightInHandPinky_rule(joint,markers,markerset):
    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    HandOut = MarkerPos("RHandOut",markerset)
    RHPinky = JointPos("RightInHandPinky",markerset)
    HandOut[2] -= MARKER_SIZE

    WristVec = normalize(np.subtract(WristOut,WristIn))
    PinkyVec = normalize(np.subtract(HandOut,RHPinky))

    UpVec = normalize(np.cross(WristVec,PinkyVec))
    FrontVec = normalize(np.cross(UpVec,PinkyVec))

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(str(joint).split(':')[-1], markerset, None,e)

def _RightHandPinky1_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RPinkyTip"):
        return
    my_name = str(joint).split(':')[-1]

    WristOut = MarkerPos("RWristOut",markerset)
    WristIn = MarkerPos("RWristIn",markerset)
    HandOut = MarkerPos("RHandOut",markerset)
    PinkyTip = MarkerPos("RPinkyTip",markerset)
    MyJoint = JointPos(my_name,markerset)

    HandOut[2] -= MARKER_SIZE
    PinkyTip[2] -= MARKER_SIZE

    WristVec = normalize(np.subtract(WristOut,WristIn))
    PinkyVec = normalize(np.subtract(PinkyTip,MyJoint))

    UpVec = normalize(np.cross(WristVec,PinkyVec))
    FrontVec = normalize(np.cross(UpVec,PinkyVec))

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _RightHandPinky2_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _RightHandPinky3_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))


def _LeftInHandThumb_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:LThumbTip"):
        return
    my_name = str(joint).split(':')[-1]

    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    ThumbTip = MarkerPos("LThumbTip",markerset)
    MyJoint = JointPos(my_name,markerset)

    ThumbTip[1] -= MARKER_SIZE
    MidLine = np.add(ThumbTip*0.3333,WristIn*0.6666)

    WristVec = normalize(np.subtract(WristOut,WristIn))
    FingerVec = normalize(np.subtract(MidLine,MyJoint))

    UpVec = normalize(np.cross(WristVec,FingerVec))
    FrontVec = normalize(np.cross(UpVec,FingerVec)) * -1.0

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _LeftHandThumb1_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:LThumbTip"):
        return
    my_name = str(joint).split(':')[-1]

    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    ThumbTip = MarkerPos("LThumbTip",markerset)
    MyJoint = JointPos(my_name,markerset)

    ThumbTip[1] -= MARKER_SIZE
    MidLine = np.add(ThumbTip*0.5,WristIn*0.5)

    WristVec = normalize(np.subtract(WristOut,WristIn))
    FingerVec = normalize(np.subtract(MidLine,MyJoint))

    UpVec = normalize(np.cross(WristVec,FingerVec))
    FrontVec = normalize(np.cross(UpVec,FingerVec)) * -1.0

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _LeftHandThumb2_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:LThumbTip"):
        return
    my_name = str(joint).split(':')[-1]

    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    ThumbTip = MarkerPos("LThumbTip",markerset)
    MyJoint = JointPos(my_name,markerset)

    #RThumbTip[1] += MARKER_SIZE

    WristVec = normalize(np.subtract(WristOut,WristIn))
    FingerVec = normalize(np.subtract(ThumbTip,MyJoint))

    UpVec = normalize(np.cross(WristVec,FingerVec))
    FrontVec = normalize(np.cross(UpVec,FingerVec)) * -1.0

    if cmds.objExists(f"{markerset}:ModelPose:LeftHandThumb3"):
        XOffsetVec = normalize(JointPosLocal("LeftHandThumb3",markerset))
        ROffset = QRotationBetweenVectors(np.array([-1.0,0.0,0.0]),XOffsetVec)
    else:
        ROffset = qscipy.QRotation()

    R = QRotationFromReference(UpVec,FrontVec)
    RTotal = R * ROffset

    e = RTotal.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _LeftHandThumb3_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _LeftInHandIndex_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RHandIn"):
        return

    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    HandIn = MarkerPos("LHandIn",markerset)
    RHIndex = JointPos("LeftInHandIndex",markerset)
    HandIn[2] -= MARKER_SIZE

    WristVec = normalize(np.subtract(WristOut,WristIn))
    IndexVec = normalize(np.subtract(HandIn,RHIndex))

    UpVec = normalize(np.cross(WristVec,IndexVec))
    FrontVec = normalize(np.cross(UpVec,IndexVec)) * -1.0

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(str(joint).split(':')[-1], markerset, None,e)


def _LeftHandIndex1_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RHandIn"):
        return
    if not cmds.objExists(f"{markerset}:RIndexTip"):
        return
    my_name = str(joint).split(':')[-1]

    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    HandIn = MarkerPos("LHandIn",markerset)
    IndexTip = MarkerPos("LIndexTip",markerset)
    MyJoint = JointPos(my_name,markerset)

    HandIn[2] -= MARKER_SIZE
    IndexTip[2] -= MARKER_SIZE

    WristVec = normalize(np.subtract(WristOut,WristIn))
    IndexVec = normalize(np.subtract(IndexTip,MyJoint))

    UpVec = normalize(np.cross(WristVec,IndexVec))
    FrontVec = normalize(np.cross(UpVec,IndexVec)) * -1.0

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _LeftHandIndex2_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _LeftHandIndex3_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _LeftInHandMiddle_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RHandIn"):
        return   
    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    HandOut = MarkerPos("LHandOut",markerset)
    HandIn = MarkerPos("LHandIn",markerset)
    RHMiddle = JointPos("LeftInHandMiddle",markerset)

    HandOut[2] -= MARKER_SIZE
    HandIn[2] -= MARKER_SIZE
    HandMid = np.add(HandOut*0.3333,HandIn*0.6666)

    WristVec = normalize(np.subtract(WristOut,WristIn))
    FingerVec = normalize(np.subtract(HandMid,RHMiddle))

    UpVec = normalize(np.cross(WristVec,FingerVec))
    FrontVec = normalize(np.cross(UpVec,FingerVec)) * -1.0

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(str(joint).split(':')[-1], markerset, None,e)

def _LeftHandMiddle1_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RPinkyTip"):
        return
    if not cmds.objExists(f"{markerset}:RIndexTip"):
        return
    my_name = str(joint).split(':')[-1]

    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    HandOut = MarkerPos("LHandOut",markerset)
    PinkyTip = MarkerPos("LPinkyTip",markerset)
    IndexTip = MarkerPos("LIndexTip",markerset)
    MyJoint = JointPos(my_name,markerset)

    IndexTip[2] -= MARKER_SIZE
    PinkyTip[2] -= MARKER_SIZE
    MidTip = np.add(PinkyTip*0.3333,IndexTip*0.6666)

    WristVec = normalize(np.subtract(WristOut,WristIn))
    FingerVec = normalize(np.subtract(MidTip,MyJoint))

    UpVec = normalize(np.cross(WristVec,FingerVec))
    FrontVec = normalize(np.cross(UpVec,FingerVec)) * -1.0

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _LeftHandMiddle2_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _LeftHandMiddle3_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _LeftInHandRing_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RHandIn"):
        return   
    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    HandOut = MarkerPos("LHandOut",markerset)
    HandIn = MarkerPos("LHandIn",markerset)
    RHRing = JointPos("LeftInHandRing",markerset)

    HandOut[2] -= MARKER_SIZE
    HandIn[2] -= MARKER_SIZE
    HandMid = np.add(HandIn*0.3333,HandOut*0.6666)

    WristVec = normalize(np.subtract(WristOut,WristIn))
    FingerVec = normalize(np.subtract(HandMid,RHRing))

    UpVec = normalize(np.cross(WristVec,FingerVec))
    FrontVec = normalize(np.cross(UpVec,FingerVec)) * -1.0

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(str(joint).split(':')[-1], markerset, None,e)

def _LeftHandRing1_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RPinkyTip"):
        return
    if not cmds.objExists(f"{markerset}:RIndexTip"):
        return
    my_name = str(joint).split(':')[-1]

    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    HandOut = MarkerPos("LHandOut",markerset)
    PinkyTip = MarkerPos("LPinkyTip",markerset)
    IndexTip = MarkerPos("LIndexTip",markerset)
    MyJoint = JointPos(my_name,markerset)

    IndexTip[2] -= MARKER_SIZE
    PinkyTip[2] -= MARKER_SIZE
    MidTip = np.add(IndexTip*0.3333,PinkyTip*0.6666)

    WristVec = normalize(np.subtract(WristOut,WristIn))
    FingerVec = normalize(np.subtract(MidTip,MyJoint))

    UpVec = normalize(np.cross(WristVec,FingerVec))
    FrontVec = normalize(np.cross(UpVec,FingerVec)) * -1.0

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _LeftHandRing2_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _LeftHandRing3_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _LeftInHandPinky_rule(joint,markers,markerset):
    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    HandOut = MarkerPos("LHandOut",markerset)
    RHPinky = JointPos("LeftInHandPinky",markerset)
    HandOut[2] -= MARKER_SIZE

    WristVec = normalize(np.subtract(WristOut,WristIn))
    PinkyVec = normalize(np.subtract(HandOut,RHPinky))

    UpVec = normalize(np.cross(WristVec,PinkyVec))
    FrontVec = normalize(np.cross(UpVec,PinkyVec)) * -1.0

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(str(joint).split(':')[-1], markerset, None,e)

def _LeftHandPinky1_rule(joint,markers,markerset):
    if not cmds.objExists(f"{markerset}:RPinkyTip"):
        return
    my_name = str(joint).split(':')[-1]

    WristOut = MarkerPos("LWristOut",markerset)
    WristIn = MarkerPos("LWristIn",markerset)
    HandOut = MarkerPos("LHandOut",markerset)
    PinkyTip = MarkerPos("LPinkyTip",markerset)
    MyJoint = JointPos(my_name,markerset)

    HandOut[2] -= MARKER_SIZE
    PinkyTip[2] -= MARKER_SIZE

    WristVec = normalize(np.subtract(WristOut,WristIn))
    PinkyVec = normalize(np.subtract(PinkyTip,MyJoint))

    UpVec = normalize(np.cross(WristVec,PinkyVec))
    FrontVec = normalize(np.cross(UpVec,PinkyVec)) * -1.0

    R = QRotationFromReference(UpVec,FrontVec)

    e = R.as_euler("xyz")
    SetJointGlobal(my_name, markerset, None,e)

def _LeftHandPinky2_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))

def _LeftHandPinky3_rule(joint,markers,markerset):
    my_name = str(joint).split(':')[-1]
    SetJointLocal(my_name, markerset, None, np.array([0.0,0.0,0.0]))


AnimRules = {
"Hips":(_Hips_rule,["WaistRFront","WaistLBack","WaistLFront","WaistRBack"]),
"Spine":(_Spine_rule,["WaistLBack","WaistRBack","BackL","BackR"]),
"Spine1":(_Spine1_rule,["BackL","BackR","Chest"]),
"Spine2":(_Spine2_rule,["Chest","SpineTop"]),
"LeftShoulder":(_LeftShoulder_rule,["LShoulderTop","LShoulderBack"]),
"LeftArm":(_LeftArm_rule,["LElbowOut","LArm"]),
"LeftForeArm":(_LeftForeArm_rule,["LElbowOut","LWristOut","LWristIn"]),
"LeftForeArmRoll":(_LeftForeArmRoll_rule,["LElbowOut","LWristOut","LWristIn"]),
"LeftHand":(_LeftHand_rule,["LWristOut","LWristIn","LHandOut","LeftHandExtra"]),
"RightShoulder":(_RightShoulder_rule,["RShoulderTop","RShoulderBack"]),
"RightArm":(_RightArm_rule,["RElbowOut","RArm"]),
"RightForeArm":(_RightForeArm_rule,["RElbowOut","RWristOut","RWristIn"]),
"RightForeArmRoll":(_RightForeArmRoll_rule,["RElbowOut","RWristOut","RWristIn"]),
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
"RightToeBase":(_RightToeBase_rule,["RForefootIn","RForefootOut","RToeTip"]),
"RightInHandThumb":(_RightInHandThumb_rule,[]),
"RightHandThumb1":(_RightHandThumb1_rule,["RWristIn","RThumbTip"]),
"RightHandThumb2":(_RightHandThumb2_rule,[]),
"RightHandThumb3":(_RightHandThumb3_rule,["RThumbTip"]),
"RightInHandIndex":(_RightInHandIndex_rule,[]),
"RightHandIndex1":(_RightHandIndex1_rule,[]),
"RightHandIndex2":(_RightHandIndex2_rule,[]),
"RightHandIndex3":(_RightHandIndex3_rule,["RIndexTip"]),
"RightInHandMiddle":(_RightInHandMiddle_rule,[]),
"RightHandMiddle1":(_RightHandMiddle1_rule,[]),
"RightHandMiddle2":(_RightHandMiddle2_rule,[]),
"RightHandMiddle3":(_RightHandMiddle3_rule,[]),
"RightInHandRing":(_RightInHandRing_rule,[]),
"RightHandRing1":(_RightHandRing1_rule,[]),
"RightHandRing2":(_RightHandRing2_rule,[]),
"RightHandRing3":(_RightHandRing3_rule,[]),
"RightInHandPinky":(_RightInHandPinky_rule,[]),
"RightHandPinky1":(_RightHandPinky1_rule,[]),
"RightHandPinky2":(_RightHandPinky2_rule,[]),
"RightHandPinky3":(_RightHandPinky3_rule,["RPinkyTip"]),
"LeftInHandThumb":(_LeftInHandThumb_rule,[]),
"LeftHandThumb1":(_LeftHandThumb1_rule,["LWristIn","LThumbTip"]),
"LeftHandThumb2":(_LeftHandThumb2_rule,[]),
"LeftHandThumb3":(_LeftHandThumb3_rule,["LThumbTip"]),
"LeftInHandIndex":(_LeftInHandIndex_rule,[]),
"LeftHandIndex1":(_LeftHandIndex1_rule,[]),
"LeftHandIndex2":(_LeftHandIndex2_rule,[]),
"LeftHandIndex3":(_LeftHandIndex3_rule,["LIndexTip"]),
"LeftInHandMiddle":(_LeftInHandMiddle_rule,[]),
"LeftHandMiddle1":(_LeftHandMiddle1_rule,[]),
"LeftHandMiddle2":(_LeftHandMiddle2_rule,[]),
"LeftHandMiddle3":(_LeftHandMiddle3_rule,[]),
"LeftInHandRing":(_LeftInHandRing_rule,[]),
"LeftHandRing1":(_LeftHandRing1_rule,[]),
"LeftHandRing2":(_LeftHandRing2_rule,[]),
"LeftHandRing3":(_LeftHandRing3_rule,[]),
"LeftInHandPinky":(_LeftInHandPinky_rule,[]),
"LeftHandPinky1":(_LeftHandPinky1_rule,[]),
"LeftHandPinky2":(_LeftHandPinky2_rule,[]),
"LeftHandPinky3":(_LeftHandPinky3_rule,["LPinkyTip"])
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
    if nodeName in AnimRules:
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
    # sel = cmds.ls(selection=True)
    # rootJoint = sel[0]
    #PrintJointRule(rootJoint)
    #PrintJointDict(rootJoint)
