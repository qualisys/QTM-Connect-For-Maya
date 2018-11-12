import os

from PySide2 import QtWidgets
from PySide2 import QtGui

import maya.cmds as cmds
import maya.api.OpenMaya as om

from mayaui import load_icon
from mayautil import MayaUtil


class SkeletonStreamer:
    def __init__(self, qtmrt, listWidget):
        self._qtm = qtmrt
        self._qtm_settings = None
        self._listWidget = listWidget
        self._unit_conversion = 0.1
        self._saved_poses = {}
        self._in_t_pose = []
        self._skeletons = []

        self._qtm.connectedChanged.connect(self._connected_changed)
        self._connected_changed(self._qtm.connected)

    def _connected_changed(self, connected):
        self._up_axis = cmds.upAxis(q=True, axis=True)

        if connected:
            self._update_ui()
        else:
            self._skeletons = []
            self._listWidget.clear()

    def _packet_received(self, packet):
        _, skeletons = packet.get_skeletons()

        for skeleton in skeletons:
            for joint_id, joint_position, joint_rotation in skeleton:
                transformFn = self._joints[joint_id]["transformFn"]

                if self._up_axis == "y":
                    translation = om.MVector(
                        -joint_position.x * self._unit_conversion,
                        joint_position.z * self._unit_conversion,
                        joint_position.y * self._unit_conversion,
                    )

                    rotation = om.MQuaternion(
                        -joint_rotation.x,
                        joint_rotation.z,
                        joint_rotation.y,
                        joint_rotation.w,
                    )
                else:
                    translation = om.MVector(
                        joint_position.x * self._unit_conversion,
                        joint_position.y * self._unit_conversion,
                        joint_position.z * self._unit_conversion,
                    )

                    rotation = om.MQuaternion(
                        joint_rotation.x,
                        joint_rotation.y,
                        joint_rotation.z,
                        joint_rotation.w,
                    )

                transformFn = self._joints[joint_id]["transformFn"]
                transformFn.setTranslation(translation, om.MSpace.kTransform)
                transformFn.setRotation(
                    rotation.asEulerRotation(), om.MSpace.kTransform
                )

    def _update_ui(self):
        self._listWidget.clear()

        if self._qtm.connected:
            self._qtm_settings = self._qtm.get_settings("skeleton")

        if (
            self._qtm_settings is None
            or self._qtm_settings.get("Skeletons", None) is None
        ):
            return

        self._skeletons = self._qtm_settings["Skeletons"].get("Skeleton", [])
        if type(self._skeletons) != type([]):
            self._skeletons = [self._skeletons]

        for skeleton in self._skeletons:
            color = QtGui.QColor(255, 0, 0)
            icon = load_icon(
                os.path.dirname(os.path.abspath(__file__))
                + "/assets/skeleton_64x64.png",
                color,
            )
            item = QtWidgets.QListWidgetItem(icon, skeleton["@Name"])

            self._listWidget.addItem(item)

    def _assume_t_pose(self, joint):
        transformFn = self._joints[int(joint["@ID"])]["transformFn"]

        if self._up_axis == "y":
            translation = om.MVector(
                -float(joint["Position"]["@X"]) * self._unit_conversion,
                float(joint["Position"]["@Z"]) * self._unit_conversion,
                float(joint["Position"]["@Y"]) * self._unit_conversion,
            )
        else:
            translation = om.MVector(
                float(joint["Position"]["@X"]) * self._unit_conversion,
                float(joint["Position"]["@Y"]) * self._unit_conversion,
                float(joint["Position"]["@Z"]) * self._unit_conversion,
            )

        transformFn.setTranslation(translation, om.MSpace.kTransform)
        transformFn.setRotation(
            om.MEulerRotation(
                float(joint["Rotation"]["@X"]),
                float(joint["Rotation"]["@Y"]),
                float(joint["Rotation"]["@Z"]),
                om.MEulerRotation.kXYZ,
            ),
            om.MSpace.kTransform,
        )

    def _save_pose(self, joint):
        transformFn = self._joints[int(joint["@ID"])]["transformFn"]

        self._saved_poses[int(joint["@ID"])] = {
            "translation": transformFn.translation(om.MSpace.kTransform),
            "rotation": transformFn.rotation(om.MSpace.kTransform),
        }

    def create(self):
        modifier = om.MDagModifier()
        self._joints = {}

        if self._qtm_settings is None and self._qtm.connected:
            self._qtm_settings = self._qtm.get_settings("skeleton")

        if (
            self._qtm_settings is not None
            and self._qtm_settings.get("Skeletons", None) is not None
        ):
            self._skeletons = self._qtm_settings["Skeletons"].get("Skeleton", [])

            if type(self._skeletons) != type([]):
                self._skeletons = [self._skeletons]

            for skeleton in self._skeletons:
                create = True

                for joint in skeleton["Joint"]:
                    joint_name = skeleton["@Name"] + "_" + joint["@Name"]
                    j = MayaUtil.get_node_by_name(joint_name)

                    if j is None:
                        j = modifier.createNode("joint")

                        modifier.renameNode(j, joint_name)
                    else:
                        create = False

                    transformFn = om.MFnTransform(j)

                    self._joints[int(joint["@ID"])] = {
                        "MObject": j,
                        "transformFn": transformFn,
                    }

                    if "@Parent_ID" in joint:
                        modifier.reparentNode(
                            j, self._joints[int(joint["@Parent_ID"])]["MObject"]
                        )

                    if create:
                        self._assume_t_pose(joint)

            modifier.doIt()

    def t_pose(self, skeleton_name):
        for skeleton_definition in self._skeletons:
            if skeleton_definition["@Name"] == skeleton_name:
                for joint in skeleton_definition["Joint"]:
                    self._save_pose(joint)
                    self._assume_t_pose(joint)

                self._in_t_pose.append(skeleton_name)

    def resume_pose(self, skeleton_name):
        for skeleton_definition in self._skeletons:
            if skeleton_definition["@Name"] == skeleton_name:
                for joint in skeleton_definition["Joint"]:
                    if int(joint["@ID"]) in self._saved_poses:
                        transformFn = self._joints[int(joint["@ID"])]["transformFn"]

                        transformFn.setTranslation(
                            self._saved_poses[int(joint["@ID"])]["translation"],
                            om.MSpace.kTransform,
                        )
                        transformFn.setRotation(
                            self._saved_poses[int(joint["@ID"])]["rotation"],
                            om.MSpace.kTransform,
                        )

        if skeleton_name in self._in_t_pose:
            self._in_t_pose.remove(skeleton_name)

    def is_in_t_pose(self, skeleton_name):
        return skeleton_name in self._in_t_pose

