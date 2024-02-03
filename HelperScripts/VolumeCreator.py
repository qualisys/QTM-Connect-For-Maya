"""
VolumeCreator - Generate a volume that represents the tracking coverage 
of the capture space.  Each cube of the volume is evaluated to determine the number
of cameras that see it, but also from which direction, so that a cube is displayed only
if it is seen by a minimum number of cameras from each of all four sides: +-X and +-Z.  
For now no evaluation is done for whether or not cameras see from above or below the 
location in space.

To Use:
  You must create a locator called "Start" that denotes the starting location of the volume.
  This location will be one corner of the volume.  The volume will grow in positive X and
  positive Y from this spot.

  The cameras must all have the name "Camera*" where the * is the rest of the name. Be sure that
  the cameras don't have scales applied to them.  They can be under a group node. You must also select
  all cameras before running the script, this way you can have cameras that can be excluded from 
  the calculations.

  The first time the script is run it will create attributes in the Start locator for 
  controlling the dimensions of the volume created by the script.
    X Res - THe number of cubes in the X dimension
    Y Res - The number of cubes in the Y direction
    Z Res - The number of (vertical) cubes in the Z direction
    Cameras - The number of cameras that must see each of the 4 sides of the cube (not top or bottom) to be counted
    Size - The dimension of each cube (in cm, so 100 is a meter)

When you run the script it will create a "gVolume" group node for the cubes to grouped under (NOTE: at the moment
Maya gives a wierd error when making the cubes a child of this node, the output of the error message causes the script
to get VERY slow), so for now they aren't automatically grouped under the group node.

All cubes of the volume will be created, but the ones that are not "counted" have their display turned off.
"""

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import math
import numpy as np

# Find if object located within camera frustum
# Usage:
#   from obj_in_frust import in_frustum
#   in_frustum('camera1', 'pCube1')

class Plane(object):
    def __init__(self, normalisedVector):
        # OpenMaya.MVector.__init__()
        self.vector= normalisedVector
        self.distance= 0.0

    def relativeToPlane(self, point):
        # Converting the point as a vector from the origin to its position
        pointVec= OpenMaya.MVector( point.x, point.y, point.z )
        val= (self.vector * pointVec) + self.distance

        if (val > 0.0):
            return 1  # In front
        elif (val < 0.0):
            return -1  # Behind

        return 0  # On the plane

class Frustum(object):
    def __init__(self, cameraName):
        # Initialising selected transforms into its associated dagPaths
        selectionList= OpenMaya.MSelectionList()
        objDagPath= OpenMaya.MDagPath()
        selectionList.add( cameraName )
        selectionList.getDagPath(0, objDagPath)
        self.camera= OpenMaya.MFnCamera(objDagPath)

        self.nearClip = self.camera.nearClippingPlane()
        self.farClip =  self.camera.farClippingPlane()
        self.aspectRatio= self.camera.aspectRatio()

        left_util= OpenMaya.MScriptUtil()
        left_util.createFromDouble( 0.0 )
        ptr0= left_util.asDoublePtr()

        right_util= OpenMaya.MScriptUtil()
        right_util.createFromDouble( 0.0 )
        ptr1= right_util.asDoublePtr()

        bot_util= OpenMaya.MScriptUtil()
        bot_util.createFromDouble( 0.0 )
        ptr2= bot_util.asDoublePtr()

        top_util= OpenMaya.MScriptUtil()
        top_util.createFromDouble( 0.0 )
        ptr3= top_util.asDoublePtr()

        stat= self.camera.getViewingFrustum(self.aspectRatio, ptr0, ptr1, ptr2, ptr3, False, True)

        planes= []

        left= left_util.getDoubleArrayItem(ptr0, 0)
        right= right_util.getDoubleArrayItem(ptr1, 0)
        bottom= bot_util.getDoubleArrayItem(ptr2, 0)
        top = top_util.getDoubleArrayItem(ptr3, 0)

        ## planeA = right plane
        a= OpenMaya.MVector(right, top, -self.nearClip)
        b= OpenMaya.MVector(right, bottom, -self.nearClip)
        c= (a ^ b).normal() ## normal of plane = cross product of vectors a and b
        planeA = Plane(c)
        planes.append(planeA)

        ## planeB = left plane
        a = OpenMaya.MVector(left, bottom, -self.nearClip)
        b = OpenMaya.MVector(left, top, -self.nearClip)
        c= (a ^ b).normal()
        planeB= Plane( c )
        planes.append( planeB )

        ##planeC = bottom plane
        a = OpenMaya.MVector(right, bottom, -self.nearClip)
        b = OpenMaya.MVector(left, bottom, -self.nearClip)
        c= (a ^ b).normal()
        planeC= Plane( c )
        planes.append( planeC )

        ##planeD = top plane
        a = OpenMaya.MVector(left, top, -self.nearClip)
        b = OpenMaya.MVector(right, top, -self.nearClip)
        c= (a ^ b).normal()
        planeD= Plane( c )
        planes.append( planeD )

        # planeE = far plane
        c = OpenMaya.MVector(0, 0, 1)
        planeE= Plane( c )
        planeE.distance= self.farClip
        planes.append( planeE )

        # planeF = near plane
        c = OpenMaya.MVector(0, 0, -1)
        planeF= Plane( c )
        planeF.distance= self.nearClip
        planes.append( planeF )

        self.planes = planes
        self.numPlanes = 6

    def relativeToFrustum(self, pointsArray):
        numInside= 0
        numPoints= len( pointsArray )

        for j in range( 0, 6 ):
          numBehindThisPlane= 0

          for i in range( 0, numPoints ):
            if (self.planes[j].relativeToPlane(pointsArray[i]) == -1):  # Behind
                numBehindThisPlane += 1
            if numBehindThisPlane == numPoints:
                ##all points were behind the same plane
                return False
            elif (numBehindThisPlane==0):
                numInside += 1

        if (numInside == self.numPlanes):
            return True  # Inside
        return True  # Intersect

