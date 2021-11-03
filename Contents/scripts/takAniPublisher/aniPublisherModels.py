"""
Author: Tak
Website: https://tak.ta-note.com
Description: Exports skeleton joints and blendshapes animation data.
"""

import maya.OpenMaya as om
import pymel.core as pm
import maya.cmds as cmds
import maya.mel as mel

import os
import glob
import re

from . import utils

reload(utils)


class AniPublisher(object):
    NAME = 'Tak Ani Publisher'
    VERSION = '2.0.0'
    CONFLICT_NAMES = ['Root', 'Geometry', 'Model']

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

            cmds.refresh(suspend=True)

            cmds.select(pubItem.exportNodes, r=True)
            utils.setFBXExportOptions(pubItem.startFrame, pubItem.endFrame, pubItem.exportBlendshape)
            fullPathFilename = os.path.join(pubItem.exportDirectory, pubItem.filename).replace('\\', '/') + '.fbx'
            mel.eval('FBXExport -f "{0}" -s'.format(fullPathFilename))

            cmds.refresh(suspend=False)

            self._editFBX(fullPathFilename, pubItem)
            om.MGlobal.displayInfo('"{0}" animation has exported successfully.'.format(pubItem.namespace))

        self._recoverScenePlaybackRange()

        return True

    def _setPlaybackRange(self, pubItem):
        pm.env.setMinTime(pubItem.startFrame)
        pm.env.setMaxTime(pubItem.endFrame)

    def _recoverScenePlaybackRange(self):
        pm.env.setMinTime(self._minTime)
        pm.env.setMaxTime(self._maxTime)

    def _editFBX(self, fbxFile, pubItem):
        performChecker = utils.PerformanceChecker()

        with open(fbxFile, 'r') as f:
            contents = f.read()

        # Show joints
        performChecker.start('Show Joint')
        subStrs = ''
        pattern = re.compile(r'\tModel:.*?"LimbNode" {.*?}.*?}\n', re.DOTALL)
        finds = pattern.findall(contents)
        if finds:
            for find in finds:
                subStr = re.sub(r'(\tP: "Show".*?),\d', r'\1,1', find)
                subStrs += subStr
        contents = contents.replace(''.join(finds), subStrs)
        performChecker.end()

        # Parent root joint to the world
        performChecker.start('Parent Root Joint to World')
        rootJnt = [item for item in pubItem.exportNodes if pm.nodeType(item) == 'joint'][0]
        contents = re.sub(r'(\t;Model.*?{0}, Model::).*?(\n\tC: "OO",\d+),\d+\n'.format(rootJnt), r'\1RootNode\2,0\n', contents)
        performChecker.end()

        # If bake space is local space, set root joint to default state
        if pubItem.bakeSpace == 'local':
            # Set default root joint state
            newRootJntProperties = '''
                        P: "PreRotation", "Vector3D", "Vector", "",-90,0,0
                        P: "RotationActive", "bool", "", "",1
                        P: "InheritType", "enum", "", "",1
                        P: "ScalingMax", "Vector3D", "Vector", "",0,0,0
                        P: "Show", "bool", "", "",1
                        P: "DefaultAttributeIndex", "int", "Integer", "",0
                        P: "Lcl Translation", "Lcl Translation", "", "A",0,0,0
                        P: "Lcl Rotation", "Lcl Rotation", "", "A+",0,0,0
            '''
            oldRootJntBlock = re.search(r'\tModel:.*?"Model::.*?%s", "LimbNode" {.*?{(.*?)\t\t}.*?}\n' % (rootJnt), contents, re.DOTALL)
            oldRootJntProperties = oldRootJntBlock.group(1)
            newRootJntBlock = oldRootJntBlock.group().replace(oldRootJntProperties, newRootJntProperties)
            contents = contents.replace(oldRootJntBlock.group(), newRootJntBlock)

            contents = re.sub(r'\t;AnimCurveNode::.*?Model::.*?%s\n\tC: "OP".*?\n' %(rootJnt), '', contents)  # Remove root joint anim curves

        # Remove namespace
        performChecker.start('Remove Namespace')
        contents = contents.replace(':'+pubItem.namespace, '')
        performChecker.end()

        with open(fbxFile, 'w') as f:
            f.write(contents)


class PublishItem(object):
    BAKE_SPACES = ['world', 'local']
    DEFAULT_IMAGE = ':noPreview.png'
    IMAGE_EXT = 'jpg'

    def __init__(self, refNode=None, exportDirectory='', filename='', enable=True, bakeSpace='world', startFrame=0, endFrame=1, exportSkeleton=True, exportBlendshape=False):
        self.refNode = refNode
        self.exportDirectory = exportDirectory
        self.filename = filename
        self.enable = enable
        self.bakeSpace = bakeSpace
        self.startFrame = startFrame
        self.endFrame = endFrame
        self.exportSkeleton = exportSkeleton
        self.exportBlendshape = exportBlendshape

        self.refFile = None
        self.image = None
        self.namespace = None
        self.exportNodes = None

        self.settings = utils.getSettings()

        self.__getReferenceInfo()

    def __getReferenceInfo(self):
        self.refFile = cmds.referenceQuery(self.refNode, filename=True)
        self.image = PublishItem.getImage(self.refFile)
        self.namespace = cmds.referenceQuery(self.refNode, namespace=True).split(':')[-1]
        self.exportNodes = cmds.sets('{0}:{1}'.format(self.namespace, self.settings['exportSetName']), q=True)
        self.exportDirectory = self.getExportDirectory(self.refFile)
        self.filename = self.namespace
        self.startFrame = cmds.playbackOptions(q=True, min=True)
        self.endFrame = cmds.playbackOptions(q=True, max=True)

    @staticmethod
    def getImage(refFile):
        image = PublishItem.DEFAULT_IMAGE

        rigDirectory = os.path.dirname(refFile)

        assetImages = glob.glob('{0}/*.{1}'.format(rigDirectory, PublishItem.IMAGE_EXT))
        if assetImages:
            image = assetImages[0]

        return image

    def getExportDirectory(self, refFile):
        exportDirectory = None

        if self.settings['useCustomExportDirectory']:
            exportDirectory = self.settings['customExportDirectory']
        else:
            parentDirLevel = 2
            rigDirectory = os.path.dirname(refFile)
            exportDirectory = rigDirectory.rsplit('/', parentDirLevel)[0] + '/Animations'

        return exportDirectory

    @staticmethod
    def getFilename(refFile):
        filename = os.path.basename(refFile).split('.')[0]

        curScenePath = cmds.file(q=True, sn=True)
        if curScenePath:
            filename = os.path.basename(curScenePath).split('.')[0]

        return filename
