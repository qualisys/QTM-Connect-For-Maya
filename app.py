import os, sys, time

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/')
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/modules/')
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/modules/qualisys_python_sdk')

from PySide2 import QtWidgets
from PySide2 import QtNetwork
from PySide2 import QtUiTools
from PySide2 import QtCore
from PySide2 import QtGui
from Qt import __binding__

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omanim
import maya.cmds as cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from qtm.packet import QRTComponentType
from qqtmrt import QQtmRt
from mayautil import MayaUtil
from mayaui import QtmConnectShelf
from markerstreamer import MarkerStreamer
from skeletonstreamer import SkeletonStreamer
from rigidbodystreamer import RigidBodyStreamer
import importlib

import qtmREST
importlib.reload(qtmREST)
from qtmREST import grabCurrentFrame

from QExportSolver import PushXMLSkeleton
import QImportSolver

import qscipy
importlib.reload(qscipy)
from qscipy import QRotation

import xml.etree.ElementTree as ET

MAYA = False

try:
    import maya.OpenMayaUI as OpenMayaUI

    if __binding__ in ('PySide2', 'PyQt5'):
        from shiboken2 import wrapInstance
    elif __binding__ in ('PySide', 'PyQt4'):
        from shiboken import wrapInstance
    else:
        _print_error('Cannot find Qt bindings.')

    MAYA = True
except:
    pass

def reset():
    parent = _get_maya_main_window()

    if hasattr(parent, '_qtmConnect'):
        parent._qtmConnect.close()

        del parent._qtmConnect

def qtm_connect_gui():
    use_workspace_control = False
    parent = _get_maya_main_window()

    if use_workspace_control:
        show_gui()
    else:
        if hasattr(parent, '_qtmConnect'):
            dialog = parent._qtmConnect
        else:
            dialog = QtmConnectWidget()

        dialog.show(dockable=True, height=800, width=285)

def start():
    parent = _get_maya_main_window()

    if not hasattr(parent, '_qtmConnect'):
        cmds.warning('Not connected to QTM.')
    else:
        if not parent._qtmConnect._qtm.connected:
            parent._qtmConnect.connect_qtm()

        if parent._qtmConnect._qtm.connected:
            parent._qtmConnect.stream()
    
def stop():
    parent = _get_maya_main_window()

    if not hasattr(parent, '_qtmConnect') or not parent._qtmConnect._qtm.connected:
        cmds.warning('Not connected to QTM.')
    else:
        parent._qtmConnect.stop_stream()

        QtCore.QTimer.singleShot(750, set_start_button)

def set_start_button():
    parent = _get_maya_main_window()

    parent._qtmConnect._shelf.toggle_stream_button('start')

def _get_maya_main_window():
    ptr = OpenMayaUI.MQtUtil.mainWindow()

    if ptr is None:
        raise RuntimeError('No Maya window found.')

    return wrapInstance(int(ptr), QtWidgets.QWidget)

def show_gui(restore=False):
    parent = _get_maya_main_window()


    ''' When the control is restoring, the workspace control has already been created and
    all that needs to be done is restoring its UI.
    '''
    if restore == True:
        # Grab the created workspace control with the following.
        restoredControl = omui.MQtUtil.getCurrentParent()

    if not hasattr(parent, 'customMixinWindow'):
        # Create a custom mixin widget for the first time.
        parent.customMixinWindow = QtmConnectWidget()
        parent.customMixinWindow.setObjectName('qtmConnectForMayaMixinWindow')

    if restore == True:
        # Add custom mixin widget to the workspace control.
        mixinPtr = omui.MQtUtil.findControl(parent.customMixinWindow.objectName())
        omui.MQtUtil.addWidgetToMayaLayout(long(mixinPtr), long(restoredControl))
    else:
        # Create a workspace control for the mixin widget by passing all the
        # needed parameters. See workspaceControl command documentation for all
        # available flags.
        parent.customMixinWindow.show(dockable=True, height=800, width=285, uiScript='show_gui(restore=True)')

    return parent.customMixinWindow