def normalize(n):
    l = np.linalg.norm(n)
    return n/l
def direction(v):
    x = abs(v[0])
    y = abs(v[1])
    if v[0] > 0 and x > y:
        return "PX"
    if v[0] < 0 and x > y:
        return "NX"
    if v[1] > 0 and y > x:
        return "PY"
    if v[1] < 0 and y > x:
        return "NY"
    print(f"Direction: shouldn't be here.")
    return None

# Cache the cameras
Cameras = {}

def in_frustum(cameraName, objectName):
    """
    returns: True if within the frustum of False if not
    """
    if cameraName in Cameras:
        camInvWorldMtx = Cameras[cameraName]['camInvWorldMtx']
        fnCam = Cameras[cameraName]['fnCam']
        camLoc = Cameras[cameraName]['camLoc']
    else:
        selectionList = OpenMaya.MSelectionList()
        camDagPath = OpenMaya.MDagPath()
        selectionList.add( cameraName )
        selectionList.getDagPath(0, camDagPath)
        cameraDagPath = OpenMaya.MFnCamera( camDagPath )
        camInvWorldMtx = camDagPath.inclusiveMatrixInverse()
        M = OpenMaya.MTransformationMatrix(camInvWorldMtx)
        translation = M.translation(OpenMaya.MSpace.kObject)        
        camLoc = np.array([-translation[0], -translation[1], -translation[2]])
        fnCam = Frustum(cameraName)
        Cameras[cameraName] = {"camInvWorldMtx": camInvWorldMtx, "fnCam": fnCam, "camLoc": camLoc}
        
    points = []

    # For node inobjectList
    selectionList = OpenMaya.MSelectionList()
    objDagPath = OpenMaya.MDagPath()
    selectionList.add(objectName)
    selectionList.getDagPath( 0, objDagPath )

    fnDag = OpenMaya.MFnDagNode(objDagPath)
    obj = objDagPath.node()

    dWorldMtx = objDagPath.exclusiveMatrix()
    bbox = fnDag.boundingBox()

    minx = bbox.min().x
    miny = bbox.min().y
    minz = bbox.min().z
    maxx = bbox.max().x
    maxy = bbox.max().y
    maxz = bbox.max().z

    # Getting points relative to the cameras transmformation matrix
    points.append( bbox.min() * dWorldMtx * camInvWorldMtx )
    points.append( OpenMaya.MPoint(maxx, miny, minz) * dWorldMtx * camInvWorldMtx )
    points.append( OpenMaya.MPoint(maxx, miny, maxz) * dWorldMtx * camInvWorldMtx )
    points.append( OpenMaya.MPoint(minx, miny, maxz) * dWorldMtx * camInvWorldMtx )
    points.append( OpenMaya.MPoint(minx, maxy, minz) * dWorldMtx * camInvWorldMtx )
    points.append( OpenMaya.MPoint(maxx, maxy, minz) * dWorldMtx * camInvWorldMtx )
    points.append( bbox.max() * dWorldMtx * camInvWorldMtx )
    points.append( OpenMaya.MPoint(minx, maxy, maxz) * dWorldMtx * camInvWorldMtx )

    if not fnCam.relativeToFrustum(points):
        return None
    M = OpenMaya.MTransformationMatrix(objDagPath.inclusiveMatrix())
    translation = M.translation(OpenMaya.MSpace.kObject)        
    objLoc = np.array([translation[0], translation[1], translation[2]])
    v = normalize(camLoc-objLoc)
    # print(f"camLoc {camLoc}")
    # print(f"objLoc {objLoc}")
    # print(f"directional vector {v}")

    return direction(v)



