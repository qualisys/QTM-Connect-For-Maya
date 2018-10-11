import os, sys

import pymel.core as pmc
import maya.OpenMayaUI as OpenMayaUI
import maya.mel as mel

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/modules/')

def install():
    """
    Call this function to install the Maya shelf.
        qtm_connect_maya.shelf.install()
    """

    # First get maya "official" shelves layout.
    top_level_shelf_layout = mel.eval(
        "global string $gShelfTopLevel; $temp = $gShelfTopLevel;"
    )

    # Get all shelves:
    shelf_layout = pmc.shelfLayout("QTM_Connect", parent=top_level_shelf_layout)
    asset_dir = os.path.dirname(os.path.abspath(__file__)) + '/assets/'
    connect_icon = asset_dir + "connect.png"
    start_icon =  asset_dir + "start.png"
    stop_icon = asset_dir + "stop.png"

    pmc.shelfButton(
        label="Connect to QTM",
        parent=shelf_layout,
        command="import qtm_connect_maya.app;reload(qtm_connect_maya.app);qtm_connect_maya.app.connect_gui()",
        image1=connect_icon
    )
    pmc.shelfButton(
        label="Start streaming",
        parent=shelf_layout,
		image1=start_icon,
        command="import qtm_connect_maya.app;reload(qtm_connect_maya.app);qtm_connect_maya.app.start()",
    )
    pmc.shelfButton(
        label="Stop streaming",
        parent=shelf_layout,
        command="import qtm_connect_maya.app;reload(qtm_connect_maya.app);qtm_connect_maya.app.stop()",
        image1=stop_icon
    )
