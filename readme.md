# QTM Connect for Maya

Stream skeleton, rigid bodies and marker data from QTM through the QTM real-time protocol.

![QTM Connect dialog screenshot](./assets/qtm_connect_maya_dialog.png "QTM Connect dialog")

## Installation
Automatic
1. Download the repo to your machine
2. Go to qtm_connect_maya\installer and run create-installer.bat
3. Make sure Maya is closed, go to qtm_connect_maya\installer\output and run installer.exe (if you have a custom path for your Maya folder you might be prompted to specify it during the installation)

Manual
1. Clone this repo to your machine.
2. Clone [qualisys_python_sdk](https://github.com/qualisys/qualisys_python_sdk) into the modules folder.
3. Edit your Maya.env file available in one of your Maya folders. Add the following line: `pythonpath=<path_to_qtm_connect_maya>/..`.
4. Start/restart Maya.
5. In Maya, open the script editor and run the following Python code:  
`import qtm_connect_maya;import qtm_connect_maya.mayaui;qtm_connect_maya.mayaui.install()`

## Streaming skeleton data
To stream skeleton data you must first define a skeleton in QTM. Do this by clicking the `Calibrate skeleton` button in QTM.

1. Ensure that the real-time server in QTM is streaming data. See [Streaming data from QTM](#streaming-data-from-qtm)
2. In Maya's `QTM_Connect` shelf, click on the QTM Connect icon to open the dialog.
3. Enter the hostname of your QTM machine and click `Connect`.
4. Click `Stream from QTM` to start streaming skeleton data.

### T-Pose
You can go to the T-pose of your skeleton by selecting the respective
skeleton in the list and clicking the `Go to T-Pose` button.

### HumanIK
The naming convention used by the joints is recognized by HumanIK. To
automatically map joints to a HumanIK character definition you need to charcaterize your skeleton.
To do so, go to the HumanIk pane, click on 'Create Character Definition', click on one of the joints of your skeleton (in the 3D view), load the `HIK`
template (folder icon in the HumanIK pane) and enter the skeleton prefix to only focus on the bones of your skeleton (useful if more than one skeletons are streamed).
![HumanIK pane screenshot](./assets/HumanIK_pane.png "HumanIK pane")

## Streaming marker data
1. Ensure that the real-time server in QTM is streaming data. See [Streaming data from QTM](#streaming-data-from-qtm).
2. In the `QTM_Connect` shelf, click on the QTM Connect icon to open the dialog.
3. Enter the hostname of your QTM machine and click `Connect`.
4. Check the `Markers` checkbox to enable marker streaming.
4. Click `Stream from QTM` to start streaming marker data.

### Grouping markers
If you have a large number markers it can be useful to group them. For each
group you create a transform node will be created to which the markers will
be parented to.

1. Enter the name of the group.
2. Select the markers you want to group in the marker list.
3. Click the `Group` button.

## Streaming rigid body data
To stream rigid bodies you must first define rigid bodies in QTM. See [Defining rigid bodies in QTM](#defining-rigid-bodies-in-qtm).

1. Ensure that the real-time server in QTM is streaming data. See [Streaming data from QTM](#streaming-data-from-qtm).
2. In the `QTM_Connect` shelf, click on the QTM Connect icon to open the dialog.
3. Enter the hostname of your QTM machine and click `Connect`.
4. Check the `Rigid bodies` checkbox to enable rigid body streaming.
4. Click `Stream from QTM` to start streaming rigid body data.

## Streaming data from QTM

###  Live streaming
In QTM:

1. Go to `Project Options` > `Processing` > `Real-time actions`, to ensure that
real-time processing is enabled.
2. Go to `File` > `New` to start streaming live data.

### Streaming using pre-recorded file
In QTM:

1. Open the file you want to stream.
2. Go to `Play` > `Play with Real-Time Output`

## Defining rigid bodies in QTM
In QTM:

1. Select three or more markers that make up a rigid body.
2. Open the context menu by right clicking and run `Define rigid body (6DOF)` > `Current Frame` / `Average of frame`.

Rigid bodies can also be edited in `Project Options` > `Processing` > `6DOF Tracking`.

## Update Qualisys Python SDK:
In terminal, run:

`git subtree pull --prefix modules/qualisys_python_sdk https://github.com/qualisys/qualisys_python_sdk.git <branch/commit> --squash`

where `<branch/commit>` is either a specific branch, or a commit hash.