# Some global variables, after the first run of this script 
# they can be set in the Extra Attributes section of the 
# "Start" locator
size = 20
cameraList = cmds.ls('Camera*',selection=True, ca=True)
# print(f"Cameras to be evaluated:\n{cameraList}")
cameras_to_see = 4
x = 5
y = 5
z = 2
VolumeLayers = []

def UpdateVariables():
    global x
    global y
    global z
    global cameras_to_see
    global size
    global VolumeLayers

    startLocation = cmds.ls("Start")[0]
    bHasAttributes = cmds.attributeQuery("X_res",node=startLocation, exists=True)
    if not bHasAttributes:
        cmds.addAttr(startLocation, ln="X_res", defaultValue=x, at="short")
        cmds.addAttr(startLocation, ln="Y_res", defaultValue=y, at="short")
        cmds.addAttr(startLocation, ln="Z_res", defaultValue=z, at="short")
        cmds.addAttr(startLocation, ln="CamerasToSee", defaultValue=cameras_to_see, at="short")
        cmds.addAttr(startLocation, ln="Size", defaultValue=size, at="short")
    else:
        x = cmds.getAttr(f"{startLocation}.X_res")
        y = cmds.getAttr(f"{startLocation}.Y_res")
        z = cmds.getAttr(f"{startLocation}.Z_res")
        cameras_to_see = cmds.getAttr(f"{startLocation}.CamerasToSee")
        size = cmds.getAttr(f"{startLocation}.Size")
    Volume = cmds.ls("gVolume")
    notVolume = cmds.ls("gNotVolume")
    if not Volume or len(Volume) == 0:
        print(f"Making Volume group node.")
        Volume = cmds.group(em=True, name="gVolume")
        notVolume = cmds.group(em=True, name="gNotVolume")
        borderVolume = cmds.group(em=True, name="gBorderVolume")

    for k in range(z):
        gName = f"VolumeLevel{k}"
        VolumeLayer = cmds.group(em=True, name=gName)
        cmds.select(Volume)
        cmds.parent(VolumeLayer)
        VolumeLayers.append(VolumeLayer)

    print(f"Made volume layers: {VolumeLayers}")

def all_seen(seenByCameras):
    for D in seenByCameras:
        if seenByCameras[D] < cameras_to_see:
            return False
    return True
def all_unseen(seenByCameras):
    """
    If less than 2 sides are seen
    """
    count = 0
    for D in seenByCameras:
        if seenByCameras[D] >= cameras_to_see:
            count += 1
    return (count < 3)

def getSGfromShader(shader=None):
    if shader:
        if cmds.objExists(shader):
            sgq = cmds.listConnections(shader, d=True, et=True, t='shadingEngine')
            if sgq:
                return sgq[0]
    return None

def assignObjectListToShader(objList=None, shader=None):
    """
    Assign the shader to the object list
    arguments:
        objList: list of objects or faces
    """
    # assign selection to the shader
    shaderSG = getSGfromShader(shader)
    if objList:
        if shaderSG:
            cmds.sets(objList, e=True, forceElement=shaderSG)
        else:
            print('The provided shader didn\'t returned a shaderSG')
    else:
        print('Please select one or more objects')