def UpdateMarkers(markerdata):
    #print(f"Update Markers with{markerdata}")
    for marker in markerdata:
        if '_' in marker:
            namespace,shortname = marker.split("_",1)
            groupnodename = f"{namespace}:Markers"
            groupnodes = cmds.ls(groupnodename)
            if not groupnodes:
                groupnode = cmds.group(em=True,name=groupnodename)
                print(f"New Namespace is {namespace}")

            else:
                groupnode = groupnodes[0]

            # hardcode mm to cm for now
            px = markerdata[marker]["x"].values[0] / 10.0
            py = markerdata[marker]["y"].values[0] / 10.0
            pz = markerdata[marker]["z"].values[0] / 10.0
            if px != px:
                # Maya doesn't like nans
                # print(f"Fixing nan")
                px = 0.0
                py = 0.0
                pz = 0.0
            fullname = f"{namespace}:{shortname}"
            if not cmds.objExists(fullname):
                print(f"Adding Marker {shortname} to {namespace}")
                cmds.spaceLocator(name=fullname)
                cmds.setAttr("%s.overrideEnabled" % fullname, 1)
                cmds.setAttr("%s.overrideColor" % fullname, 22)
                cmds.select(fullname)
                cmds.move(px,py,pz, ls=True)
                cmds.scale(2,2,2)
                cmds.select(groupnodename)
                cmds.parent(fullname)
            else:
                cmds.select(fullname)
                cmds.move(px,py,pz)

def MtoE(m):
    """
    Convert a REST 3x3 matrix to Euler angles for Maya
    """
    R = QRotation()
    R.M[0][0] = m[0]
    R.M[0][1] = m[1]
    R.M[0][2] = m[2]
    R.M[1][0] = m[3]
    R.M[1][1] = m[4]
    R.M[1][2] = m[5]
    R.M[2][0] = m[6]
    R.M[2][1] = m[7]
    R.M[2][2] = m[8]
    return R.as_euler_xyz()

def UpdateRigidbodies(rigidbodies):
    print(f"UpdateRigidBodies")
    for rigidbody in rigidbodies:
        if '_' in rigidbody:
            namespace,shortname = rigidbody.split("_",1)
            groupnodename = f"{namespace}:Rigidbodies"
            groupnodes = cmds.ls(groupnodename)
            if not groupnodes:
                groupnode = cmds.group(em=True,name=groupnodename)
                print(f"New Namespace is {namespace}")
            else:
                groupnode = groupnodes[0]

            # hardcode mm to cm for now
            px = rigidbodies[rigidbody]["Position"][0] / 10.0
            py = rigidbodies[rigidbody]["Position"][1] / 10.0
            pz = rigidbodies[rigidbody]["Position"][2] / 10.0
            if px != px:
                # Maya doesn't like nans
                # print(f"Fixing nan")
                px = 0.0
                py = 0.0
                pz = 0.0
            r = MtoE(rigidbodies[rigidbody]["Rotation"])

            fullname = f"{namespace}:{shortname}"
            if not cmds.objExists(fullname):
                print(f"Adding Rigid Body {shortname} to {namespace}")
                cmds.spaceLocator(name=fullname)
                cmds.setAttr("%s.overrideEnabled" % fullname, 1)
                cmds.setAttr("%s.overrideColor" % fullname, 23)
                cmds.select(fullname)
                cmds.move(px,py,pz, ls=True)
                cmds.rotate(r[0],r[1],r[2])
                cmds.scale(4,4,4)
                cmds.select(groupnodename)
                cmds.parent(fullname)
            else:
                cmds.select(fullname)
                cmds.move(px,py,pz)


