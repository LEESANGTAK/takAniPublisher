import maya.cmds as cmds
import pymel.core as pm

from . import aniPublisherModels as apMdl
from . import aniPublisherUI as apUI

from . import utils

reload(apMdl)
reload(apUI)
reload(utils)


class AniPublisherCtrl(object):
    def __init__(self):
        self.aniPub = None
        self.aniPubUI = None
        self.settings = utils.getSettings()

        self.__validRefNodes = []
        self.__rigRefNodes = []

    def showUI(self):
        self.__getValidRefNodes()
        self.__getRigRefNodes()

        self.aniPub = apMdl.AniPublisher()

        for refNode in self.__rigRefNodes:
            pubItem = apMdl.PublishItem(refNode)
            self.aniPub.addItem(pubItem)

        self.aniPubUI = apUI.AniPublisherUI(self.aniPub)

        self.aniPubUI.show()

    def __getRigRefNodes(self):
        rigRefNodes = []

        for refNode in self.__validRefNodes:
            refNamespace = cmds.referenceQuery(refNode, namespace=True)
            if cmds.objExists('{0}:{1}'.format(refNamespace,  self.settings['exportSetName'])):
                rigRefNodes.append(refNode)

        self.__rigRefNodes = rigRefNodes

    def __getValidRefNodes(self):
        validRefNodes = []

        refNodes = cmds.ls(type='reference')
        for refNode in refNodes:
            try:  # Empty reference node
                cmds.referenceQuery(refNode, filename=True)
            except:
                continue

            if not cmds.referenceQuery(refNode, isLoaded=True):  # Not loaded refrence node
                continue

            validRefNodes.append(refNode)

        self.__validRefNodes = validRefNodes
