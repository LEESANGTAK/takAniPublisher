import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pm

import os
import json
import time

from . import constants


def removeNamespace(node):
    newName = ''
    newName = node.split(':')[-1]
    return newName


def restoreRootTransform(rootJoint):
    attrs = ['translate', 'rotate', 'jointOrient']
    axes = ['X', 'Y', 'Z']

    for attr in attrs:
        for axis in axes:
            channelInputs = cmds.listConnections('{0}.{1}{2}'.format(rootJoint, attr, axis))
            if channelInputs:
                cmds.delete(channelInputs)

            attrName = attr + axis
            if attrName == 'jointOrientX':
                cmds.setAttr('{0}.{1}'.format(rootJoint, attrName), -90)
            else:
                cmds.setAttr('{0}.{1}'.format(rootJoint, attrName), 0)


def loadFBXPlugin():
    if not cmds.pluginInfo('fbxmaya', q=True, loaded=True):
        cmds.loadPlugin('fbxmaya')


def setFBXExportOptions(startFrame, endFrame):
    loadFBXPlugin()

    mel.eval('FBXResetExport;')

    mel.eval('FBXExportSmoothingGroups -v false;')
    mel.eval('FBXExportTangents -v false;')
    mel.eval('FBXExportSmoothMesh -v false;')
    mel.eval('FBXExportTriangulate -v false;')

    mel.eval('FBXExportAnimationOnly -v false;')
    mel.eval('FBXExportAxisConversionMethod convertAnimation;')
    mel.eval('FBXExportBakeComplexAnimation -v true;')
    mel.eval('FBXExportBakeComplexStart -v {0};'.format(startFrame))
    mel.eval('FBXExportBakeComplexEnd -v {0};'.format(endFrame))
    mel.eval('FBXExportBakeComplexStep -v 1;')
    mel.eval('FBXExportQuaternion -v resample;')
    mel.eval('FBXExportBakeResampleAnimation -v false;')
    mel.eval('FBXExportApplyConstantKeyReducer -v false;')

    mel.eval('FBXExportSkins -v false;')
    mel.eval('FBXExportShapes -v false;')

    mel.eval('FBXExportLights -v false;')
    mel.eval('FBXExportCameras -v false;')
    mel.eval('FBXExportInstances -v false;')
    mel.eval('FBXExportCacheFile -v false;')
    mel.eval('FBXExportEmbeddedTextures -v false;')

    mel.eval('FBXExportColladaSingleMatrix true;')
    mel.eval('FBXExportColladaTriangulate false;')

    mel.eval('FBXExportConstraints -v false;')
    mel.eval('FBXExportInputConnections -v false;')
    mel.eval('FBXExportSkeletonDefinitions -v true;')

    mel.eval('FBXExportUpAxis y;')
    mel.eval('FBXExportScaleFactor 1.0;')
    mel.eval('FBXExportConvertUnitString cm;')

    mel.eval('FBXExportInAscii -v true;')
    mel.eval('FBXExportReferencedAssetsContent -v false;')
    mel.eval('FBXExportUseSceneName -v false;')
    mel.eval('FBXExportFileVersion -v FBX202000;')


def showJoints(joints):
    for jnt in joints:
        cmds.setAttr('{0}.drawStyle'.format(jnt), 0)


def getSettings():
    settingsFile = constants.USER_SETTING_FILE if os.path.exists(constants.USER_SETTING_FILE) else constants.DEFAULT_SETTING_FILE
    with open(settingsFile, 'r') as f:
        settings = json.load(f)
    return settings


def isConstrained(obj):
    result = False
    constraints = obj.inputs(type='constraint')
    if constraints:
        for const in constraints:
            if const.nodeType() in ['parentConstraint', 'pointConstraint', 'orientConstraint']:
                result = True
    return result


class PerformanceChecker(object):
    def __init__(self):
        super(PerformanceChecker, self).__init__()
        self._startTime = None
        self._label = None

    def start(self, label):
        self._startTime = time.time()
        self._label = label

    def end(self):
        duration = time.time() - self._startTime
        pm.displayInfo('"{0}" job took {1}s.'.format(self._label, round(duration, 2)))
