import os

from PySide2 import QtWidgets
from PySide2 import QtGui

import maya.cmds as cmds
import maya.api.OpenMaya as om

from mayaui import load_icon
from mayautil import MayaUtil

class SkeletonStreamer:
    def __init__(self, qtmrt, listWidget):
        self._qtm             = qtmrt
        self._up_axis         = cmds.upAxis(q=True, axis=True)
        self._qtm_settings    = None
        self._listWidget      = listWidget
        self._unit_conversion = 0.1

        self._qtm.connectedChanged.connect(self._connected_changed)

    def _connected_changed(self, connected):
        if connected:
            self._update_ui()
            self.create()
        else:
            self._listWidget.clear()

    def _packet_received(self, packet):
        info, skeletons = packet.get_skeleton()
        
        for skeleton in skeletons:
            for joint in skeleton:
                joint_id = joint[0].id
                joint_position = joint[1]
                joint_rotation = joint[2]
                transformFn = self._joints[joint_id]['transformFn']
                
                if self._up_axis == 'y':
                    translation = om.MVector(
                        -joint_position.x * self._unit_conversion,
                        joint_position.z * self._unit_conversion,
                        joint_position.y * self._unit_conversion,
                    )

                    rotation = om.MQuaternion(-joint_rotation.x, joint_rotation.z, joint_rotation.y, joint_rotation.w)
                else:
                    translation = om.MVector(
                        joint_position.x * self._unit_conversion,
                        joint_position.y * self._unit_conversion,
                        joint_position.z * self._unit_conversion,
                    )

                    rotation = om.MQuaternion(joint_rotation.x, joint_rotation.y, joint_rotation.z, joint_rotation.w)

                transformFn = self._joints[joint_id]['transformFn']
                transformFn.setTranslation(translation, om.MSpace.kTransform)
                transformFn.setRotation(rotation.asEulerRotation(), om.MSpace.kTransform)

    def _update_ui(self):
        self._listWidget.clear()

        if self._qtm.connected:
            self._qtm_settings = self._qtm.get_settings('skeleton')

        for i, skeleton in enumerate(self._qtm_settings['Skeletons']['Skeleton']):
            color = QtGui.QColor(255, 0, 0)
            icon  = load_icon(os.path.dirname(os.path.abspath(__file__)) + '/assets/marker_64x32.png', color)
            item  = QtWidgets.QListWidgetItem(icon, skeleton['@Name'])

            self._listWidget.addItem(item)

    def create(self):
        modifier = om.MDagModifier()
        self._joints = {}

        if self._qtm_settings is None and self._qtm.connected:
            self._qtm_settings = self._qtm.get_settings('skeleton')

        if self._qtm_settings is not None:
            for m, skeleton in enumerate(self._qtm_settings['Skeletons']['Skeleton']):
                for n, joint in enumerate(skeleton['Joint']):
                    joint_name = skeleton['@Name'] + '_' + joint['@Name']
                    j = MayaUtil.get_node_by_name(joint_name)

                    if j is None:
                        j = modifier.createNode('joint')

                        modifier.renameNode(j, joint_name)

                    transformFn = om.MFnTransform(j)
                    self._joints[int(joint['@ID'])] = {
                        'MObject': j,
                        'transformFn': transformFn
                    }
                    
                    if '@Parent_ID' in joint:
                        modifier.reparentNode(j, self._joints[int(joint['@Parent_ID'])]['MObject'])

                    if self._up_axis == 'y':
                        translation = om.MVector(
                            -float(joint['Position']['@X']) * self._unit_conversion,
                            float(joint['Position']['@Z']) * self._unit_conversion,
                            float(joint['Position']['@Y']) * self._unit_conversion,
                        )
                    else:
                        translation = om.MVector(
                            float(joint['Position']['@X']) * self._unit_conversion,
                            float(joint['Position']['@Y']) * self._unit_conversion,
                            float(joint['Position']['@Z']) * self._unit_conversion,
                        )

                    transformFn.setTranslation(translation, om.MSpace.kTransform)
                    transformFn.setRotation(om.MEulerRotation(float(joint['Rotation']['@X']), float(joint['Rotation']['@Y']), float(joint['Rotation']['@Z']), om.MEulerRotation.kXYZ), om.MSpace.kTransform)

            modifier.doIt()