import maya.api.OpenMaya as om

class MayaUtil:
    @staticmethod
    def get_node_by_name(name):
        dagIterator = om.MItDag()
        dagNodeFn = om.MFnDagNode()

        while (not dagIterator.isDone()):
            dagObject = dagIterator.currentItem()
            dagNodeFn.setObject(dagObject)

            if dagNodeFn.name() == name:
                return dagObject

            dagIterator.next()

        return None