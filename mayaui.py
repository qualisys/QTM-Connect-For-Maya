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

        self.asset_dir      = os.path.dirname(os.path.abspath(__file__)) + '/assets/'
        self.connect_icon   = self.asset_dir + 'connect.png'
        self.connected_icon = self.asset_dir + 'connected.png'
        self.start_icon     = self.asset_dir + 'start.png'
        self.stop_icon      = self.asset_dir + 'stop.png'
        self.import_icon    = self.asset_dir + 'import.png'
        self.export_icon    = self.asset_dir + 'export.png'
        self.add_dofs_icon  = self.asset_dir + 'add_dofs.png'
        self.add_attachments_icon = self.asset_dir + 'add_attachments.png'
        self.wash_locators_icon = self.asset_dir + 'wash_locators.png'
        self.shelf_name = 'QTM_Connect'
        self.connect_label = 'Connect to QTM'
        self.stream_label = 'Start/stop streaming'
        self.import_label = 'Import skeleton definition'
        self.export_label = 'Export skeleton definition'
        self.add_dofs_label = 'Add DOF attributes'
        self.add_attachments_label = 'Add marker attachments'
        self.wash_locators_label = 'Wash locators'


    def install(self):
        shelf_layout = pmc.shelfLayout(self.shelf_name, parent=self.top_level_shelf_layout)

        cmds.shelfButton(
            label=self.connect_label,
            parent=shelf_layout,
            image1=self.connect_icon,
            command='import qtm_connect_maya.app;reload(qtm_connect_maya.app);qtm_connect_maya.app.qtm_connect_gui()'
        )

        cmds.shelfButton(
            'start_stop',
            label=self.stream_label,
            parent=self.shelf_name,
            image1=self.start_icon,
            command='import qtm_connect_maya.app;reload(qtm_connect_maya.app);qtm_connect_maya.app.start()'
        )

        cmds.shelfButton(
            'import_definition',
            label=self.import_label,
            parent=self.shelf_name,
            image1=self.import_icon,
            command='import qtm_connect_maya.QImportSolver;reload(qtm_connect_maya.QImportSolver);qtm_connect_maya.QImportSolver.ImportQTMSkeleton()'
        )

        cmds.shelfButton(
            'export_definition',
            label=self.export_label,
            parent=self.shelf_name,
            image1=self.export_icon,
            command='import qtm_connect_maya.QExportSolver;reload(qtm_connect_maya.QExportSolver);qtm_connect_maya.QExportSolver.ExportQTMSkeleton()'
        )

        cmds.shelfButton(
            'add_dofs',
            label=self.add_dofs_label,
            parent=self.shelf_name,
            image1=self.add_dofs_icon,
            command='import qtm_connect_maya.AddDOFAttributes;reload(qtm_connect_maya.AddDOFAttributes);qtm_connect_maya.AddDOFAttributes.AddDOFAttributes()'
        )

        cmds.shelfButton(
            'add_attachments',
            label=self.add_attachments_label,
            parent=self.shelf_name,
            image1=self.add_attachments_icon,
            command='import qtm_connect_maya.AddAttachments;reload(qtm_connect_maya.AddAttachments);qtm_connect_maya.AddAttachments.AddAttachments()'
        )

        cmds.shelfButton(
            'wash_locators',
            label=self.wash_locators_label,
            parent=self.shelf_name,
            image1=self.wash_locators_icon,
            command='import qtm_connect_maya.WashLocators;reload(qtm_connect_maya.WashLocators);qtm_connect_maya.WashLocators.WashLocators()'
        )

    # Find the button with the specified name. For some reason Maya resets the
    # name we've given the shelf button so we cannot rely on that.
    def _find_button(self, name):
        buttons = cmds.shelfLayout(self.shelf_name, query=True, childArray=True)

        for button in buttons:
            label = cmds.shelfButton(button, query=True, annotation=True)

            if label == name:
                return button
        
        return None

    def toggle_connect_button(self, connected):
        connect_button = self._find_button(self.connect_label)

        cmds.shelfButton(
            connect_button,
            edit=True,
            image1=self.connected_icon if connected else self.connect_icon
        )

    def toggle_stream_button(self, mode):
        stream_button = self._find_button(self.stream_label)

        cmds.shelfButton(
            stream_button,
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

def startup():
    shelf = QtmConnectShelf()

    shelf.toggle_connect_button(False)

def install_startup_script():
    script_dir = cmds.internalVar(userScriptDir=True)
    script_file = script_dir + 'userSetup.py'
    snippet = '''
import maya.cmds as cmds
import qtm_connect_maya.mayaui

cmds.evalDeferred(qtm_connect_maya.mayaui.startup())
'''

    f = open(script_file, 'r+')
    current_script = f.read()

    # Remove snippet if it already exists, then append it again.
    new_script = current_script.replace(snippet, '')
    new_script += snippet

    f.seek(0)
    f.write(new_script)
    f.truncate()
    f.close()

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