class QtmConnectWidget(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    def __init__(self, parent=_get_maya_main_window() if MAYA else None):
        super(QtmConnectWidget, self).__init__(parent=parent)

        self.setWindowTitle('QTM Connect for Maya')
        self.setMinimumWidth(200)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.widget = QtUiTools.QUiLoader().load(os.path.dirname(os.path.realpath(__file__)) + '/ui/qtm_connect.ui')
        layout = QtWidgets.QVBoxLayout(self)

        layout.addWidget(self.widget)

        self.marker_groups = None

        if hasattr(parent, '_qtmConnect'):
            parent._qtmConnect.stop_stream()
            parent._qtmConnect._qtm.disconnect()

        self._qtm                 = QQtmRt()
        print(f"InitQtmConnectionWidget QQtmRt is {type(self._qtm)}")
        self._skeleton_streamer   = SkeletonStreamer(self._qtm, self.widget.skeletonList)
        self._marker_streamer     = MarkerStreamer(self._qtm, self.widget.markerList, self.widget.groupNameField)
        self._rigid_body_streamer = RigidBodyStreamer(self._qtm, self.widget.rigidBodyList)
        self._shelf               = QtmConnectShelf()

        self._shelf.toggle_stream_button('start')

        # Expose this dialog instance to following script runs.
        # The advantage of setting it on the parent is that we can reload the
        # module and still access it as opposed to a variable local to the module.
        parent._qtmConnect = self

        self._qtm.connectedChanged.connect(self._connected_changed)
        self._qtm.streamingChanged.connect(self._streaming_changed)
        self._qtm.packetReceived.connect(self._packet_received)
        self._qtm.eventReceived.connect(self._event_received)
        self._qtm.noDataReceived.connect(self._no_data_received)

        self.widget.verticalLayout.setAlignment(QtCore.Qt.AlignTop)
        self.widget.connectButton.clicked.connect(self.connect_qtm)
        self.widget.startButton.clicked.connect(self.stream)
        self.widget.stopButton.clicked.connect(self.stop_stream)
        self.widget.groupButton.clicked.connect(self._marker_streamer.group_markers)
        self.widget.groupNameField.textChanged.connect(self.group_name_changed)
        self.widget.markerGroupButtonLayout.setAlignment(QtCore.Qt.AlignTop)
        self.widget.markerList.clicked.connect(self.marker_selected)
        self.widget.markerList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.widget.markerList.setIconSize(QtCore.QSize(32, 16))
        self.widget.skeletonList.clicked.connect(self.skeleton_selected)
        self.widget.skeletonList.setIconSize(QtCore.QSize(32, 16))
        self.widget.skeletonComponentButton.toggled.connect(self.component_changed)
        self.widget.markerComponentButton.toggled.connect(self.component_changed)
        self.widget.rigidBodyComponentButton.toggled.connect(self.component_changed)
        self.widget.tPoseButton.clicked.connect(self.toggle_t_pose)
        self.widget.getMarkers.clicked.connect(self.get_markers)
        self.widget.pushSkeleton.clicked.connect(self.push_skeleton)
        self.widget.pullSkeletons.clicked.connect(self.pull_skeletons)

        #self.widget.connectionContainer.setFixedHeight(110)
        
        if cmds.optionVar(exists='qtmHost') == 1:
            hostname = 'localhost' if cmds.optionVar(q='qtmHost') == '' else cmds.optionVar(q='qtmHost')
        else:
            hostname = 'localhost'

        self.widget.hostField.textChanged.connect(self._host_changed)
        self.widget.hostField.setText(hostname)
        self._host = self.widget.hostField.text()
        #self._password = "password"
        self._password = ""
        self.is_streaming = False

        self._connected_changed(self._qtm.connected)
        self.component_changed()

        self._last_event = None

    def component_changed(self):
        #self.widget.skeletonComponentContainer.setVisible(self.widget.skeletonComponentButton.isChecked())
        #self.widget.markerComponentContainer.setVisible(self.widget.markerComponentButton.isChecked())
        #self.widget.rigidBodyComponentContainer.setVisible(self.widget.rigidBodyComponentButton.isChecked())

        if self.is_streaming:
            self._qtm.stop_stream()
            self._shelf.toggle_stream_button('start')

        if self.widget.skeletonComponentButton.isChecked():
            self._skeleton_streamer.create()

        if self.widget.markerComponentButton.isChecked():
            self._marker_streamer.create()
        
        if self.widget.rigidBodyComponentButton.isChecked():
            self._rigid_body_streamer.create()

    def _host_changed(self, text):
        self._host = text
        cmds.optionVar(sv=('qtmHost', text))

    def _no_data_received(self, packet):
        cmds.warning('No data received. Make sure QTM is broadcasting.')
        self.stop_stream()
        self._qtm.disconnect()

    def _packet_received(self, packet):
        if not isinstance(packet, str):
            if QRTComponentType.Component3d in packet.components:
                self._marker_streamer._packet_received(packet)

            if QRTComponentType.ComponentSkeleton in packet.components:
                self._skeleton_streamer._packet_received(packet)

            if QRTComponentType.Component6d in packet.components:
                self._rigid_body_streamer._packet_received(packet)

    def _event_received(self, event):
        self._last_event = event
        self._output('Event received: {}'.format(event))

    def _output(self, text):
        #pass
        print(text)

    def _connected_changed(self, connected):
        self.is_connected = connected

        self.widget.connectButton.setText('Disconnect' if connected else 'Connect')
        self.widget.hostField.setEnabled(not connected)
        self.widget.startButton.setEnabled(connected)
        self.widget.pushSkeleton.setEnabled(connected)
        self.widget.pullSkeletons.setEnabled(connected)
        self._shelf.toggle_connect_button(connected)

        if connected:
            event = self._qtm.get_latest_event()

            if self.widget.skeletonComponentButton.isChecked():
                self._skeleton_streamer.create()

            if self.widget.markerComponentButton.isChecked():
                self._marker_streamer.create()

            if self.widget.rigidBodyComponentButton.isChecked():
                self._rigid_body_streamer.create()

            self._output('Latest event: {}'.format(event))

    def group_name_changed(self):
        if self.widget.groupNameField.text() != '' and len(self.widget.markerList.selectedItems()) > 0:
            self.widget.groupButton.setEnabled(True)

    def marker_selected(self, index):
        if self.widget.groupNameField.text() != '':
            self.widget.groupButton.setEnabled(True)

    def skeleton_selected(self, index):
        self.widget.tPoseButton.setEnabled(not self.is_streaming)

        item = self.widget.skeletonList.itemFromIndex(index)

        if self._skeleton_streamer.is_in_t_pose(item.text().replace(' [T-pose]', '')):
            self.widget.tPoseButton.setText('Resume pose')
        else:
            self.widget.tPoseButton.setText('Go to T-pose')

    def toggle_t_pose(self):
        selected = self.widget.skeletonList.selectedItems()

        for item in selected:
            skeleton_name = item.text().replace(' [T-pose]', '')

            if self._skeleton_streamer.is_in_t_pose(skeleton_name):
                self._skeleton_streamer.resume_pose(skeleton_name)
                item.setText(skeleton_name)
                self.widget.tPoseButton.setText('Go to T-pose')
            else:
                self._skeleton_streamer.t_pose(skeleton_name)
                item.setText(skeleton_name + ' [T-pose]')
                self.widget.tPoseButton.setText('Resume pose')
    def get_markers(self):
        """
        Get the current frame of markers AND rigid bodies from QTM and create locators
        for all of them that can be used to create a custom solver model.
        """
        #self._output(f"You selected GetMarkers!")
        marker_data, rigidbody_data = grabCurrentFrame(self._host)
        no_response = False
        if marker_data is not False:
            #self._output(f"Got a response")
            #print (f"Response is {response}")
            #print(f"FileInfo {fileInfo}")
            #print(f"Marker Data is {marker_data}")
            UpdateMarkers(marker_data)
        else:
            no_response = True
        print(f"Rigid body data {rigidbody_data}")
        if rigidbody_data is not False:
            UpdateRigidbodies(rigidbody_data)
        else:
            no_response = True

        if no_response:
            self._output(f"No marker data or rigid body data - did not get a reponse")

    def push_skeleton(self):
        print(f"In Push Skeleton")
        XML = PushXMLSkeleton()
        if XML:
            #print(f"XML is {XML}")
            resp = self._qtm.set_skeletons(XML)
            print(f"Response from Pushing skeleton: {resp}")
        else:
            print(f"No Valid Model Pose")

    def pull_skeletons(self):
        print(f"In Pull Skeletons")
        sXML = self._qtm.get_parameters("skeleton")
        root = ET.fromstring(sXML)
        print(f"root is {type(root)}")
        tag = root.tag
        print(f"Root Tag is {tag}")
        for skeletons in root:
            for skeleton in skeletons:
                print(f"skeleton {skeleton.tag}")
                QIS = QImportSolver.QImportSolver()
                QIS.SetSceneScale()
                QIS.ImportQTMSkeletonStream(skeleton)

    def _reset_skeleton_names(self):
        items = []
        for index in range(self.widget.skeletonList.count()):
            items.append(self.widget.skeletonList.item(index))

        for item in items:
            skeleton_name = item.text().replace(' [T-pose]', '')

            self._skeleton_streamer.resume_pose(skeleton_name)
            item.setText(skeleton_name)

        self.widget.tPoseButton.setText('Go to T-pose')

    def _streaming_changed(self, streaming):
        self.widget.startButton.setEnabled(not streaming)
        self.widget.stopButton.setEnabled(streaming)
        self.widget.tPoseButton.setEnabled(not streaming)
        self.widget.pushSkeleton.setEnabled(not streaming)
        self.widget.pullSkeletons.setEnabled(not streaming)
    
    def stream(self):

        components = []

        if self.widget.skeletonComponentButton.isChecked():
            components.append('skeleton')

        if self.widget.markerComponentButton.isChecked():
            components.append('3d')

        if self.widget.rigidBodyComponentButton.isChecked():
            components.append('6d')

        self._qtm.stream(' '.join(components))
        self._reset_skeleton_names()
        self._shelf.toggle_stream_button('stop')

        self.is_streaming = True

    def stop_stream(self):
        self._qtm.stop_stream()
        self.is_streaming = False

        self._shelf.toggle_stream_button('start')

    def get_settings_3d(self):
        self._output(str(self._qtm.get_settings('3d')))

    def connect_qtm(self):
        if self._qtm.connected:
            self._qtm.disconnect()
            self._shelf.toggle_stream_button('start')
        else:
            self.widget.connectButton.setEnabled(False)
            self._qtm.connect_to_qtm(self._host, 4000)
            self.widget.connectButton.setEnabled(True)

            if not self._qtm.connected:
                cmds.warning('Could not connect to host \'' + self._host + '\'.')

def main():
    if not MAYA:
        app = QtWidgets.QApplication(sys.argv)

    window = MainPlugin()
    window.show()

    if not MAYA:
        app.exec_()


if __name__ == '__main__':
    main()
