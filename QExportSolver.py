import xml.etree.ElementTree as ET
import maya.cmds as cmds
import math
import numpy as np
import tempfile
import importlib
import os, sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/')
import qscipy
importlib.reload(qscipy)
from qscipy import QRotation

def extract_rotation(xform):
    """
    Extract the qscipy rotation
    from the full transform
    """
    R = QRotation()
    for i in range(0,3):
        for j in range(0,3):
            # R.M[i][j] = xform[j][i]
            R.M[i][j] = xform[i][j]
    return R
#
#
#
# Quaternion to Euler Angle converter.  This is mainly used for the importer
#
def QtoE(qx,qy,qz,qw):
    x = float(qx)
    y = float(qy)
    z = float(qz)
    w = float(qw)
    
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    X = math.degrees(math.atan2(t0, t1))

    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    Y = math.degrees(math.asin(t2))

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    Z = math.degrees(math.atan2(t3, t4))

    return X, Y, Z
    

#    
# Euler Angles to Quaternion converter.
#
def EtoQ(yaw, pitch, roll):

    qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
    qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
    qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)

    return [qx, qy, qz, qw]

# multiply two row-major 4x4 matrices.
def matmul(m1,m2):
    R = np.array([[1.0,0.0,0.0,0.0],[0.0,1.0,0.0,0.0],[0.0,0.0,1.0,0.0],[0.0,0.0,0.0,1.0]])
    R[0][0] = m1[0][0]*m2[0][0] + m1[0][1]*m2[1][0] + m1[0][2]*m2[2][0] + m1[0][3]*m2[3][0]
    R[0][1] = m1[0][0]*m2[0][1] + m1[0][1]*m2[1][1] + m1[0][2]*m2[2][1] + m1[0][3]*m2[3][1]
    R[0][2] = m1[0][0]*m2[0][2] + m1[0][1]*m2[1][2] + m1[0][2]*m2[2][2] + m1[0][3]*m2[3][2]
    R[0][3] = m1[0][0]*m2[0][3] + m1[0][1]*m2[1][3] + m1[0][2]*m2[2][3] + m1[0][3]*m2[3][3]
    R[1][0] = m1[1][0]*m2[0][0] + m1[1][1]*m2[1][0] + m1[1][2]*m2[2][0] + m1[1][3]*m2[3][0]
    R[1][1] = m1[1][0]*m2[0][1] + m1[1][1]*m2[1][1] + m1[1][2]*m2[2][1] + m1[1][3]*m2[3][1]
    R[1][2] = m1[1][0]*m2[0][2] + m1[1][1]*m2[1][2] + m1[1][2]*m2[2][2] + m1[1][3]*m2[3][2]
    R[1][3] = m1[1][0]*m2[0][3] + m1[1][1]*m2[1][3] + m1[1][2]*m2[2][3] + m1[1][3]*m2[3][3]
    R[2][0] = m1[2][0]*m2[0][0] + m1[2][1]*m2[1][0] + m1[2][2]*m2[2][0] + m1[2][3]*m2[3][0]
    R[2][1] = m1[2][0]*m2[0][1] + m1[2][1]*m2[1][1] + m1[2][2]*m2[2][1] + m1[2][3]*m2[3][1]
    R[2][2] = m1[2][0]*m2[0][2] + m1[2][1]*m2[1][2] + m1[2][2]*m2[2][2] + m1[2][3]*m2[3][2]
    R[2][3] = m1[2][0]*m2[0][3] + m1[2][1]*m2[1][3] + m1[2][2]*m2[2][3] + m1[2][3]*m2[3][3]
    R[3][0] = m1[3][0]*m2[0][0] + m1[3][1]*m2[1][0] + m1[3][2]*m2[2][0] + m1[3][3]*m2[3][0]
    R[3][1] = m1[3][0]*m2[0][1] + m1[3][1]*m2[1][1] + m1[3][2]*m2[2][1] + m1[3][3]*m2[3][1]
    R[3][2] = m1[3][0]*m2[0][2] + m1[3][1]*m2[1][2] + m1[3][2]*m2[2][2] + m1[3][3]*m2[3][2]
    R[3][3] = m1[3][0]*m2[0][3] + m1[3][1]*m2[1][3] + m1[3][2]*m2[2][3] + m1[3][3]*m2[3][3]
    return R
       
