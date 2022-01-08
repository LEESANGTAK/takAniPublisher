"""
Author: TAK
Website: https://ta-note.com
Description: Exports skeleton and blendshapes animation data.
"""

import os
import re
import logging

import pymel.core as pm

from . import utils
reload(utils)  # type: ignore


logger = logging.getLogger('TAK Ani Publisher')
logger.setLevel('DEBUG')


class AniPublisher(object):
    def __init__(self):
        super(AniPublisher, self).__init__()
        self.publishItems = []
        self._minTime = pm.env.minTime
        self._maxTime = pm.env.maxTime

    def addItem(self, pubItem):
        if not isinstance(pubItem, PublishItem):
            raise RuntimeError('"{0}" is not an instance of class PublishItem.'.format(pubItem))
        self.publishItems.append(pubItem)

    def setItems(self, pubItems):
        self.publishItems = pubItems

    def publish(self):
        for pubItem in self.publishItems:
            if not pubItem.enable:
                continue

            self._setPlaybackRange(pubItem)

            pm.refresh(suspend=True)

            # Make skeletonRoot channel values in world
            skelRoot = pm.PyNode(pubItem.skeletonRoot)
            skelRootLoc = None
            skelRootInheritsTransformValOrig = skelRoot.inheritsTransform.get()
            isConst = utils.isConstrained(skelRoot)
            if not isConst:  # Turning off inheritsTransform will make skeletonRoot jump to other position if not constrained
                skelRootLoc = pm.spaceLocator(n='{0}_loc'.format(skelRoot))
                pm.matchTransform(skelRootLoc, skelRoot)
                pm.parentConstraint(skelRootLoc, skelRoot)
                pm.scaleConstraint(skelRootLoc, skelRoot)
            skelRoot.inheritsTransform.set(False)

            # Select nodes to export
            pm.select(pubItem.skeletonRoot, r=True)
            if pubItem.modelRoot:
                pm.select(pubItem.modelRoot, add=True)

            # Export fbx
            utils.setFBXExportOptions(pubItem.startFrame, pubItem.endFrame)
            fullPathFilename = os.path.join(pubItem.exportDirectory, pubItem.filename).replace('\\', '/') + '.fbx'
            pm.mel.eval('FBXExport -f "{0}" -s'.format(fullPathFilename))

            # Restore skeletonRoot state
            if skelRootLoc:
                pm.delete(skelRootLoc)
            skelRoot.inheritsTransform.set(skelRootInheritsTransformValOrig)

            pm.refresh(suspend=False)

            # Edit fbx file
            self._editFBX(fullPathFilename, pubItem)
            logger.info('"{0}" animation has exported successfully.'.format(pubItem.namespace))

        self._recoverScenePlaybackRange()

        return True

    def _setPlaybackRange(self, pubItem):
        pm.env.setMinTime(pubItem.startFrame)
        pm.env.setMaxTime(pubItem.endFrame)

    def _recoverScenePlaybackRange(self):
        pm.env.setMinTime(self._minTime)
        pm.env.setMaxTime(self._maxTime)

    def _editFBX(self, fbxFile, pubItem):
        with open(fbxFile, 'r') as f:
            contents = unicode(f.read(), 'utf-8')  # type: ignore

        # Show joints
        subStrs = ''
        pattern = re.compile(r'\tModel:.*?"LimbNode" {.*?}.*?}\n', re.DOTALL)
        finds = pattern.findall(contents)
        if finds:
            for find in finds:
                subStr = re.sub(r'(\tP: "Show".*?),\d', r'\1,1', find)
                subStrs += subStr
        contents = contents.replace(''.join(finds), subStrs)

        # Parent skeletonRoot to the world
        contents = re.sub(r'(\t;Model.*?{0}, Model::).*?(\n\tC: "OO",\d+),\d+\n'.format(pubItem.skeletonRoot), r'\1RootNode\2,0\n', contents)

        if pubItem.moveToOrigin:
            jointOrientStr = '0,0,0'
            skelRoot = pm.PyNode(pubItem.skeletonRoot)
            if skelRoot.nodeType() == 'joint':
                jointOrient = skelRoot.jointOrient.get()
                jointOrientStr = '{0},{1},{2}'.format(jointOrient.x, jointOrient.y, jointOrient.z)
            skelRootPropertyNew = '''
                        P: "PreRotation", "Vector3D", "Vector", "",{0}
                        P: "RotationActive", "bool", "", "",1
                        P: "InheritType", "enum", "", "",1
                        P: "ScalingMax", "Vector3D", "Vector", "",0,0,0
                        P: "Show", "bool", "", "",1
                        P: "DefaultAttributeIndex", "int", "Integer", "",0
                        P: "Lcl Translation", "Lcl Translation", "", "A",0,0,0
                        P: "Lcl Rotation", "Lcl Rotation", "", "A+",0,0,0
            '''.format(jointOrientStr)
            skelRootOldBlock = re.search(r'\tModel:.*?"Model::.*?%s", "\w+?" {.*?{(.*?)\t\t}.*?}\n' % (pubItem.skeletonRoot), contents, re.DOTALL)
            skelRootPropertyOld = skelRootOldBlock.group(1)
            skelRootNewBlock = skelRootOldBlock.group().replace(skelRootPropertyOld, skelRootPropertyNew)
            contents = contents.replace(skelRootOldBlock.group(), skelRootNewBlock)

            contents = re.sub(r'\t;AnimCurveNode::.*?Model::.*?%s\n\tC: "OP".*?\n' % (pubItem.skeletonRoot), '', contents)  # Remove root joint anim curves

        # Remove namespace
        contents = contents.replace(':'+pubItem.namespace, '')

        with open(fbxFile, 'w') as f:
            f.write(contents.encode('utf-8'))


class PublishItem(object):
    def __init__(self, refNode, exportDirectory='', filename='', enable=True, moveToOrigin=False, startFrame=0, endFrame=1):
        self.exportDirectory = exportDirectory
        self.filename = filename
        self.enable = enable
        self.moveToOrigin = moveToOrigin
        self.startFrame = startFrame
        self.endFrame = endFrame

        self.refNode = refNode
        self.refFile = None
        self.namespace = None
        self.modelRoot = None
        self.skeletonRoot = None

        self.settings = utils.getSettings()

        self.__getReferenceInfo()

    def __getReferenceInfo(self):
        self.refFile = pm.referenceQuery(self.refNode, filename=True)
        self.namespace = pm.referenceQuery(self.refNode, namespace=True, shortName=True)
        self.exportDirectory = self.getExportDirectory(self.refFile)
        self.filename = self.namespace
        self.startFrame = pm.env.minTime
        self.endFrame = pm.env.maxTime

    def getExportDirectory(self, refFile):
        exportDirectory = None

        exportDirectory = os.path.dirname(refFile)

        if self.settings['useCustomExportDirectory']:
            exportDirectory = self.settings['customExportDirectory']

        return exportDirectory
