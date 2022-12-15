import maya.cmds as cmds

def WashLocators():

    nodes = cmds.ls( selection=True, type='dagNode')
    n = str(nodes[0])
    markerset = "Washed"
    sep = ' '
    if ':' in n:
        sep = ':'
        markerset = f"Washed_{n.split(sep)[0]}"
    elif '_' in n:
        sep = '_'
        markerset = f"Washed_{n.split(sep)[0]}"


    gMarkers = cmds.group(em=True,name=f"{markerset}:Markers")
    for oldloc in nodes:
        cn = cmds.xform( str(oldloc), q=True, matrix=True, ws=True)
        x = cn[12]
        y = cn[13]
        z = cn[14]
        #print x, y, z
        NewLoc = f"{markerset}:{str(oldloc).split(sep)[-1]}"
        loc = cmds.spaceLocator(name=NewLoc)
        cmds.setAttr("%s.overrideEnabled" % NewLoc, 1)
        cmds.setAttr("%s.overrideColor" % NewLoc, 22)
        cmds.select(loc)
        cmds.move(x,y,z)
        cmds.scale(2,2,2)
        cmds.select(gMarkers)
        cmds.parent(loc)