# For indenting to make the printout pretty
# four spaces per level.
#
def Spaces(level):
    r = ""
    for i in range(0,level):
        r = r + "    "
    return r



################################################################
#
# Class QExportSolver
#
# Handles the traversal of a Maya scene with solver information
# and exports it to an XML file or string.
#
################################################################
class QExportSolver:

    def __init__(self):
        self._sceneScale = 1.0
        self._rootScale = 1.0
        self._fd = None
        self._sXML = u""
        self._NS = u":"
        self._MPNS = self._NS+u"ModelPose:"
        self._root_is_reference = False
        self._reference_child = None

    def _SetNamespace(self, namespace):
        self._NS = namespace+u":"
        self._MPNS = self._NS+u"ModelPose:"
        print ("Namespace = ", self._NS)
        print ("Model Pose Namespace = ", self._MPNS)
        
    # SetSceneScale()
    #
    # Calculate the conversion factor for converting the current scene units into mm, which QTM requires.
    #     [mm | millimeter | cm | centimeter | m | meter | km | kilometer | in | inch | ft | foot | yd | yard | mi | mile]
    # Also grab the skeleton scale from the root node
    #
    def SetSceneScale(self):
        cu = cmds.currentUnit( query=True, linear=True )
        if cu == "cm":
            self._sceneScale = 10.0
        elif cu == "mm":
             self._sceneScale = 1.0
        elif cu == "m":
            self._sceneScale = 1000.0
        elif cu == "m":
            self._sceneScale = 1000000.0
        elif cu == "ft":
            self._sceneScale = 304.8
        elif cu == "yd":
            self._sceneScale = 914.4
        elif cu == "mi":
            self._sceneScale = 1609300.0
        else:
            self._sceneScale = 1.0
        
        if self._root_is_reference:
            scaleNode = self._reference_child
        else:
            # Sanity check passed, so this will work
            scaleNode = cmds.ls(selection=True)[0]
        scaleNodeName = str(scaleNode)
        self._rootScale = cmds.getAttr("%s.scaleX" % scaleNodeName)
    
        self._sceneScale = self._sceneScale * self._rootScale
        print (f"Scale node is {scaleNodeName}")
        print(f"Scale is {self._sceneScale}")
 
    def CheckRootIsReference(self):
        """
        Check to see if selected root node is actually the reference node.
        True if there is only one child and it has all the DOFs turned on,
        which means it's the hips/pelvis node.
        """
        self._root_is_reference = False
        rootNode = cmds.ls(selection=True)[0]
        children = cmds.listRelatives(rootNode,c=True)
        if len(children) != 1:
            return

        child = children[0]
        if not cmds.attributeQuery("XRotDoF",node=child, exists=True):
            return
        
        # Assume one attribute means they're all there.
        bRX = cmds.getAttr("%s.XRotDoF" % child)
        bRY = cmds.getAttr("%s.YRotDoF" % child)
        bRZ = cmds.getAttr("%s.ZRotDoF" % child)
        bTX = cmds.getAttr("%s.XTransDoF" % child)
        bTY = cmds.getAttr("%s.YTransDoF" % child)
        bTZ = cmds.getAttr("%s.ZTransDoF" % child)
        if bRX and bRY and bRZ and bTX and bTY and bTZ:
            self._root_is_reference = True
            self._reference_child = child

    def _Write(self, s):
        if self._fd is not None:
            self._fd.write(s)
            #self._fd.write(os.linesep)
            self._fd.write(u"\n")
        else:
            self._sXML = self._sXML + s + u"\n"
            
    # Hardcode use of "Markers" for now.  This is used to find the list
    # of marker names and scan
    # the attributes of the joint for one whose name matches the marker.
    #
    # Note that this has problems if a joint happens to have the same name
    # as a marker because then the marker name contains
    # the full path name which is not part of the attribute name
    #
    # Return True if markers were found.  False otherwise.
    def _ExportMarkers(self, node, level):
        bHasMarkers = False
        nodeName = str(node)
        markersNode =  f"{self._NS}Markers"
        markers = cmds.listRelatives(markersNode,c=True)
        if markers is None:
            print(f"No markers to export.")
            return
        for m in markers:
            #remove namespaces and leave just the marker name
            markerName = str(m).split(":")[-1]
            a = nodeName+"."+markerName
            #print a
            if cmds.attributeQuery(markerName,node=nodeName, exists=True):
                weight = str(cmds.getAttr(a))
                if not bHasMarkers :
                    bHasMarkers = True
                    self._Write( Spaces(level)+"<Markers>")
            
                # Get marker position relative to the segment
                cn = cmds.xform( self._NS+markerName, q=True, matrix=True, ws=True)
                pn = cmds.xform( nodeName, q=True, matrix=True, ws=True)

                cm = np.array([cn[0:4],cn[4:8],cn[8:12],cn[12:16]])
                pm = np.array([pn[0:4],pn[4:8],pn[8:12],pn[12:16]])
                pminv = np.linalg.inv(pm)
                om = matmul(cm,pminv)

                px = str(om[3][0] * self._sceneScale)
                py = str(om[3][1] * self._sceneScale)
                pz = str(om[3][2] * self._sceneScale)
               
                self._Write( Spaces(level+1)+"<Marker Name=\"" + markerName + "\">")
                self._Write( Spaces(level+2)+"<Position X=\"" + px + "\" Y=\"" + py + "\" Z=\"" + pz +  "\"/>")
                self._Write( Spaces(level+2)+"<Weight>" + str(weight) + "</Weight>")
                self._Write( Spaces(level+1)+"</Marker>" )
    
        if bHasMarkers:
            self._Write( Spaces(level)+"</Markers>")
            return True
        else:
            return False

            
    # Hardcode the use of "RigidBodies" for now.  This is used to find the list
    # of rigid body names and scan
    # the attributes of the joint for one whose name matches the rigid body.
    #
    # Note that this has problems if a joint or marker happens to have the same name
    # as a rigid body because then the rigid body name contains
    # the full path name which is not part of the attribute name
    #
    # Return True if rigid bodies were found.  False otherwise.
    def _ExportRigidBodies(self, node, level):
        bHasRigidBodies = False
        nodeName = str(node)
        rigidbodiesNode =  f"{self._NS}RigidBodies"
        rigidbodies = cmds.listRelatives(rigidbodiesNode,c=True)
        if rigidbodies is None:
            print(f"No rigid bodies to export.")
            return
        for rb in rigidbodies:
            #remove namespaces and leave just the marker name
            rigidbodyName = str(rb).split(":")[-1]
            a = nodeName+"."+ rigidbodyName
            #print a
            if cmds.attributeQuery(rigidbodyName,node=nodeName, exists=True):
                weight = str(cmds.getAttr(a))
                if not bHasRigidBodies :
                    bHasRigidBodies = True
                    self._Write( Spaces(level)+"<RigidBodies>")
            
                # Get rigid body transform relative to the segment, set scale to one
                # first, then restore it
                rbname = self._NS+rigidbodyName
                sx = cmds.getAttr("%s.scaleX" % rbname)
                cmds.setAttr("%s.scaleX" % rbname, 1.0)
                cmds.setAttr("%s.scaleY" % rbname, 1.0)
                cmds.setAttr("%s.scaleZ" % rbname, 1.0)
                cn = cmds.xform( rbname, q=True, matrix=True, ws=True)
                cmds.setAttr("%s.scaleX" % rbname, sx)
                cmds.setAttr("%s.scaleY" % rbname, sx)
                cmds.setAttr("%s.scaleZ" % rbname, sx)

                pn = cmds.xform( nodeName, q=True, matrix=True, ws=True)
                cm = np.array([cn[0:4],cn[4:8],cn[8:12],cn[12:16]])
                pm = np.array([pn[0:4],pn[4:8],pn[8:12],pn[12:16]])
                pminv = np.linalg.inv(pm)
                # print(f"CM: \n{cm}")
                # print(f"PM: \n{pm}")
                # print(f"PMINV: \n{pminv}")

                om = matmul(cm,pminv)
                # print(f"OM: {om}")
                R = extract_rotation(om)
                Q = R.as_quat()
                # print(f"Q: {Q}")
                qx = str(Q[0])
                qy = str(Q[1])
                qz = str(Q[2])
                qw = str(Q[3])

                px = str(om[3][0] * self._sceneScale)
                py = str(om[3][1] * self._sceneScale)
                pz = str(om[3][2] * self._sceneScale)
               
                self._Write( Spaces(level+1)+"<RigidBody Name=\"" + rigidbodyName + "\">")
                self._Write( Spaces(level+2)+"<Transform>")
                self._Write( Spaces(level+3)+"<Position X=\"" + px + "\" Y=\"" + py + "\" Z=\"" + pz +  "\"/>")
                self._Write( Spaces(level+3)+"<Rotation X=\"" + qx + "\" Y=\"" + qy + "\" Z=\"" + qz +  "\" W=\"" + qw + "\"/>")
                self._Write( Spaces(level+2)+"</Transform>")
                self._Write( Spaces(level+2)+"<Weight>" + str(weight) + "</Weight>")
                self._Write( Spaces(level+1)+"</RigidBody>" )
            
    
        if bHasRigidBodies:
            self._Write( Spaces(level)+"</RigidBodies>")
            return True
        else:
            return False

    #
    # ExportTransform
    #
    # Calculates the transform.  Local attributes are used
    # so this is relative to the parent.
    # The "DefaultTransform" comes from the Maya joint "Preferred Angle"
    # definition.  In Maya thi is used for IK calculations,
    # but we'll use it for the Default Transform which should be the value that puts the joint in a "T Pose".
    # Usually this will be a zero rotation, but sometimes not....
    #
    def _ExportTransform(self, item, level):

        # Do the math first, get the local transform
        px = str(cmds.getAttr("%s.translateX" % item) * self._sceneScale)
        py = str(cmds.getAttr("%s.translateY" % item) * self._sceneScale)
        pz = str(cmds.getAttr("%s.translateZ" % item) * self._sceneScale)
        rx = math.radians(cmds.getAttr("%s.rotateX" % item))
        ry = math.radians(cmds.getAttr("%s.rotateY" % item))
        rz = math.radians(cmds.getAttr("%s.rotateZ" % item))
        Q = EtoQ(rz,ry,rx)   
        qx = str(Q[0])
        qy = str(Q[1])
        qz = str(Q[2])
        qw = str(Q[3])
    
        # Get the default transform from the Preferred Angle of the joint
        pax = math.radians(cmds.getAttr("%s.preferredAngleX" % item))
        pay = math.radians(cmds.getAttr("%s.preferredAngleY" % item))
        paz = math.radians(cmds.getAttr("%s.preferredAngleZ" % item))

        Q = EtoQ(paz,pay,pax)   
        paqx = str(Q[0])
        paqy = str(Q[1])
        paqz = str(Q[2])
        paqw = str(Q[3])
       
        #print "T  =", rx, ry, rz
        #print "DT = ", pax, pay, paz
        
        # Write out both
        self._Write( Spaces(level)+"<Transform>")
        self._Write( Spaces(level+1)+"<Position X=\"" + px + "\" Y=\""+ py + "\" Z=\"" + pz + "\"/>")
        self._Write( Spaces(level+1)+"<Rotation X=\"" + qx + "\" Y=\""+ qy + "\" Z=\"" + qz +"\" W=\"" + qw + "\"/>")
        self._Write( Spaces(level)+"</Transform>")
        self._Write( Spaces(level)+"<DefaultTransform>")
        self._Write( Spaces(level+1)+"<Position X=\"" + px + "\" Y=\""+ py + "\" Z=\"" + pz + "\"/>")
        self._Write( Spaces(level+1)+"<Rotation X=\"" + paqx + "\" Y=\""+ paqy + "\" Z=\"" + paqz +"\" W=\"" + paqw + "\"/>")
        self._Write( Spaces(level)+"</DefaultTransform>")
 
    # Assume it's a leaf node until a grandchild is found
    def _IsLeaf(self, jointNode):
        bIs = True
        children = cmds.listRelatives(jointNode,c=True)
        if children:
            for c in children:
                grandChildren = cmds.listRelatives(c,c=True)
                if  grandChildren :
                    bIs = False
        return bIs


    # ExportDOFs
    #
    # Inspect the attributes and if the ones for DOFs are there then use them to write out the dofs    
    def _ExportDOFs(self, jointNode, level):
        nodeName = str(jointNode)
        bHasAttributes = cmds.attributeQuery("XRotDoF",node=nodeName, exists=True)
        
        self._Write( Spaces(level+1)+"<DegreesOfFreedom>")
    
        if bHasAttributes:
            # Assume one attribute means they're all there.
            bRX = cmds.getAttr("%s.XRotDoF" % nodeName)
            bRY = cmds.getAttr("%s.YRotDoF" % nodeName)
            bRZ = cmds.getAttr("%s.ZRotDoF" % nodeName)
            bTX = cmds.getAttr("%s.XTransDoF" % nodeName)
            bTY = cmds.getAttr("%s.YTransDoF" % nodeName)
            bTZ = cmds.getAttr("%s.ZTransDoF" % nodeName)
            if bRX:
                lb = math.radians(cmds.getAttr("%s.XRotDoF_LowerBound" % nodeName))
                ub = math.radians(cmds.getAttr("%s.XRotDoF_UpperBound" % nodeName))
                self._Write( Spaces(level+2)+"<RotationX>")
                self._Write( Spaces(level+3)+"<Constraint LowerBound=\""+str(lb)+"\" UpperBound=\""+str(ub)+"\"/>")

                # Check for coupling definition
                bHasCoupling1 = cmds.attributeQuery("XRot_CP1_Coeff",node=nodeName, exists=True)
                bHasCoupling2 = cmds.attributeQuery("XRot_CP2_Coeff",node=nodeName, exists=True)

                if bHasCoupling1:
                    bCP1_coeff = cmds.getAttr("%s.XRot_CP1_Coeff"% nodeName)
                    bCP1_segment = cmds.getAttr("%s.XRot_CP1_Segment"% nodeName)
                if bHasCoupling2:
                    bCP2_coeff = cmds.getAttr("%s.XRot_CP2_Coeff"% nodeName)
                    bCP2_segment = cmds.getAttr("%s.XRot_CP2_Segment"% nodeName)
                if bHasCoupling1:
                    self._Write( Spaces(level+3) + "<Couplings>")
                    self._Write( Spaces(level+4)+ "<Coupling Coefficient=\""+str(bCP1_coeff)+"\" DegreeOfFreedom=\"RotationX\" Segment=\""+ bCP1_segment+"\"/>")
                    if bHasCoupling2:
                        self._Write( Spaces(level+4)+ "<Coupling Coefficient=\""+str(bCP2_coeff)+"\" DegreeOfFreedom=\"RotationX\" Segment=\""+ bCP2_segment+"\"/>")

                    self._Write( Spaces(level+3) + "</Couplings>")
                self._Write( Spaces(level+2)+"</RotationX>")

            if bRY:     
                lb = math.radians(cmds.getAttr("%s.YRotDoF_LowerBound" % nodeName))
                ub = math.radians(cmds.getAttr("%s.YRotDoF_UpperBound" % nodeName))
                self._Write( Spaces(level+2)+"<RotationY>")
                self._Write( Spaces(level+3)+"<Constraint LowerBound=\""+str(lb)+"\" UpperBound=\""+str(ub)+"\"/>")

                # Check for coupling definition
                bHasCoupling1 = cmds.attributeQuery("YRot_CP1_Coeff",node=nodeName, exists=True)
                bHasCoupling2 = cmds.attributeQuery("YRot_CP2_Coeff",node=nodeName, exists=True)

                if bHasCoupling1:
                    bCP1_coeff = cmds.getAttr("%s.YRot_CP1_Coeff"% nodeName)
                    bCP1_segment = cmds.getAttr("%s.YRot_CP1_Segment"% nodeName)
                if bHasCoupling2:
                    bCP2_coeff = cmds.getAttr("%s.YRot_CP2_Coeff"% nodeName)
                    bCP2_segment = cmds.getAttr("%s.YRot_CP2_Segment"% nodeName)
                if bHasCoupling1:
                    self._Write( Spaces(level+3) + "<Couplings>")
                    self._Write( Spaces(level+4)+ "<Coupling Coefficient=\""+str(bCP1_coeff)+"\" DegreeOfFreedom=\"RotationY\" Segment=\""+ bCP1_segment+"\"/>")
                    if bHasCoupling2:
                        self._Write( Spaces(level+4)+ "<Coupling Coefficient=\""+str(bCP2_coeff)+"\" DegreeOfFreedom=\"RotationY\" Segment=\""+ bCP2_segment+"\"/>")

                    self._Write( Spaces(level+3) + "</Couplings>")
                self._Write( Spaces(level+2)+"</RotationY>")


            if bRZ: 
                lb = math.radians(cmds.getAttr("%s.ZRotDoF_LowerBound" % nodeName))
                ub = math.radians(cmds.getAttr("%s.ZRotDoF_UpperBound" % nodeName))
                self._Write( Spaces(level+2)+"<RotationZ>")
                self._Write( Spaces(level+3)+"<Constraint LowerBound=\""+str(lb)+"\" UpperBound=\""+str(ub)+"\"/>")

                # Check for coupling definition
                bHasCoupling1 = cmds.attributeQuery("ZRot_CP1_Coeff",node=nodeName, exists=True)
                bHasCoupling2 = cmds.attributeQuery("ZRot_CP2_Coeff",node=nodeName, exists=True)

                if bHasCoupling1:
                    bCP1_coeff = cmds.getAttr("%s.ZRot_CP1_Coeff"% nodeName)
                    bCP1_segment = cmds.getAttr("%s.ZRot_CP1_Segment"% nodeName)
                if bHasCoupling2:
                    bCP2_coeff = cmds.getAttr("%s.ZRot_CP2_Coeff"% nodeName)
                    bCP2_segment = cmds.getAttr("%s.ZRot_CP2_Segment"% nodeName)
                if bHasCoupling1:
                    self._Write( Spaces(level+3) + "<Couplings>")
                    self._Write( Spaces(level+4)+ "<Coupling Coefficient=\""+str(bCP1_coeff)+"\" DegreeOfFreedom=\"RotationZ\" Segment=\""+ bCP1_segment+"\"/>")
                    if bHasCoupling2:
                        self._Write( Spaces(level+4)+ "<Coupling Coefficient=\""+str(bCP2_coeff)+"\" DegreeOfFreedom=\"RotationZ\" Segment=\""+ bCP2_segment+"\"/>")

                    self._Write( Spaces(level+3) + "</Couplings>")
                self._Write( Spaces(level+2)+"</RotationZ>")

            if bTX:
                self._Write( Spaces(level+2)+"<TranslationX/>")
            if bTY:
                self._Write( Spaces(level+2)+"<TranslationY/>")
            if bTZ:
                self._Write( Spaces(level+2)+"<TranslationZ/>")
        self._Write( Spaces(level+1)+"</DegreesOfFreedom>")
    
    
    # very similar to ExportRootJoint, except no translation DoFs and have to check for end point   
    def _ExportJoint(self, jointNode, level):
        bLeaf = False
        segmentName = str(jointNode).split(":")[-1]
        self._Write( Spaces(level)+"<Segment Name=\"" + segmentName + "\">")
    
        children = cmds.listRelatives(jointNode,c=True)
        if not children:
            #print "Shouldn't get here!!", jointNode
            bLeaf = True
            end_px = str(0)
            end_py = str(0)
            end_pz = str(1 * self._sceneScale)
           
        elif self._IsLeaf(jointNode):
            bLeaf = True
            endNode = children[0]
        
            end_px = str(cmds.getAttr("%s.translateX" % endNode) * self._sceneScale)
            end_py = str(cmds.getAttr("%s.translateY" % endNode) * self._sceneScale)
            end_pz = str(cmds.getAttr("%s.translateZ" % endNode) * self._sceneScale)

        # Check for solver root
        bHasSolver = cmds.attributeQuery("Solver",node=str(jointNode), exists=True)
        if bHasSolver :
            self._Write( Spaces(level+1) +"<Solver> Global Optimization </Solver>")
        self._ExportTransform(jointNode,level+1)

        # Hardcode Dofs for now, root has translation and rotation
        self._ExportDOFs(jointNode, level)

        if bLeaf:
            self._Write( Spaces(level+1)+"<Endpoint X=\"" + end_px + "\" Y=\""+ end_py + "\" Z=\"" + end_pz + "\"/>")
        
        self._ExportMarkers(jointNode,level+1)
        self._ExportRigidBodies(jointNode,level+1)
        # self._Write( Spaces(level+1)+"<RigidBodies/>")
    
        if not bLeaf:    
            # Export children, again assume that children exist
            if children : 
                for c in children:
                    self._ExportJoint(c, level+1)
        
        self._Write( Spaces(level)+"</Segment>")
    
    
    # ExportRootJoint
    #
    # Special joint, assume it's a "Global" joint with 6 DoFs.
    #
    def _ExportRootJoint(self, rootNode, level):
    
        bIsProp = False
        segmentName = str(rootNode).split(":")[-1]
    
        self._Write( Spaces(level)+"<Segment Name=\"" + segmentName + "\">")
    
        self._ExportTransform(rootNode,level+1)
    
        # Hardcode Dofs for now, root has translation and rotation
        self._Write( Spaces(level+1)+"<DegreesOfFreedom>")
        self._Write( Spaces(level+2)+"<RotationX/>")
        self._Write( Spaces(level+2)+"<RotationY/>")
        self._Write( Spaces(level+2)+"<RotationZ/>")
        self._Write( Spaces(level+2)+"<TranslationX/>")
        self._Write( Spaces(level+2)+"<TranslationY/>")
        self._Write( Spaces(level+2)+"<TranslationZ/>")
        self._Write( Spaces(level+1)+"</DegreesOfFreedom>")
    
        bIsProp = self._IsLeaf(rootNode)
        if bIsProp:
            children = cmds.listRelatives(rootNode,c=True)
            if not children:
                end_px = str(0)
                end_py = str(0)
                end_pz = str(1 * self._sceneScale)
               
            else:
                endNode = children[0]         
                end_px = str(cmds.getAttr("%s.translateX" % endNode) * self._sceneScale)
                end_py = str(cmds.getAttr("%s.translateY" % endNode) * self._sceneScale)
                end_pz = str(cmds.getAttr("%s.translateZ" % endNode) * self._sceneScale)
            self._Write( Spaces(level+1)+"<Endpoint X=\"" + end_px + "\" Y=\""+ end_py + "\" Z=\"" + end_pz + "\"/>")
        else:
            self._Write( Spaces(level+1)+"<Endpoint/>")
    
        #Markers
        self._ExportMarkers(rootNode,level+1)
        self._ExportRigidBodies(rootNode,level+1)
        # self._Write( Spaces(level+1)+"<RigidBodies/>")
    
        if not bIsProp:
            # Export children, again assume that children exist
            children = cmds.listRelatives(rootNode,c=True)
            for c in children:
                self._ExportJoint(c, level+1)
        
        #close section and return
        self._Write( Spaces(level)+"</Segment>")

    def _ExportReferenceJoint(self, rootNode, level):
        segmentName = str(rootNode).split(":")[-1]
        children = cmds.listRelatives(rootNode,c=True)
        child = children[0]    

        self._Write( Spaces(level)+"<Segment Name=\"" + segmentName + "\">")
        self._ExportRootJoint(child,level+1)
        self._Write( Spaces(level)+"</Segment>")        

    #
    # ExportSkeleton
    #
    # Start the export of the joint hierarchy
    #
    def _ExportSkeleton(self):
        # Get root joint, it's been previously verified that it is the currently selected node
        nodes = cmds.ls(selection=True)
        rootNode = nodes[0]
        namespace = str(rootNode).rpartition(":")[0]
        namespace_base = cmds.namespaceInfo(namespace,baseName=True)
        skeletonName = cmds.namespaceInfo(namespace,parent=True)
        self._SetNamespace(skeletonName)
        
        # SanityCheck() guarantees this will work
        m = cmds.ls(skeletonName+":Markers")
        markers = m[0]

        self._Write( Spaces(1)+"<Skeleton Name=\"" + skeletonName + "\">")
 
        self._Write( Spaces(2)+"<Solver>Global Optimization</Solver>")
        self._Write( Spaces(2)+"<Scale>" + str(self._rootScale)+"</Scale>")

        self._Write( Spaces(2)+"<Segments>")
    
        # Check for special case: the root is really the root with 
        # one child as the translational root (hips/pelvis)
        if self._root_is_reference:
            print(f"Exporting as Reference node.")
            self._ExportReferenceJoint(rootNode,3)
        else:    
            self._ExportRootJoint(rootNode, 3)
        
        self._Write( Spaces(2)+"</Segments>")
          
        self._Write( Spaces(1)+"</Skeleton>")

    #
    # ExportQTMSkeletonFile
    #
    # Top most function for exporting a QTM Skeleton XML file.
    # This is done recursively to handle the  joint hierarchy.
    # Each section has its own function call to export the section.
    #
    # if fd is None then assume we're writing a string for passing
    # back to QTM
    #
    def ExportQTMSkeletonFile(self,fd):

        self._fd = fd
        self._sXML = u""

        if self._fd is None:
            self._Write("  <Skeletons>")
        else:
            self._Write("<QTM_Skeleton_File>")

        self._ExportSkeleton()

        if self._fd is None:
            self._Write("  </Skeletons>")
        else:
            self._Write("</QTM_Skeleton_File>")

        return self._sXML
    
