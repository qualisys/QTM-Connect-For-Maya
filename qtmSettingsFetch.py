

import qqtmrt
import xml.etree.ElementTree as ET
import copy

def main():
    q = qqtmrt.QQtmRt()
    settings = None
    if (q.connect_to_qtm(host="10.211.55.3")):
        settings = q.get_parameters("skeletons")
        ans = q.takeControl()
        dom = ET.fromstring(settings)
        dom.tag = "QTM_Settings"
        skeletons = dom.find("Skeletons")
        skeleton = copy.deepcopy(dom.find("./Skeletons[Skeleton]/"))
        skeleton.set("Name","AH3")
        skeletons.append(skeleton)
        #dom.find("Skeletons")
        settings = ET.tostring(dom, encoding='unicode')
        answer = q.set_parameters(settings=settings)
        q.disconnect()
    print(answer)
    #print(ET.dump(dom))
    for child in dom.find("Skeletons"):
        print(child)
        print(child.attrib)

    


if __name__ == '__main__':
    main()