def assignSelectionToShader(shader=None):
    sel = cmds.ls(sl=True, l=True)
    if sel:
        assignObjectListToShader(sel, shader)

# assignSelectionToShader('lambert2')
def colorizeNotVolumeCube(cube, seenByCameras):
    cmds.select([f"{cube}.f[1]"])
    if seenByCameras["PY"] >= cameras_to_see:
        assignSelectionToShader("mNotVolumeGreen")
    elif seenByCameras["PY"] == 0:
        assignSelectionToShader("mNotVolumeRed")
    else:
        assignSelectionToShader("mNotVolumeYellow")
    cmds.select([f"{cube}.f[3]"])
    if seenByCameras["NY"] >= cameras_to_see:
        assignSelectionToShader("mNotVolumeGreen")
    elif seenByCameras["NY"] == 0:
        assignSelectionToShader("mNotVolumeRed")
    else:
        assignSelectionToShader("mNotVolumeYellow")
    cmds.select([f"{cube}.f[4]"])
    if seenByCameras["PX"] >= cameras_to_see:
        assignSelectionToShader("mNotVolumeGreen")
    elif seenByCameras["PX"] == 0:
        assignSelectionToShader("mNotVolumeRed")
    else:
        assignSelectionToShader("mNotVolumeYellow")
    cmds.select([f"{cube}.f[5]"])
    if seenByCameras["NX"] >= cameras_to_see:
        assignSelectionToShader("mNotVolumeGreen")
    elif seenByCameras["NX"] == 0:
        assignSelectionToShader("mNotVolumeRed")
    else:
        assignSelectionToShader("mNotVolumeYellow")
    cmds.select([f"{cube}.f[0]", f"{cube}.f[2]"])
    assignSelectionToShader("mNotVolumeClear")


def CreateVolume():
    total=x*y*z
    breakLoops = False
    startLocation = cmds.ls("Start")
    startLocation = startLocation[0]
    Volume = cmds.ls("gVolume")[0]
    notVolume = cmds.ls("gNotVolume")[0]
    borderVolume = cmds.ls("gBorderVolume")[0]
    cmds.progressWindow(isInterruptable=1, min=0, max=total, t= 'Creating volume')
    print(f"VolumeLayers: {VolumeLayers}")
    for i in range(x):
        if breakLoops:
            break
        for j in range(y):
            if breakLoops:
                break
            for k in range(z):
                if cmds.progressWindow(query=1, isCancelled=1):
                    breakLoops=True
                    break
                cmds.progressWindow(edit=True,s=1)
    #            res = cmds.polySphere(n='mySphere', sx=10, sy=10)

                res = cmds.polyCube(w=size,h=size,d=size)
                # cmds.select(Volume)
                # cmds.parent(res)
                cmds.select(res)
                cmds.move(cmds.getAttr(startLocation+".translateX"),cmds.getAttr(startLocation+".translateY"),cmds.getAttr(startLocation+".translateZ"),res)
                cmds.move(i*size,j*size,k*size,res,r=True)
                cmds.refresh()
                seenByCameras = {"PX":0, "NX": 0, "PY": 0, "NY": 0 }
                is_seen = False

                # print(f"cameraList length is {len(cameraList)}")
                for cam in cameraList:
                    #print(cam)
                    #print(res)
                    D = in_frustum(cam,res[0])
                    # print(f"D: {D}")
                    if D is not None:
                        seenByCameras[D] += 1
                        # print(f"seenBy: {seenByCameras}")
                    if all_seen(seenByCameras):
                        is_seen = True
                        break
                    # if(seenByCameras >= cameras_to_see):
                        # break
                if(not is_seen):
                    # cmds.hide(res)
                    # cmds.delete(res)
                    if all_unseen(seenByCameras):
                        cmds.select(notVolume)
                        cmds.parent(res[0])
                    else:
                        cmds.select(borderVolume)
                        cmds.parent(res[0])
                        colorizeNotVolumeCube(res[0], seenByCameras)
                else:
                    cmds.select(VolumeLayers[k])
                    cmds.parent(res[0])

    cmds.progressWindow(endProgress=1)
    cmds.hide(notVolume)

UpdateVariables()
CreateVolume()