################################################################
#
# End of QExportSolver class definition
#
################################################################


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
        cmds.confirmDialog(title="No Root",message="Please select the root joint to export",button=["OK"], defaultButton="OK")
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
    print ("Found", markers, cmds.nodeType(markers))
    parents = cmds.listRelatives(markers,parent=True)
                
    return True
    
#
# Drag this function to the tool bar for easy access, it should look like this:
#    import QExportSolver
#    reload(QExportSolver)
#    QExportSolver.ExportQTMSkeleton()
#
def ExportQTMSkeleton():
    # make sure the user has selected a joint and that the scene has the right construction    
    bOK = SanityCheck()
    if bOK == True:
        fPath = cmds.fileDialog2(fileFilter="QTM Skeleton (*.xml)",caption="Save QTM Skeleton File", fm=0)
        if fPath is not None:
            fName = fPath[0]
            QES = QExportSolver()
            QES.CheckRootIsReference()
            QES.SetSceneScale()

            #fd = os.open(fName , os.O_RDWR|os.O_CREAT )
            fd = open(fName , 'w' )
            QES.ExportQTMSkeletonFile(fd)
            fd.close()
            print ("Wrote", fName)

def gexXmlSkeleton():
    bOK = SanityCheck()
    if bOK:
        with tempfile.TemporaryFile() as fd:
            QES = QExportSolver()
            QES.SetSceneScale()
            QES.ExportQTMSkeletonFile(fd)
            fd.seek(0)
            skeletonXML = fd.read()
            fd.close()
    if skeletonXML:
        return skeletonXML
    else:
        return None

def PushXMLSkeleton():
    bOK = SanityCheck()
    if bOK:
        QES = QExportSolver()
        QES.SetSceneScale()
        QES.ExportQTMSkeletonFile(None) # No file means to create XML string
        return QES._sXML
    return None
