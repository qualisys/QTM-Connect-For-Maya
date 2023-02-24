import maya.cmds as cmds

#
# Set the attributes in the "attrs" list that you want to add
# If you want the parent entered as the coupled segment, Set
# parentAsDefault to True
#
#attrs = ['ZR1','ZR2']
#attrs = ['ZR1','ZR2','YR1','YR2']
#attrs = ['ZR1','YR1','YR2']
#attrs = ['ZR1','YR1','XR1']
#attrs = ['ZR1']
#attrs = ['ZR1','ZR2','YR1','YR2']
#attrs = ['XR1','XR2']
attrs = ['YR1']
parentAsDefault = True
couplings = {'XR1': ("XRot_CP1_Coeff", 0.7, "XRot_CP1_Segment", ""),
             'XR2': ("XRot_CP2_Coeff", 0.3, "XRot_CP2_Segment", ""),
             'YR1': ("YRot_CP1_Coeff", 0.7, "YRot_CP1_Segment", ""),
             'YR2': ("YRot_CP2_Coeff", 0.3, "YRot_CP2_Segment", ""),
             'ZR1': ("ZRot_CP1_Coeff", 0.7, "ZRot_CP1_Segment", ""),
             'ZR2': ("ZRot_CP2_Coeff", 0.3, "ZRot_CP2_Segment", "")}

def AddCoupling():
    dags = cmds.ls(selection=True)

    for nodes in dags:
        n = str(nodes)
        for a in attrs:
            (Cattr,Cdefault,Sattr, Sdefault) = couplings[a]

            cmds.addAttr (n, ln=Cattr, defaultValue=Cdefault)
            cmds.addAttr (n, ln=Sattr, dt="string")
            if parentAsDefault:
                myParent = cmds.listRelatives(nodes, parent=True)
                if len(myParent)>0:
                    mp = myParent[0]
                    slist = mp.split(':')
                    Sdefault = slist[len(slist)-1]
                    #print(f"Parent is {Sdefault}")            
                    cmds.setAttr (f"{n}.{Sattr}", Sdefault,type="string")
        
AddCoupling()
