from imp import reload

import pymel.core as pm

from . import aniPublisherModels as apMdl; reload(apMdl)
from . import aniPublisherUI as apUI; reload(apUI)
from . import utils; reload(utils)


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
            for node in pm.referenceQuery(refNode, nodes=True, dagPath=True):
                if pm.nodeType(node) == 'joint':
                    rigRefNodes.append(refNode)
                    break

        self.__rigRefNodes = rigRefNodes

    def __getValidRefNodes(self):
        validRefNodes = []

        refNodes = pm.ls(type='reference')
        for refNode in refNodes:
            try:  # Empty reference node
                pm.referenceQuery(refNode, filename=True)
            except RuntimeError:
                continue

            if not pm.referenceQuery(refNode, isLoaded=True):  # Not loaded refrence node
                continue

            validRefNodes.append(refNode)

        self.__validRefNodes = validRefNodes
