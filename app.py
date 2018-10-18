import hashlib, os, sys, time

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/modules/')

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

from qqtmrt import QQtmRt

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

def qtm_connect_gui():
    use_workspace_control = True

    if use_workspace_control:
        show_gui()
    else:
        d = QtmConnectWidget()
        d.show(dockable=True, height=800, width=480)

def start():
    parent = _get_maya_main_window()

    if not hasattr(parent, '_qtm') or not parent._qtm.connected:
        cmds.warning('Not connected to QTM.')
    else:
        parent._qtm.stream('3d')

def stop():
    parent = _get_maya_main_window()

    if not hasattr(parent, '_qtm') or not parent._qtm.connected:
        cmds.warning('Not connected to QTM.')
    else:
        parent._qtm.stop_stream()


def _get_maya_main_window():
    ptr = OpenMayaUI.MQtUtil.mainWindow()

    if ptr is None:
        raise RuntimeError('No Maya window found.')

    return wrapInstance(long(ptr), QtWidgets.QWidget)

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
        parent.customMixinWindow.show(dockable=True, height=600, width=480, uiScript='show_gui(restore=True)')

    return parent.customMixinWindow

class QtmConnectWidget(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    def __init__(self, parent=_get_maya_main_window() if MAYA else None):
        super(QtmConnectWidget, self).__init__(parent=parent)

        self.setWindowTitle('QTM Connect for Maya')
        self.setMinimumWidth(200)
        #self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint())
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.widget = QtUiTools.QUiLoader().load(os.path.dirname(os.path.realpath(__file__)) + '/ui/plugin_w.ui')
        layout = QtWidgets.QVBoxLayout(self)

        layout.addWidget(self.widget)

        # self.streamingService = StreamingService()
        self.marker_groups = None

        if hasattr(parent, '_qtm'):
            parent._qtm.stop_stream()
            parent._qtm.disconnect()

        self._qtm = QQtmRt()

        # Expose QQtmRt instance to following script runs.
        # The advantage of setting it on the parent is that we can reload the
        # module and still access it as opposed to a variable local to the module.
        parent._qtm = self._qtm

        self._qtm.connectedChanged.connect(self._connected_changed)
        self._qtm.streamingChanged.connect(self._streaming_changed)
        self._qtm.packetReceived.connect(self._packet_received)
        self._qtm.eventReceived.connect(self._event_received)

        self.widget.connectButton.clicked.connect(self.connect_qtm)
        self.widget.startButton.clicked.connect(self.stream_3d)
        self.widget.stopButton.clicked.connect(self._qtm.stop_stream)
        self.widget.groupButton.clicked.connect(self.group_markers)
        self.widget.list.clicked.connect(self.item_selected)
        self.widget.list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.widget.list.setIconSize(QtCore.QSize(32, 16))
        self.widget.markerGroupButtonLayout.setAlignment(QtCore.Qt.AlignTop)
        self.widget.groupNameField.textChanged.connect(self.group_name_changed)

        self.widget.textBox.setFixedHeight(50)

        if cmds.optionVar(exists='qtmHost') == 1:
            hostname = 'localhost' if cmds.optionVar(q='qtmHost') == '' else cmds.optionVar(q='qtmHost')
        else:
            hostname = 'localhost'

        self.widget.hostField.textChanged.connect(self._host_changed)
        self.widget.hostField.setText(hostname)
        self._host = self.widget.hostField.text()

    def _host_changed(self, text):
        self._host = text
        cmds.optionVar(sv=('qtmHost', text))

    def _packet_received(self, packet):
        info, markers = packet.get_3d_markers()

        for i, marker in enumerate(markers):
            locator = self.markers[i]['locator']
            transformFn = self.markers[i]['transformFn']
            transformFn.setTranslation(om.MVector(marker.x/100, marker.z/100, marker.y/100), om.MSpace.kTransform)

    def _event_received(self, event):
        self._output('Event received: {}'.format(event))

    def _output(self, text):
        self.widget.textBox.appendPlainText(text)

    def _connected_changed(self, connected):
        self.is_connected = connected
        self.widget.connectButton.setText('Disconnect' if connected else 'Connect')
        self.widget.hostField.setEnabled(not connected)
        self.widget.startButton.setEnabled(connected)

        if connected:
            event = self._qtm.get_latest_event()
            self._output('Latest event: {}'.format(event))
            self.qtm_3d_settings = self._qtm.get_settings('3d')

            self.setup_marker_groups()
            self.populate_marker_list()
            self.upsert_locators()
        else:
            self.widget.list.clear()

    def setup_marker_groups(self):
        self.markers = []

        if self.marker_groups is None:
            self.marker_groups = { 'mocapMarkers': [] }

            for i, label in enumerate(self.qtm_3d_settings['The_3D']['Label']):
                label['Index'] = i

                self.markers.append(label)
                self.marker_groups['mocapMarkers'].append(label)

    def populate_marker_list(self):
        self.widget.list.clear()

        for group_name, marker_group in self.marker_groups.items():
            group_item = QtWidgets.QListWidgetItem(group_name) 

            self.widget.list.addItem(group_item)

            for label in marker_group:
                red = long(label['RGBColor']) >> 16
                green = (long(label['RGBColor']) >> 8) & 0x00ff
                blue = long(label['RGBColor']) & 0x0000ff
                marker_color = QtGui.QColor(red, green, blue)
                icon = self.load_icon(os.path.dirname(os.path.abspath(__file__)) + '/assets/marker_64x32.png', marker_color)
                item = QtWidgets.QListWidgetItem(icon, label['Name']) 

                self.widget.list.addItem(item)

    def group_markers(self):
        new_group = []
        new_group_name = self.widget.groupNameField.text()
        selected = self.widget.list.selectedItems()

        for item in selected:
            for group_name, marker_group in self.marker_groups.items():
                # Remove marker from existing groups.
                for i, marker in enumerate(marker_group):
                    if item.text() == marker['Name']:
                        new_group.append(marker_group[i])

                        self.markers[marker['Index']] = marker

                        del marker_group[i]
                
        for group_name, marker_group in self.marker_groups.items():
            if len(marker_group) == 0:
                del self.marker_groups[group_name]

        self.marker_groups[new_group_name + ' temp'] = new_group

        if new_group_name in self.marker_groups:
            random_name = hashlib.md5(str(time.time())).hexdigest()
            self.marker_groups[random_name] = self.marker_groups[new_group_name]

        self.marker_groups[new_group_name] = self.marker_groups[new_group_name + ' temp']
        del self.marker_groups[new_group_name + ' temp']

        self.populate_marker_list()
        self.upsert_locators()

    def group_name_changed(self):
        if self.widget.groupNameField.text() != '' and len(self.widget.list.selectedItems()) > 0:
            self.widget.groupButton.setEnabled(True)

    def item_selected(self, item):
        if self.widget.groupNameField.text() != '':
            self.widget.groupButton.setEnabled(True)
    
    def upsert_locators(self):
        modifier = om.MDagModifier()

        for group_name, marker_group in self.marker_groups.items():
            parent = self.get_node_by_name(group_name)

            if parent is None:
                parent = modifier.createNode('transform')

                modifier.renameNode(parent, group_name)
                modifier.doIt()

            for i, marker in enumerate(marker_group):
                locator = self.get_node_by_name(marker['Name'])

                if locator is None:
                    locator = modifier.createNode('locator')

                    modifier.renameNode(locator, marker['Name'])

                modifier.reparentNode(locator, parent)
                modifier.doIt()

                transformFn = om.MFnTransform(locator)
                self.markers[marker['Index']]['locator'] = locator
                self.markers[marker['Index']]['transformFn'] = transformFn

    # Returns a QIcon with the image at path recolored with the specified
    # color.
    def load_icon(self, path, color):
        pixmap = QtGui.QPixmap(path)
        icon = QtGui.QIcon()
        mask = pixmap.createMaskFromColor(QtGui.QColor(0x0, 0x0, 0x0), QtCore.Qt.MaskOutColor)
        p = QtGui.QPainter(pixmap)

        p.setPen(color)
        p.drawPixmap(pixmap.rect(), mask, mask.rect())
        p.end()
        icon.addPixmap(pixmap, QtGui.QIcon.Normal)
    
        return icon

    def _streaming_changed(self, streaming):
        self.widget.startButton.setEnabled(not streaming)
        self.widget.stopButton.setEnabled(streaming)

    def stream_3d(self):
        self._qtm.stream('3d')

    def get_settings_3d(self):
        self._output(str(self._qtm.get_settings('3d')))

    def connect_qtm(self):
        if self._qtm.connected:
            self._qtm.disconnect()
        else:
            self.widget.connectButton.setEnabled(False)
            self._qtm.connect_to_qtm(self._host, 3000)
            self.widget.connectButton.setEnabled(True)

            if not self._qtm.connected:
                cmds.warning('Could not connect to host.')
                
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


def main():
    if not MAYA:
        app = QtWidgets.QApplication(sys.argv)

    window = MainPlugin()
    window.show()

    if not MAYA:
        app.exec_()


if __name__ == '__main__':
    main()