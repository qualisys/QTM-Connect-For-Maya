import xml.etree.ElementTree as ET
import maya.cmds as cmds
import math
import os
from pymel.all import *
import pymel.core.datatypes as dt

#
# Quaternion to Euler angle conversion
# Inputs are strings
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
    

# For indenting to make the printout pretty
def Spaces(level):
    r = ""
    for i in range(0,level):
        r = r + "    "
    return r

################################################################
#
# Class QImportSolver
#
# Handles the traversal of an ElementTree made from a QTM Solver
# XML file and converts it to a Maya scene
#
# sceneScale  - For scene conversion between units
# rootScale   - For scaling the skeleton
# NS          - The main namespace (equals the markerset name in QTM
# MPNS        - The model pose name space which is a child of the
#               namespace
#
################################################################
class QImportSolver:

    def __init__(self):
        self._sceneScale = 1.0
        self._rootScale = 1.0
        self._NS = u":"
        self._MPNS = self._NS+u"ModelPose:"
            
    def _SetNamespace(self, namespace):
        self._NS = namespace+u":"
        self._MPNS = self._NS+u"ModelPose:"
        if not cmds.namespace( exists=namespace ):
            cmds.namespace(add=namespace)
        if not cmds.namespace( exists="ModelPose", parent=namespace ):
            cmds.namespace(add="ModelPose", parent=namespace)
        #print "Namespace = ", self._NS
        #print "Model Pose Namespace = ", self._MPNS
        
    # SetSceneScale()
    #
    # Calculate the conversion factor for converting the current scene units into mm, which QTM requires.
    #     [mm | millimeter | cm | centimeter | m | meter | km | kilometer | in | inch | ft | foot | yd | yard | mi | mile]
    def SetSceneScale(self):
    
        cu = cmds.currentUnit( query=True, linear=True )
        if cu == "cm":
            self._sceneScale = 0.1
        elif cu == "mm":
            self._sceneScale = 1.0
        elif cu == "m":
            self._sceneScale = 0.001
        elif cu == "m":
            self._sceneScale = 0.000001
        elif cu == "ft":
            self._sceneScale = 1.0 / 304.8
        elif cu == "yd":
            self._sceneScale = 1.0 / 914.4
        elif cu == "mi":
            self._sceneScale = 1.0 / 1609300.0
        else:
            self._sceneScale = 1.0

        #print "Scene Scale" , self._sceneScale
 
       

    #
    # Create marker locators information
    #
    # Assume no children of the markers in the XML file.
    # First make the locator a child of the joint since the position data is relative to the joint.
    # Then reparent the locator to the Markers group node. This turns the local offset into a global one.
    # Any markers that have alrady been created are skipped.
    #
    # ParentNode - is the Maya joint to which the markers are attached
    # Segment    - XML reference to the joint, not used here
    # markers    - XML list of markers
    # level      - # of indentations for printing for debugging
    #
    def _ImportMarkers(self, ParentNode, segment, markers, level):
        tag = markers.tag
        for cm in markers:
            if cm.tag == "Marker":
                plainname = cm.attrib["Name"]
                mname = self._NS+plainname
                
                #print Spaces(level), "Marker", mname
 
                # if marker exists don't make a new one, just create attributes for it in the joint.           
                if not cmds.objExists(mname):
                    loc = cmds.spaceLocator(name=mname)
                    cmds.setAttr("%s.overrideEnabled" % mname, 1)
                    cmds.setAttr("%s.overrideColor" % mname, 22)
                
                    cmds.select(ParentNode)
                    #cmds.select(ParentNode, add=True)
                    cmds.parent(loc)
                    cmds.select(loc)
                    cmds.move(0,0,0)
                    cmds.scale(3,3,3)
                    cmds.rotate(0,0,0)
                    bSkip = False
                else:
                    #print "Skip", mname
                    loc = mname
                    bSkip = True

                cmds.addAttr(ParentNode,ln=plainname, defaultValue=1.0)
            
                for ccm in cm:
                    if ccm.tag == "Position":
                        px = float(ccm.attrib["X"]) * self._sceneScale / self._rootScale
                        py = float(ccm.attrib["Y"]) * self._sceneScale / self._rootScale
                        pz = float(ccm.attrib["Z"]) * self._sceneScale / self._rootScale
                        #print Spaces(level+1), "Position", px, py, pz
                    
                        if not bSkip:
                            # Actually make a new marker
                            cmds.select(loc)
                            cmds.move(px,py,pz, ls=True)
                            cmds.select(self._NS+"Markers")
                            cmds.parent(loc)
                    elif ccm.tag == "Weight":
                        w = float(ccm.text)
                        a = str(ParentNode)+'.'+plainname
                        cmds.setAttr(a, w)
                        #print Spaces(level+1), "Weight" , w
    

    def _ImportSolver(self, solver):
        if solver.text == "Global Optimization" :
            #print "GO"
            return True
        else:
            return False
 
    # 
    # ImportSegment
    # 
    # Recursive routine for importing a segment (joint) definition.
    #
    # ParentNode - Maya joint node that is the parent of the new segment to be created  
    # segment    - XML definition of the segment
    # level      - for pretty printing debug statements
    # bIsRoot    - Root is special, skeleton scale information is stashed there
    #     
    def _ImportSegment(self, ParentNode, segment, level,bIsRoot=False):
        tag       = segment.tag
        attrib    = segment.attrib
        name      = self._MPNS+attrib["Name"]

        #print Spaces(level), tag,  name

        #print Spaces(level), attrib
        if ParentNode is not None:
            cmds.select(ParentNode)
        else:
            cmds.select(clear=True)
        jMe = cmds.joint(name = name)
        cmds.select(jMe)
        jMeRadius = jMe+".radius"
        cmds.setAttr(jMeRadius, 1)
        cmds.setAttr("%s.segmentScaleCompensate" % str(jMe), 0)
    
        # stash the root scale in the root joint
        if bIsRoot:
            cmds.setAttr("%s.scaleX" % str(jMe), self._rootScale)
            cmds.setAttr("%s.scaleY" % str(jMe), self._rootScale)
            cmds.setAttr("%s.scaleZ" % str(jMe), self._rootScale)
            #print "Set Root Scale", str(self._rootScale), str(jMe)
        
        for cs in segment:
            if cs.tag == "Segment":
                self._ImportSegment(jMe, cs, level + 1)
            elif cs.tag == "Solver":
                n = str(jMe)
                # Add all the DOF flags and bounds
                cmds.addAttr(n,ln="Solver",at="bool")
                cmds.setAttr(n+ ".Solver", True)
            elif cs.tag == "Markers":
                self._ImportMarkers(jMe, segment, cs, level + 1)
            elif cs.tag == "Transform":
                for ccs in cs:
                    if ccs.tag == "Position":
                        px = float(ccs.attrib["X"]) * self._sceneScale / self._rootScale
                        py = float(ccs.attrib["Y"]) * self._sceneScale / self._rootScale
                        pz = float(ccs.attrib["Z"]) * self._sceneScale / self._rootScale                  
                        #print Spaces(level+1),"Transform Position" , px, py, pz 
                        #cmds.joint(edit=True, position=[px,py,pz]) 
                        cmds.select(jMe)
                        cmds.move(px,py,pz,ls=True)        
                    elif ccs.tag == "Rotation":
                        qx = ccs.attrib["X"]
                        qy = ccs.attrib["Y"]
                        qz = ccs.attrib["Z"]   
                        qw = ccs.attrib["W"]
                        ER = QtoE(qx,qy,qz,qw)
                        #print Spaces(level+1),"Transform Rotation E" , ER[0], ER[1], ER[2]                     
                        #print Spaces(level+1),"Transform Rotation" , qx, qy, qz, qw
                        cmds.select(jMe) 
                        cmds.rotate(ER[0], ER[1],ER[2])  
                             
            elif cs.tag == "DefaultTransform":
                for ccs in cs:
                    if ccs.tag == "Position":
                        px = float(ccs.attrib["X"]) * self._sceneScale / self._rootScale
                        py = float(ccs.attrib["Y"]) * self._sceneScale / self._rootScale
                        pz = float(ccs.attrib["Z"]) * self._sceneScale / self._rootScale                    
                        #print Spaces(level+1),"Default Transform", "Position" , px, py, pz           
                    elif ccs.tag == "Rotation":
                        qx = ccs.attrib["X"]
                        qy = ccs.attrib["Y"]
                        qz = ccs.attrib["Z"]   
                        qw = ccs.attrib["W"]
                        ER = QtoE(qx,qy,qz,qw)                     
                        #print Spaces(level+1),"Default Transform","Rotation" , px, py, pz, pw      
                        # Get the default transform from the Preferred Angle of the joint
                        n = str(jMe)
                        cmds.setAttr("%s.preferredAngleX" % n,ER[0])
                        cmds.setAttr("%s.preferredAngleY" % n,ER[1])
                        cmds.setAttr("%s.preferredAngleZ" % n,ER[2])      
            elif cs.tag == "DegreesOfFreedom":
                #print Spaces(level+1), "DoFs"
                n = str(jMe)
                # Add all the DOF flags and bounds
                cmds.addAttr(n,ln="XRotDoF",at="bool")
                cmds.setAttr(n+ ".XRotDoF", False)
                cmds.addAttr(n,ln="XRotDoF_LowerBound", defaultValue=-360)
                cmds.addAttr(n,ln="XRotDoF_UpperBound", defaultValue=360)
        
                cmds.addAttr(n,ln="YRotDoF",at="bool")
                cmds.setAttr(n+".YRotDoF", False)
                cmds.addAttr(n,ln="YRotDoF_LowerBound", defaultValue=-360)
                cmds.addAttr(n,ln="YRotDoF_UpperBound", defaultValue=360)
        
                cmds.addAttr(n,ln="ZRotDoF",at="bool")
                cmds.setAttr(n+".ZRotDoF", False)
                cmds.addAttr(n,ln="ZRotDoF_LowerBound", defaultValue=-360)
                cmds.addAttr(n,ln="ZRotDoF_UpperBound", defaultValue=360)
        
                cmds.addAttr(n,ln="XTransDoF",at="bool")
                cmds.setAttr(n+ ".XTransDoF", False)
                cmds.addAttr(n,ln="YTransDoF",at="bool")
                cmds.setAttr(n+ ".YTransDoF", False)
                cmds.addAttr(n,ln="ZTransDoF",at="bool")
                cmds.setAttr(n+ ".ZTransDoF", False)
            
                for ccs in cs:
                    if ccs.tag == "RotationX":
                        for cccs in ccs:
                            if cccs.tag == "Constraint":
                                bounded = False
                                lb = -180
                                ub = 180
                                if "LowerBound" in cccs.attrib:
                                    bounded = True
                                    lb = math.degrees(float(cccs.attrib["LowerBound"]))
                                    ub = math.degrees(float(cccs.attrib["UpperBound"]))
                    
                                cmds.setAttr(n+ ".XRotDoF", True)
                                cmds.setAttr(n+".XRotDoF_LowerBound", lb)
                                cmds.setAttr(n+".XRotDoF_UpperBound", ub) 

                            elif cccs.tag == "Couplings":
                                #print ("Found Couplings for "+ n + ":")
                                i = 1
                                for coupling in cccs:
                                    c_coef = float(coupling.attrib["Coefficient"])
                                    c_segment = coupling.attrib["Segment"]
                                    c_coefname = "XRot_CP"+str(i)+"_Coeff"
                                    c_segmentname = "XRot_CP"+str(i)+"_Segment"
                                    print("    Coef="+str(c_coef)+"  Segment: "+str(c_segment))
                                    print("    Coefname="+str(c_coefname)+"  Segmentname: "+str(c_segmentname))
                                    cmds.addAttr(n,ln=c_coefname, defaultValue=c_coef)
                                    cmds.addAttr(n,ln=c_segmentname,dt="string")
                                    cmds.setAttr(n+"."+c_segmentname,c_segment,type="string")
                                    i = i + 1

                            elif cccs.tag == "Goal":
                                goal_value = float(cccs.attrib["Value"])
                                goal_weight = float(cccs.attrib["Weight"])
                                cmds.addAttr(n,ln="XRot_Goal_Value", defaultValue=goal_value)
                                cmds.addAttr(n,ln="XRot_Goal_Weight",defaultValue=goal_weight)

                        #print Spaces(level+2), "RX", bounded, "LowerBound", lb, "UpperBound", ub
                    elif ccs.tag == "RotationY":   
                        for cccs in ccs:
                            if cccs.tag == "Constraint":
                                bounded = False
                                lb = -180
                                ub = 180
                                if "LowerBound" in cccs.attrib:
                                    bounded = True
                                    lb = math.degrees(float(cccs.attrib["LowerBound"]))
                                    ub = math.degrees(float(cccs.attrib["UpperBound"]))
                    
                                cmds.setAttr(n+ ".YRotDoF", True)
                                cmds.setAttr(n+".YRotDoF_LowerBound", lb)
                                cmds.setAttr(n+".YRotDoF_UpperBound", ub) 
                            elif cccs.tag == "Couplings":
                                #print ("Found Couplings for "+ n + ":")
                                i = 1
                                for coupling in cccs:
                                    c_coef = float(coupling.attrib["Coefficient"])
                                    c_segment = coupling.attrib["Segment"]
                                    c_coefname = "YRot_CP"+str(i)+"_Coeff"
                                    c_segmentname = "YRot_CP"+str(i)+"_Segment"
                                    print("    Coef="+str(c_coef)+"  Segment: "+str(c_segment))
                                    print("    Coefname="+str(c_coefname)+"  Segmentname: "+str(c_segmentname))
                                    cmds.addAttr(n,ln=c_coefname, defaultValue=c_coef)
                                    cmds.addAttr(n,ln=c_segmentname,dt="string")
                                    cmds.setAttr(n+"."+c_segmentname,c_segment,type="string")
                                    i = i + 1
                                    
                            elif cccs.tag == "Goal":
                                goal_value = float(cccs.attrib["Value"])
                                goal_weight = float(cccs.attrib["Weight"])
                                cmds.addAttr(n,ln="YRot_Goal_Value", defaultValue=goal_value)
                                cmds.addAttr(n,ln="YRot_Goal_Weight",defaultValue=goal_weight)
                    
                        #print Spaces(level+2), "RY", bounded, "LowerBound", lb, "UpperBound", ub                  
                    elif ccs.tag == "RotationZ":   
                        for cccs in ccs:
                            if cccs.tag == "Constraint":
                                bounded = False
                                lb = -180
                                ub = 180
                                if "LowerBound" in cccs.attrib:
                                    bounded = True
                                    lb = math.degrees(float(cccs.attrib["LowerBound"]))
                                    ub = math.degrees(float(cccs.attrib["UpperBound"]))
                    
                                cmds.setAttr(n+ ".ZRotDoF", True)
                                cmds.setAttr(n+".ZRotDoF_LowerBound", lb)
                                cmds.setAttr(n+".ZRotDoF_UpperBound", ub) 
                            elif cccs.tag == "Couplings":
                                #print ("Found Couplings for "+ n + ":")
                                i = 1
                                for coupling in cccs:
                                    c_coef = float(coupling.attrib["Coefficient"])
                                    c_segment = coupling.attrib["Segment"]
                                    c_coefname = "ZRot_CP"+str(i)+"_Coeff"
                                    c_segmentname = "ZRot_CP"+str(i)+"_Segment"
                                    print("    Coef="+str(c_coef)+"  Segment: "+str(c_segment))
                                    print("    Coefname="+str(c_coefname)+"  Segmentname: "+str(c_segmentname))
                                    cmds.addAttr(n,ln=c_coefname, defaultValue=c_coef)
                                    cmds.addAttr(n,ln=c_segmentname,dt="string")
                                    cmds.setAttr(n+"."+c_segmentname,c_segment,type="string")
                                    i = i + 1
                            elif cccs.tag == "Goal":
                                goal_value = float(cccs.attrib["Value"])
                                goal_weight = float(cccs.attrib["Weight"])
                                cmds.addAttr(n,ln="ZRot_Goal_Value", defaultValue=goal_value)
                                cmds.addAttr(n,ln="ZRot_Goal_Weight",defaultValue=goal_weight)

                        #print Spaces(level+2), "RZ", bounded, "LowerBound", lb, "UpperBound", ub
                    elif ccs.tag == "TranslationX":
                        cmds.setAttr(n+ ".XTransDoF", True)
                        #print Spaces(level+2), "PX"
                        dofX = True
                    elif ccs.tag == "TranslationY":  
                        cmds.setAttr(n+ ".YTransDoF", True) 
                        #print Spaces(level+2), "PY"   
                        dofY = True
                    elif ccs.tag == "TranslationZ": 
                        cmds.setAttr(n+ ".ZTransDoF", True)  
                        #print Spaces(level+2), "PZ"
                        dofZ = True
            elif cs.tag == "Endpoint":  
                if "X" in cs.attrib:
                    px = float(cs.attrib["X"]) * self._sceneScale / self._rootScale
                    py = float(cs.attrib["Y"]) * self._sceneScale / self._rootScale
                    pz = float(cs.attrib["Z"]) * self._sceneScale / self._rootScale
                    #print Spaces(level+1), "Endpoint", "X", px, "Y", py, "Z", pz
                    EPName = name + "_end"
                    cmds.select(jMe)
                    jEP = cmds.joint(name=EPName)
                    cmds.select(jEP)
                    cmds.move(px,py,pz,ls=True)             
                else:
                    #print Spaces(level+1), "Endpoint"
                    cmds.select(ParentNode)
            elif cs.tag == "RigidBodies":  
                #print Spaces(level+1), "RigidBodies"
                cmds.select(ParentNode)    
               
    #
    # This is the start of the segments hierarchy
    #      
    # There is really only supposed to be one "Segment" tag
    #  
    # gGroupName  - Maya group node that is the scene root
    # segments    - The XML list of segments
    #
    #def _ImportSegments(self, gGroupName, segments):
    def _ImportSegments(self, segments):
        tag    = segments.tag
        attrib = segments.attrib

        for c in segments:
            ctag = c.tag
            if c.tag == "Segment":
                self._ImportSegment(None,c,0,True)
        
    #
    # At the start of the skeleton definition, this is like the
    # group node, segments start below
    # 
    # Skeleton - The XML node that must work out to have a "Skeleton" tag
    #
    # Also looks for the Solver tag that must exist.
    # Finally looks for the "Skeleton" tag which is the start of the
    # joint hierarchy.
    #
    # The first two Maya nodes are created.  The first is the root of
    # the scene, the
    # name is the one that matches the markerset
    # prefix in QTMfor holding the markers.  The second is the child
    # of the first and
    # is the group node for all the markers.
    # This is not passed along, subroutines will find the Maya node
    # themselves.  Kind of like a global variable.
    #       
    def _ImportSkeleton(self, skeleton):
        tag    = skeleton.tag
        attrib = skeleton.attrib
        # print tag
        #print attrib
    
        name = attrib["Name"]
        if tag == "Skeleton":
            #print "Yes!! A Skeleton named " + name
            self._SetNamespace(name)
            
            #gGroupName = cmds.group( em=True,name=name)
            gMarkers = cmds.group(em=True,name=self._NS+u"Markers")
            for child in skeleton:
                # print child.tag
                if child.tag == "Solver":
                    # Nothing is really done with this, could be used for a sanity check later.
                    if self._ImportSolver(child):
                        #print "A Globally Optimized Solver"
                        GOS = True 
                    else:
                        #print "Not a GO"
                        GOS = False
                elif child.tag == "Scale":
                    self._rootScale = float(child.text)
                    #print "Root Scale", self._rootScale
                elif child.tag == "Segments":
                    #print "Do Segments"
                    self._ImportSegments(child) 
                else:
                    print ("Unrecognized Skeleton child " + child.tag   )         
        else:
            print ("Expected skeleton tag.  Found <", tag, ">")
        
  
    #
    # this is where the XML traversing starts
    #
    # root  - The root of the XML tree that was read from the file.
    #  
    def ImportQTMSkeletonFile(self,root):
        tag = root.tag
    
        if tag == "QTM_Skeleton_File":
            #print "Yes!! A Skeleton file"
            # will be only one child
            for child in root :
                self._ImportSkeleton(child)
        elif tag == "Skeletons":
            #print "Yes!! A Skeleton Stream"
            # will be only one child
            for child in root :
                self._ImportSkeleton(child)
            
        else:
            print ("NO!  <", tag, "> is Not a skeleton definition")

################################################################
#
# End of QImportSolver Class definition
#
################################################################

#
# ImportQTMSkeleton
#
# Where it all starts.  Get the file to load and do it!
# Drag this function to the tool bar for easy access
#
# The code in the shelf command should be:
#    import QImportSolver
#    reload(QImportSolver)
#    QImportSolver.ImportQTMSkeleton()
#
# NOTE:  This routine completely NUKES the current Maya scene, use with caution.
#
def ImportQTMSkeleton():
    
    fPath = cmds.fileDialog2(fileFilter="QTM Skeleton (*.xml)",caption="Open QTM Skeleton File", fm=1)
    if fPath is not None:
        fName = fPath[0]
        print (fName)
        dom = ET.parse(fName)
        
        if dom is not None:
            root = dom.getroot()             
            QIS = QImportSolver()
            QIS.SetSceneScale()

            # Start a new scene in Maya
            #cmds.file(new=True,f=True)
            cmds.currentUnit( linear='cm' )

            QIS.ImportQTMSkeletonFile(root)
  

