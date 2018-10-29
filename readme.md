# QTM Connect for Maya

Stream skeleton and marker data from QTM through the QTM real-time protocol.

## Installation
1. Clone this repo to your machine.
2. Clone [qualisys_python_sdk](https://github.com/qualisys/qualisys_python_sdk) into the modules folder.
3. Edit your Maya.env file. Add the following line: `pythonpath=<path_to_qtm_connect_maya>/..`.
4. Start/restart Maya.
5. In Maya, open the script editor and run the following Python code:  
`import qtm_connect_maya;import qtm_connect_maya.mayaui;qtm_connect_mata.mayaui.install()`

## Streaming skeleton data
To stream skeleton data you must first define a skeleton in QTM. Do this by clicking the `Calibrate skeleton` button in QTM.

1. In the QTM_Connect shelf, click on the QTM Connect icon to open the dialog.
2. Enter the hostname of your QTM machine and click Connect.
3. Click `Stream from QTM` to start streaming skeleton data.

### T-Pose
You can go to the T-pose of your skeleton by selecting the respective
skeleton in the list and clicking the `Go to T-Pose button`.

## Streaming marker data
1. In the QTM_Connect shelf, click on the QTM Connect icon to open the dialog.
2. Enter the hostname of your QTM machine and click Connect.
3. Click `Stream from QTM` to start streaming marker data.

### Grouping markers
If you have a large number markers it can be useful to group them. For each
group you create a transform node will be created to which the markers will
be parented to.

1. Enter the name of the group.
2. Select the markers in the marker list.
3. Click the Group button.