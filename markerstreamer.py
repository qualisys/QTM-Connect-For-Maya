import hashlib, os

from PySide2 import QtGui
from PySide2 import QtWidgets

import maya.cmds as cmds
import maya.api.OpenMaya as om

from mayaui import load_icon
from mayautil import MayaUtil


class MarkerStreamer:
    def __init__(self, qtmrt, listWidget, textWidget):
        self._qtm = qtmrt
        self._listWidget = listWidget
        self._textWidget = textWidget
        self._markers = None
        self._marker_groups = None
        self._unit_conversion = 0.1

        self._qtm.connectedChanged.connect(self._connected_changed)
        self._connected_changed(self._qtm.connected)

    def _connected_changed(self, connected):
        self._up_axis = cmds.upAxis(q=True, axis=True)

        if connected:
            self._init()
            self._update_ui()
        else:
            self._markers = None
            self._marker_groups = None
            self._listWidget.clear()

    def _packet_received(self, packet):
        _, markers = packet.get_3d_markers()

        for i, marker in enumerate(markers):
            transformFn = self._markers[i]["transformFn"]

            if self._up_axis == "y":
                translation = om.MVector(
                    -marker.x * self._unit_conversion,
                    marker.z * self._unit_conversion,
                    marker.y * self._unit_conversion,
                )
            else:
                translation = om.MVector(
                    marker.x * self._unit_conversion,
                    marker.y * self._unit_conversion,
                    marker.z * self._unit_conversion,
                )

            transformFn.setTranslation(translation, om.MSpace.kTransform)

    def _init(self):
        self._qtm_settings = self._qtm.get_settings("3d")

        if self._qtm_settings == None:
            return

        if self._marker_groups is None:
            self._markers = []
            self._marker_groups = {"mocapMarkers": []}

            for i, label in enumerate(self._qtm_settings["The_3D"]["Label"]):
                label["Index"] = i

                self._markers.append(label)
                self._marker_groups["mocapMarkers"].append(label)

    def _update_ui(self):
        self._listWidget.clear()

        if self._marker_groups == None:
            return

        for group_name, marker_group in self._marker_groups.items():
            group_icon = load_icon(
                os.path.dirname(os.path.abspath(__file__)) + "/assets/transform.svg",
                QtGui.QColor(255, 0, 0),
            )
            group_item = QtWidgets.QListWidgetItem(group_icon, group_name)

            self._listWidget.addItem(group_item)

            for label in marker_group:
                red = int(label["RGBColor"]) >> 16
                green = (int(label["RGBColor"]) >> 8) & 0x00FF
                blue = int(label["RGBColor"]) & 0x0000FF
                marker_color = QtGui.QColor(red, green, blue)
                icon = load_icon(
                    os.path.dirname(os.path.abspath(__file__))
                    + "/assets/marker_64x32.png",
                    marker_color,
                )
                item = QtWidgets.QListWidgetItem(icon, label["Name"])

                self._listWidget.addItem(item)

    def create(self):
        modifier = om.MDagModifier()

        if self._marker_groups is not None:
            for group_name, marker_group in self._marker_groups.items():
                parent = MayaUtil.get_node_by_name(group_name)

                if parent is None:
                    parent = modifier.createNode("transform")

                    modifier.renameNode(parent, group_name)
                    modifier.doIt()

                for i, marker in enumerate(marker_group):
                    locator = MayaUtil.get_node_by_name(marker["Name"])

                    if locator is None:
                        locator = modifier.createNode("locator")

                        modifier.renameNode(locator, marker["Name"])

                    modifier.reparentNode(locator, parent)
                    modifier.doIt()

                    transformFn = om.MFnTransform(locator)
                    self._markers[marker["Index"]]["locator"] = locator
                    self._markers[marker["Index"]]["transformFn"] = transformFn

    def group_markers(self):
        new_group = []
        new_group_name = self._textWidget.text()
        selected = self._listWidget.selectedItems()

        for item in selected:
            for group_name, marker_group in self._marker_groups.items():
                # Remove marker from existing groups.
                for i, marker in enumerate(marker_group):
                    if item.text() == marker["Name"]:
                        new_group.append(marker_group[i])

                        self._markers[marker["Index"]] = marker

                        del marker_group[i]

        for group_name, marker_group in self._marker_groups.items():
            if len(marker_group) == 0:
                del self._marker_groups[group_name]

        self._marker_groups[new_group_name + " temp"] = new_group

        if new_group_name in self._marker_groups:
            random_name = hashlib.md5(str(time.time())).hexdigest()
            self._marker_groups[random_name] = self._marker_groups[new_group_name]

        self._marker_groups[new_group_name] = self._marker_groups[
            new_group_name + " temp"
        ]
        del self._marker_groups[new_group_name + " temp"]

        self._update_ui()
        self.create()
