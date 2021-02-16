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
        self._modifier = None

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

        # once = True
        
        for skeleton_index, skeleton in enumerate(skeletons):

            for segment_id, segment_position, segment_rotation in skeleton:
                if self._up_axis == "y":
                    translation = om.MVector(
                        -segment_position.x * self._unit_conversion,
                        segment_position.z * self._unit_conversion,
                        segment_position.y * self._unit_conversion,
                    )

                    rotation = om.MQuaternion(
                        -segment_rotation.x,
                        segment_rotation.z,
                        segment_rotation.y,
                        segment_rotation.w,
                    )
                else:
                    translation = om.MVector(
                        segment_position.x * self._unit_conversion,
                        segment_position.y * self._unit_conversion,
                        segment_position.z * self._unit_conversion,
                    )

                    rotation = om.MQuaternion(
                        segment_rotation.x,
                        segment_rotation.y,
                        segment_rotation.z,
                        segment_rotation.w,
                    )
                ## Debug
                # if once :
                #     n = self._segments[skeleton_index][segment_id]["@Name"]
                #     print ("Skeleton ", n ,"First Q: ",
                #         segment_rotation.x,
                #         segment_rotation.y,
                #         segment_rotation.z,
                #         segment_rotation.w)
                #    once = False

                transformFn = self._segments[skeleton_index][segment_id]["transformFn"]
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

    def _assume_t_pose(self, skeleton_index, segment):
        transformFn = self._segments[skeleton_index][int(segment["@ID"])]["transformFn"]

        if self._up_axis == "y":
            translation = om.MVector(
                -float(segment["DefaultTransform"]["Position"]["@X"]) * self._unit_conversion,
                float(segment["DefaultTransform"]["Position"]["@Z"]) * self._unit_conversion,
                float(segment["DefaultTransform"]["Position"]["@Y"]) * self._unit_conversion,
            )
            rotation = om.MQuaternion(
                -float(segment["DefaultTransform"]["Rotation"]["@X"]),
                float(segment["DefaultTransform"]["Rotation"]["@Z"]),
                float(segment["DefaultTransform"]["Rotation"]["@Y"]),
                float(segment["DefaultTransform"]["Rotation"]["@W"]),
            )
        else:
            translation = om.MVector(
                float(segment["DefaultTransform"]["Position"]["@X"]) * self._unit_conversion,
                float(segment["DefaultTransform"]["Position"]["@Y"]) * self._unit_conversion,
                float(segment["DefaultTransform"]["Position"]["@Z"]) * self._unit_conversion,
            )
            rotation = om.MQuaternion(
                float(segment["DefaultTransform"]["Rotation"]["@X"]),
                float(segment["DefaultTransform"]["Rotation"]["@Y"]),
                float(segment["DefaultTransform"]["Rotation"]["@Z"]),
                float(segment["DefaultTransform"]["Rotation"]["@W"]),
            )

        transformFn.setTranslation(translation, om.MSpace.kTransform)
        transformFn.setRotation(rotation.asEulerRotation(), om.MSpace.kTransform)

    def _save_pose(self, skeleton_index, segment):
        transformFn = self._segments[skeleton_index][int(segment["@ID"])]["transformFn"]
        segment_id = int(segment["@ID"])

        if skeleton_index not in self._saved_poses:
            self._saved_poses[skeleton_index] = {}

        self._saved_poses[skeleton_index][segment_id] = {
            "translation": transformFn.translation(om.MSpace.kTransform),
            "rotation": transformFn.rotation(om.MSpace.kTransform),
        }

    def create(self):
        self._segments = []

        if self._modifier is None:
            self._modifier = om.MDagModifier()

        if self._qtm_settings is None and self._qtm.connected:
            self._qtm_settings = self._qtm.get_settings("skeleton")

        if (
            self._qtm_settings is not None
            and self._qtm_settings.get("Skeletons", None) is not None
        ):
            self._skeletons = self._qtm_settings["Skeletons"].get("Skeleton", [])

            if type(self._skeletons) != type([]):
                self._skeletons = [self._skeletons]

            for skeleton_index, skeleton in enumerate(self._skeletons):
                if not cmds.namespace( exists=skeleton["@Name"] ):
                    cmds.namespace( add=skeleton["@Name"] )
                self._segments.append({})

                self.add_segment(skeleton_index, skeleton["Segments"]["Segment"], None)

            self._modifier.doIt()

    def add_segment(self, skeleton_index, segment, parent_id):
        segment_name = self._skeletons[skeleton_index]["@Name"] + ":" + segment["@Name"]
        create = True
        j = MayaUtil.get_node_by_name(segment_name)

        if j is None:
            j = self._modifier.createNode("joint")

            self._modifier.renameNode(j, segment_name)
        else:
            create = False

        transformFn = om.MFnTransform(j)

        self._segments[skeleton_index][int(segment["@ID"])] = segment
        self._segments[skeleton_index][int(segment["@ID"])]["MObject"] = j
        self._segments[skeleton_index][int(segment["@ID"])]["transformFn"] = transformFn

        if parent_id is not None:
            self._modifier.reparentNode(
                j, self._segments[skeleton_index][int(parent_id)]["MObject"]
            )

        if create:
            self._assume_t_pose(skeleton_index, segment)

        # Add child segments.
        if "Segment" in segment:
            if type(segment["Segment"]) is list:
                for s in segment["Segment"]:
                    self.add_segment(skeleton_index, s, segment["@ID"])
            else:
                self.add_segment(skeleton_index, segment["Segment"], segment["@ID"])

    def t_pose(self, skeleton_name):
        for skeleton_index, skeleton_definition in enumerate(self._skeletons):
            if skeleton_definition["@Name"] == skeleton_name:
                for segment_id, segment in self._segments[skeleton_index].iteritems():
                    self._save_pose(skeleton_index, segment)
                    self._assume_t_pose(skeleton_index, segment)

                self._in_t_pose.append(skeleton_name)

    def resume_pose(self, skeleton_name):
        for skeleton_index, skeleton_definition in enumerate(self._skeletons):
            if skeleton_definition["@Name"] == skeleton_name:
                for segment_id, segment in self._segments[skeleton_index].iteritems():
                    if skeleton_index in self._saved_poses and int(segment_id) in self._saved_poses[skeleton_index]:
                        transformFn = self._segments[skeleton_index][int(segment_id)]["transformFn"]

                        transformFn.setTranslation(
                            self._saved_poses[skeleton_index][int(segment_id)]["translation"],
                            om.MSpace.kTransform,
                        )
                        transformFn.setRotation(
                            self._saved_poses[skeleton_index][int(segment_id)]["rotation"],
                            om.MSpace.kTransform,
                        )

        if skeleton_name in self._in_t_pose:
            self._in_t_pose.remove(skeleton_name)

    def is_in_t_pose(self, skeleton_name):
        return skeleton_name in self._in_t_pose

