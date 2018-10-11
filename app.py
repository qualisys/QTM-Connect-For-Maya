import os, sys
import struct

from PySide2 import QtWidgets
from PySide2 import QtNetwork
from PySide2 import QtUiTools
from PySide2 import QtCore
from Qt import QtCompat
from Qt import __binding__

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omanim
import maya.cmds as cmds

from pyxml2dict import XML2Dict

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/packages/')

import qtm
from qtm.packet import QRTPacketType

MAYA = False
GUI = None

try:
    import maya.OpenMayaUI as OpenMayaUI

    if __binding__ in ("PySide2", "PyQt5"):
        from shiboken2 import wrapInstance
    elif __binding__ in ("PySide", "PyQt4"):
        from shiboken import wrapInstance
    else:
        _print_error("cannot find Qt bindings")
    MAYA = True

except:
    pass


def connect_gui():
    GUI = ConnectGuiDialog()
    GUI.show()


def stop():
    # GUI.close()
	pass


def _get_maya_main_window():
    ptr = OpenMayaUI.MQtUtil.mainWindow()

    if ptr is None:
        raise RuntimeError("No Maya window found.")

    #window = wrapInstance(long(ptr), QtWidgets.QMainWindow)
    #assert isinstance(window, QtWidgets.QMainWindow)
    return wrapInstance(long(ptr), QtWidgets.QWidget)


class ConnectGuiDialog(QtWidgets.QDialog):
    def __init__(self, parent=_get_maya_main_window() if MAYA else None):
        super(ConnectGuiDialog, self).__init__(parent)

        self.setWindowTitle('QTM Connect for Maya')
        self.setMinimumWidth(200)
        #self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint())

        self.widget = QtUiTools.QUiLoader().load(os.path.dirname(os.path.realpath(__file__)) + "/ui/plugin_w.ui")
        layout = QtWidgets.QVBoxLayout(self)

        layout.addWidget(self.widget)
        self.widget.connectButton.clicked.connect(self.connect_qtm)

        self._socket = QtNetwork.QTcpSocket(self)

        self._socket.connected.connect(self._connected)
        self._socket.disconnected.connect(self._disconnected)
        self._socket.readyRead.connect(self._got_data)

        self._handlers = {
            # QRTPacketType.PacketError: self._on_error,
            QRTPacketType.PacketData: self._on_data,
            QRTPacketType.PacketCommand: self._on_command,
            # QRTPacketType.PacketEvent: self._on_event,
            QRTPacketType.PacketXML: self._on_xml,
            QRTPacketType.PacketNoMoreData: lambda _: self._output(
                QRTPacketType.PacketNoMoreData
            ),
        }

        self.is_connected = False

        self._receiver = qtm.Receiver(self._handlers)

    def _on_xml(self, data):
        xml2dict = XML2Dict()
        params = xml2dict.fromstring(data)
        labels = []
        label_data = params['QTM_Parameters_Ver_1.17']['The_3D']['Label']
        self.markers = {}

        for l in label_data:
            labels.append({ 'name': l['Name'], 'color': l['RGBColor'] })

            locator = self.get_node_by_name(l['Name'])

            if locator is None:
                modifier = om.MDagModifier()
                locator = modifier.createNode('locator')

                modifier.renameNode(locator, l['Name'])
                modifier.doIt()

            transformFn = om.MFnTransform(locator)
            self.markers[l['Name']] = {
                'locator': locator,
                'transformFn': transformFn,
           }

        self.labels = labels

        self._send_command("streamframes allframes 3d")

    def _on_command(self, response):
        self._output("R: {}".format(response))
        print(response)

        if response == b"QTM RT Interface connected":
            self._send_command("version 1.17")

        elif response == b"Version set to 1.17":
            self._send_command("getparameters 3d")

    def get_node_by_name(self, name):
        dagIterator = om.MItDag()
        dagNodeFn = om.MFnDagNode()

        while (not dagIterator.isDone()):
            dagObject = dagIterator.currentItem()
            dagNodeFn.setObject(dagObject)

            if dagNodeFn.name() == name:
                return dagObject

            dagIterator.next()

        return None


    def handle_markers(self, markers):
        for i, marker in enumerate(markers):
            marker_name = self.labels[i]['name']

            locator = self.markers[marker_name]['locator']
            transformFn = self.markers[marker_name]['transformFn']
            transformFn.setTranslation(om.MVector(marker.x/100, marker.z/100, marker.y/100), om.MSpace.kTransform)

        pass
        

    def _on_data(self, packet):
        info, markers = packet.get_3d_markers()

        self.handle_markers(markers)

        self._output(
            "Frame number: {} Markers: {} - First: {}".format(
                packet.framenumber, info.marker_count, markers[0]
            )
        )
        # print(markers)

    def _output(self, text):
        self.widget.textBox.appendPlainText(text)

    def _got_data(self):
        self._receiver.data_received(self._socket.readAll())

    def _connected(self):
        self.is_connected = True
        self.widget.connectButton.setText("Disconnect")
        self._output("Connected")

    def _disconnected(self):
        self.is_connected = False
        self.widget.connectButton.setText("Connect")
        self._output("Disconnected")

    def _send_command(self, command, command_type=QRTPacketType.PacketCommand):
        cmd_length = len(command)
        self._output("S: {}".format(command))
        self._socket.write(
            struct.pack(
                qtm.packet.RTCommand % cmd_length,
                qtm.packet.RTheader.size + cmd_length + 1,
                command_type.value,
                command.encode(),
                b"\0",
            )
        )

    def connect_qtm(self):
        if not self.is_connected:
            self._socket.connectToHost("qualisys842", 22223)
        else:
            self._socket.disconnectFromHost()


def main():
    if not MAYA:
        app = QtWidgets.QApplication(sys.argv)

    #window = MainPlugin()
    #window.show()
    dialog = ConnectGuiDialog()
    dialog.show()

    if not MAYA:
        app.exec_()


if __name__ == "__main__":
    main()

