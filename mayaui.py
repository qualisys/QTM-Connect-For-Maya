import os, sys

from PySide2 import QtCore
from PySide2 import QtGui

import maya.cmds as cmds
import pymel.core as pmc
import maya.OpenMayaUI as OpenMayaUI
import maya.mel as mel

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/modules/')

class QtmConnectShelf:
    def __init__(self):
        self.top_level_shelf_layout = mel.eval('global string $gShelfTopLevel; $temp = $gShelfTopLevel;')

        self.asset_dir    = os.path.dirname(os.path.abspath(__file__)) + '/assets/'
        self.connect_icon = self.asset_dir + 'connect.png'
        self.start_icon   = self.asset_dir + 'start.png'
        self.stop_icon    = self.asset_dir + 'stop.png'
        self.start        = 'Start_streaming'
        self.stop         = 'Stop_streaming'


    def install(self):
        shelf_layout = pmc.shelfLayout('QTM_Connect', parent=self.top_level_shelf_layout)

        cmds.shelfButton(
            label='Connect to QTM',
            parent=shelf_layout,
            command='import qtm_connect_maya.app;reload(qtm_connect_maya.app);qtm_connect_maya.app.qtm_connect_gui()',
            image1=self.connect_icon
        )

        cmds.shelfButton(
            'start_stop',
            label='Start/stop streaming',
            parent='QTM_Connect',
            image1=self.start_icon,
            command='import qtm_connect_maya.app;reload(qtm_connect_maya.app);qtm_connect_maya.app.start()',
        )

    def toggle_stream_button(self, mode):
        cmds.shelfButton(
            'start_stop',
            edit=True,
            command='import qtm_connect_maya.app;reload(qtm_connect_maya.app);qtm_connect_maya.app.' + ('stop()' if mode == 'stop' else 'start()'),
            image1=self.stop_icon if mode == 'stop' else self.start_icon
        )

def install():
    """
    Call this function to install the Maya shelf.
        qtm_connect_maya.shelf.install()
    """

    shelf = QtmConnectShelf()
    shelf.install()


# Returns a QIcon with the image at path recolored with the specified color.
def load_icon(path, color):
    pixmap = QtGui.QPixmap(path)
    icon = QtGui.QIcon()
    mask = pixmap.createMaskFromColor(QtGui.QColor(0x0, 0x0, 0x0), QtCore.Qt.MaskOutColor)
    p = QtGui.QPainter(pixmap)

    p.setPen(color)
    p.drawPixmap(pixmap.rect(), mask, mask.rect())
    p.end()
    icon.addPixmap(pixmap, QtGui.QIcon.Normal)

    return icon