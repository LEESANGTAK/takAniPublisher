"""
Author: TAK
Website: https://ta-note.com
Description: Exports skeleton and blendshapes animation data.
"""

import os
import re
import glob

import pymel.core as pm

from . import logger
from . import utils
from . import constants

reload(utils)  # type: ignore
reload(constants)  # type: ignore


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
        pm.refresh(suspend=True)

        for pubItem in self.publishItems:
            if not pubItem.enable:
                continue
            if not pubItem.skeletonRoot:
                logger.error('"{0}" is not specified skeleton root node.'.format(pubItem.namespace))
                continue

            skelRoot = pm.PyNode(pubItem.skeletonRoot)
            skelRootLoc, skelRootInheritsTransformValOrig = self.makeSkeletonRootInWorld(skelRoot)

            for clip in pubItem.clips:
                if not clip.enable:
                    continue

                self._setPlaybackRange(clip)

                # Select nodes to export
                if pubItem.exportSkeleton:
                    pm.select(pubItem.skeletonRoot, r=True)
                if pubItem.exportModel:
                    pm.select(pubItem.modelRoot, add=True)

                # Export fbx
                utils.setFBXExportOptions(clip.startFrame, clip.endFrame)
                fullPathFilename = os.path.join(pubItem.exportDirectory, clip.name).replace('\\', '/') + '.fbx'
                pm.mel.eval('FBXExport -f "{0}" -s'.format(fullPathFilename))

                # Edit fbx file
                self._editFBX(fullPathFilename, pubItem)
                logger.info('"{0}" clip has exported successfully.'.format(clip.name))

            # Restore skeletonRoot state
            if skelRootLoc:
                pm.delete(skelRootLoc)
            skelRoot.inheritsTransform.set(skelRootInheritsTransformValOrig)

        self._recoverScenePlaybackRange()

        pm.refresh(suspend=False)

        return True

    def makeSkeletonRootInWorld(self, skelRoot):
        skelRootLoc = None
        skelRootInheritsTransformValOrig = skelRoot.inheritsTransform.get()
        isParentConst = utils.isConstrained(skelRoot)
        if not isParentConst:  # Turning off inheritsTransform will make skeletonRoot jump to other position if not constrained
            skelRootLoc = pm.spaceLocator(n='{0}_loc'.format(skelRoot))
            pm.matchTransform(skelRootLoc, skelRoot)
            pm.parentConstraint(skelRootLoc, skelRoot)
        skelRoot.inheritsTransform.set(False)

        return skelRootLoc, skelRootInheritsTransformValOrig

    def _setPlaybackRange(self, clip):
        pm.env.setMinTime(clip.startFrame)
        pm.env.setMaxTime(clip.endFrame)

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

        # Parent export nodes to the world
        contents = re.sub(r'(\t;Model.*?{0}, Model::).*?(\n\tC: "OO",\d+),\d+\n'.format(pubItem.skeletonRoot), r'\1RootNode\2,0\n', contents)
        contents = re.sub(r'(\t;Model.*?{0}, Model::).*?(\n\tC: "OO",\d+),\d+\n'.format(pubItem.modelRoot), r'\1RootNode\2,0\n', contents)

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

            # Remove skeletonRoot anim curves
            contents = re.sub(r'\t;AnimCurveNode::.*?Model::.*?%s\n\tC: "OP".*?\n' % (pubItem.skeletonRoot), '', contents)

        # Remove topTransforms
        for topTransform in pubItem.topTransforms:
            srchObj = re.search(r'\tModel:.*?"Model::%s", "\w+?" {.*?{.*?\t\t}.*?}\n' % (topTransform), contents, re.DOTALL)
            if srchObj:
                contents = contents.replace(srchObj.group(), '')

        # Remove namespace
        contents = contents.replace(pubItem.namespace+':', '')

        with open(fbxFile, 'w') as f:
            f.write(contents.encode('utf-8'))


class PublishItem(object):
    DEFAULT_IMAGE = ':noPreview.png'
    IMAGE_EXT = 'jpg'

    @staticmethod
    def getImage(refFile):
        image = PublishItem.DEFAULT_IMAGE

        rigDirectory = os.path.dirname(refFile)

        assetImages = glob.glob('{0}/*.{1}'.format(rigDirectory, PublishItem.IMAGE_EXT))
        if assetImages:
            image = assetImages[0]

        return image

    def __init__(self, refNode):
        self.exportDirectory = ''
        self.enable = True
        self.moveToOrigin = False
        self.exportSkeleton = True
        self.exportModel = False

        self.refNode = refNode
        self.refFile = None
        self.image = None
        self.namespace = None
        self.modelRoot = None
        self.skeletonRoot = None
        self.topTransforms = []

        self.clips = []

        self.settings = utils.getSettings()

        self.__getReferenceInfo()

    def __getReferenceInfo(self):
        self.refFile = pm.referenceQuery(self.refNode, filename=True)
        self.image = PublishItem.getImage(self.refFile)
        self.namespace = pm.referenceQuery(self.refNode, namespace=True, shortName=True)
        self.exportDirectory = self.getExportDirectory(self.refFile)
        self.topTransforms = self.getTopTransforms(self.refFile)

    def getExportDirectory(self, refFile):
        exportDirectory = None

        exportDirectory = os.path.dirname(refFile)

        if self.settings['useCustomExportDirectory']:
            exportDirectory = self.settings['customExportDirectory']

        return exportDirectory

    def getTopTransforms(self, refFile):
        topTransforms = []
        for node in pm.referenceQuery(refFile, nodes=True, dagPath=True):
            if pm.nodeType(node) == 'transform':
                node = pm.PyNode(node)
                if not node.getParent():
                    topTransforms.append(node)
        return topTransforms


class Clip(object):
    def __init__(self):
        self.enable = False

        self.name = None
        self.startFrame = None
        self.endFrame = None
