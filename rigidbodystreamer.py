import hashlib, os

from PySide2 import QtGui
from PySide2 import QtWidgets

import maya.cmds as cmds
import maya.api.OpenMaya as om
from maya.api.OpenMaya import MMatrix, MTransformationMatrix

from mayaui import load_icon
from mayautil import MayaUtil


class RigidBodyStreamer:
    def __init__(self, qtmrt, listWidget):
        self._qtm = qtmrt
        self._listWidget = listWidget
        self._bodies = None
        self._unit_conversion = 0.1

        self._qtm.connectedChanged.connect(self._connected_changed)
        self._connected_changed(self._qtm.connected)

    def _connected_changed(self, connected):
        self._up_axis = cmds.upAxis(q=True, axis=True)

        if connected:
            self._init()
            self._update_ui()
        else:
            self._bodies = None
            self._listWidget.clear()

    def _packet_received(self, packet):
        _, bodies = packet.get_6d()

        for i, body in enumerate(bodies):
            (body_position, body_rotation) = body
            rot = body_rotation.matrix
            transformFn = self._bodies[i]["transformFn"]

            if self._up_axis == "y":
                translation = om.MVector(
                    -body_position.x * self._unit_conversion,
                    body_position.z * self._unit_conversion,
                    body_position.y * self._unit_conversion,
                )
                matrix = MMatrix(
                    [
                        rot[0],
                        -rot[2],
                        -rot[1],
                        0,
                        -rot[6],
                        rot[8],
                        rot[7],
                        0,
                        -rot[3],
                        rot[5],
                        rot[4],
                        0,
                        0,
                        0,
                        0,
                        1,
                    ]
                )
            else:
                translation = om.MVector(
                    body_position.x * self._unit_conversion,
                    body_position.y * self._unit_conversion,
                    body_position.z * self._unit_conversion,
                )
                matrix = MMatrix(
                    [
                        rot[0],
                        rot[1],
                        rot[2],
                        0,
                        rot[3],
                        rot[4],
                        rot[5],
                        0,
                        rot[6],
                        rot[7],
                        rot[8],
                        0,
                        0,
                        0,
                        0,
                        1,
                    ]
                )

            transformFn.setTransformation(MTransformationMatrix(matrix))
            transformFn.setTranslation(translation, om.MSpace.kTransform)

    def _init(self):
        self._qtm_settings = self._qtm.get_settings("6d")

        if self._qtm_settings == None:
            return

        self._bodies = []
        bodies = self._qtm_settings["The_6D"].get("Body", [])
        if type(bodies) != type([]):
            bodies = [bodies]

        for i, body in enumerate(bodies):
            body["Index"] = i
            self._bodies.append(body)

    def _update_ui(self):
        self._listWidget.clear()

        for body in self._bodies:
            icon = load_icon(
                os.path.dirname(os.path.abspath(__file__)) + "/assets/rigidbody.svg",
                QtGui.QColor(0x0, 0x0, 0x0),
            )
            item = QtWidgets.QListWidgetItem(icon, body["Name"])

            self._listWidget.addItem(item)

    def create(self):
        if self._bodies == None:
            return

        modifier = om.MDagModifier()

        for body in self._bodies:
            parent = MayaUtil.get_node_by_name(body["Name"])

            if parent is None:
                parent = modifier.createNode("transform")

                modifier.renameNode(parent, body["Name"])
                modifier.doIt()

            transformFn = om.MFnTransform(parent)

            for i, point in enumerate(body["Point"]):
                point_name = body["Name"] + "_" + str(i)
                locator = MayaUtil.get_node_by_name(point_name)

                if locator is None:
                    locator = modifier.createNode("locator")

                    modifier.renameNode(locator, point_name)

                modifier.reparentNode(locator, parent)
                modifier.doIt()

                pointTransformFn = om.MFnTransform(locator)
                translation = None

                if self._up_axis == "y":
                    translation = om.MVector(
                        -float(point["X"]) * self._unit_conversion,
                        float(point["Z"]) * self._unit_conversion,
                        float(point["Y"]) * self._unit_conversion,
                    )
                else:
                    translation = om.MVector(
                        float(point["X"]) * self._unit_conversion,
                        float(point["Y"]) * self._unit_conversion,
                        float(point["Z"]) * self._unit_conversion,
                    )

                pointTransformFn.setTranslation(translation, om.MSpace.kTransform)
            self._bodies[body["Index"]].update(
                {"transform": parent, "transformFn": transformFn}
            )
