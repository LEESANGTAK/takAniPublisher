import maya.OpenMayaUI as omui

import os
from shiboken2 import wrapInstance
from PySide2 import QtWidgets, QtCore, QtGui

from . import logger
from . import settingsUI
from . import constants
from . import aniPublisherModels as aniPubModels

reload(settingsUI)  # type: ignore
reload(aniPubModels)  # type: ignore


def getMayaMainWin():
    mayaMainWinWidget = None

    mayaMainWinPtr = omui.MQtUtil.mainWindow()
    mayaMainWinWidget = wrapInstance(long(mayaMainWinPtr), QtWidgets.QWidget)  # type: ignore

    return mayaMainWinWidget


class AniPublisherUI(QtWidgets.QDialog):
    def __init__(self, aniPublisher=None, parent=getMayaMainWin()):
        super(AniPublisherUI, self).__init__(parent)

        self.aniPubObj = aniPublisher
        self.publishItemWidgets = []

        self.setWindowTitle('{0}_Personal - {1}'.format(constants.NAME, constants.VERSION))
        self.setWindowIcon(QtGui.QIcon(':out_timeEditorAnimSource.png'))
        self.resize(900, 1000)

        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.setInitialState()

    def createWidgets(self):
        self.menuBar = QtWidgets.QMenuBar()
        self.editMenu = self.menuBar.addMenu('Edit')
        self.settingsAction = self.editMenu.addAction('Settings')

        self.itemMasterChkBox = QtWidgets.QCheckBox()
        self.itemMasterMoveToOriginLabel = QtWidgets.QLabel('Move to Origin: ')
        self.itemMasterMoveToOriginChkBox = QtWidgets.QCheckBox()
        self.itemMasterExportDirLabel = QtWidgets.QLabel('Export Directory: ')
        self.itemMasterExportDirLe = QtWidgets.QLineEdit()
        self.itemMasterGetDirectoryBtn = QtWidgets.QPushButton()

        for item in self.aniPubObj.publishItems:
            self.publishItemWidgets.append(PublishItemWidget(item))

        self.publishBtn = QtWidgets.QPushButton('Publish Animation')

    def createLayouts(self):
        mainLayout = QtWidgets.QVBoxLayout(self)

        mainLayout.addWidget(self.menuBar)

        itemMasterLayout = QtWidgets.QHBoxLayout()
        itemMasterLayout.addWidget(self.itemMasterChkBox)
        itemMasterLayout.addWidget(self.itemMasterMoveToOriginLabel)
        itemMasterLayout.addWidget(self.itemMasterMoveToOriginChkBox)
        itemMasterLayout.addWidget(self.itemMasterExportDirLabel)
        itemMasterLayout.addWidget(self.itemMasterExportDirLe)
        itemMasterLayout.addWidget(self.itemMasterGetDirectoryBtn)
        mainLayout.addLayout(itemMasterLayout)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollWidget = QtWidgets.QWidget()
        scrollWidget.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        scrollLayout = QtWidgets.QVBoxLayout()

        for publishItemWidget in self.publishItemWidgets:
            scrollLayout.addWidget(publishItemWidget)
            AniPublisherUI.addSeparator(scrollLayout)

        scrollWidget.setLayout(scrollLayout)
        scrollArea.setWidget(scrollWidget)
        mainLayout.addWidget(scrollArea)

        mainLayout.addWidget(self.publishBtn)

    def createConnections(self):
        self.settingsAction.triggered.connect(self.showSettingsUI)

        self.itemMasterChkBox.stateChanged.connect(self.setItemWidgetsEnable)
        self.itemMasterMoveToOriginChkBox.stateChanged.connect(self.setItemWidgetsMoveToOrigin)
        self.itemMasterGetDirectoryBtn.clicked.connect(lambda: self.setDirectoryPath(self.itemMasterExportDirLe))
        self.itemMasterExportDirLe.textChanged.connect(self.setItemWidgetsExportDir)
        self.publishBtn.clicked.connect(self.publishAnimation)

    def showSettingsUI(self):
        setUI = settingsUI.SettingsUI(self)
        setUI.show()

    def setInitialState(self):
        self.itemMasterChkBox.setMinimumWidth(50)
        self.itemMasterChkBox.setCheckState(QtCore.Qt.Checked)
        self.itemMasterMoveToOriginChkBox.setMinimumWidth(50)
        self.itemMasterGetDirectoryBtn.setIcon(QtGui.QIcon(':fileOpen.png'))

    def setItemWidgetsMoveToOrigin(self, val):
        for itemWidget in self.publishItemWidgets:
            if val == QtCore.Qt.Checked:
                itemWidget.moveToOriginChkBox.setCheckState(QtCore.Qt.Checked)
            else:
                itemWidget.moveToOriginChkBox.setCheckState(QtCore.Qt.Unchecked)

    def setItemWidgetsEnable(self, val):
        for itemWidget in self.publishItemWidgets:
            if val == QtCore.Qt.Checked:
                itemWidget.enableChkBox.setCheckState(QtCore.Qt.Checked)
            else:
                itemWidget.enableChkBox.setCheckState(QtCore.Qt.Unchecked)

    def publishAnimation(self):
        pubItems = []
        for pubItemWidget in self.publishItemWidgets:
            pubItems.append(pubItemWidget.publishItem)
        self.aniPubObj.setItems(pubItems)
        self.aniPubObj.publish()

    def setDirectoryPath(self, widget):
        curDir = widget.text()
        dirPath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Export Directory', curDir)
        if not dirPath:
            return

        widget.setText(dirPath)

    def setItemWidgetsExportDir(self, text):
        for itemWidget in self.publishItemWidgets:
            if itemWidget.publishItem.enable:
                itemWidget.exportDirectoryLe.setText(text)

    def closeEvent(self, event):
        super(AniPublisherUI, self).closeEvent(event)

        for item in self.children():
            try:
                item.close()
            except:
                pass

    @staticmethod
    def addSeparator(layout):
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(separator)


class PublishItemWidget(QtWidgets.QWidget):
    def __init__(self, publishItem):
        super(PublishItemWidget, self).__init__()

        self.publishItem = publishItem
        self.clipWidgets = []

        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.initializeWidgets()

    def createWidgets(self):
        self.enableChkBox = QtWidgets.QCheckBox()

        self.publishOptionWidget = QtWidgets.QWidget()

        self.imageLabel = QtWidgets.QLabel()
        self.imageLabelText = QtWidgets.QLabel()

        self.moveToOriginLabel = QtWidgets.QLabel('Move to Origin: ')
        self.moveToOriginChkBox = QtWidgets.QCheckBox()

        self.exportSkelLabel = QtWidgets.QLabel('Export Skeleton: ')
        self.exportSkelChkBox = QtWidgets.QCheckBox()

        self.exportModelLabel = QtWidgets.QLabel('Export Model: ')
        self.exportModelChkBox = QtWidgets.QCheckBox()

        self.exportNodesLabel = QtWidgets.QLabel('Export Nodes:')
        self.exportSkeletonLe = QtWidgets.QLineEdit(placeholderText='Skeleton Root Node')
        self.exportModelLe = QtWidgets.QLineEdit(placeholderText='Model Root Node')

        self.exportDirectoryLabel = QtWidgets.QLabel('Export Directory:')
        self.exportDirectoryLe = QtWidgets.QLineEdit()
        self.getDirectoryBtn = QtWidgets.QPushButton()

    def createLayouts(self):
        mainLayout = QtWidgets.QHBoxLayout(self)

        mainLayout.addWidget(self.enableChkBox)
        PublishItemWidget.addSeparator(mainLayout)

        imageLayout = QtWidgets.QVBoxLayout()
        imageLayout.addWidget(self.imageLabel, 1, QtCore.Qt.AlignCenter)
        imageLayout.addWidget(self.imageLabelText, 1, QtCore.Qt.AlignCenter)
        mainLayout.addLayout(imageLayout)
        PublishItemWidget.addSeparator(mainLayout)

        publishOptionLayout = QtWidgets.QVBoxLayout()

        checkLayout = QtWidgets.QHBoxLayout()
        checkLayout.addWidget(self.moveToOriginLabel)
        checkLayout.addWidget(self.moveToOriginChkBox)
        checkLayout.addWidget(self.exportSkelLabel)
        checkLayout.addWidget(self.exportSkelChkBox)
        checkLayout.addWidget(self.exportModelLabel)
        checkLayout.addWidget(self.exportModelChkBox)
        publishOptionLayout.addLayout(checkLayout)

        exportNodesLayout = QtWidgets.QHBoxLayout()
        exportNodesLayout.addWidget(self.exportNodesLabel)
        exportNodesLayout.addWidget(self.exportSkeletonLe)
        exportNodesLayout.addWidget(self.exportModelLe)
        publishOptionLayout.addLayout(exportNodesLayout)

        exportDirLayout = QtWidgets.QHBoxLayout()
        exportDirLayout.addWidget(self.exportDirectoryLabel)
        exportDirLayout.addWidget(self.exportDirectoryLe)
        exportDirLayout.addWidget(self.getDirectoryBtn)
        publishOptionLayout.addLayout(exportDirLayout)

        self.clipLayout = QtWidgets.QVBoxLayout()
        ClipWidget(self)
        publishOptionLayout.addLayout(self.clipLayout)
        self.publishOptionWidget.setLayout(publishOptionLayout)

        mainLayout.addWidget(self.publishOptionWidget)

    def createConnections(self):
        self.enableChkBox.stateChanged.connect(self.setPublishItemEnable)
        self.moveToOriginChkBox.stateChanged.connect(self.setPublishItemMoveToOrigin)
        self.exportSkelChkBox.stateChanged.connect(self.setPublishItemExportSkeleton)
        self.exportModelChkBox.stateChanged.connect(self.setPublishItemExportModel)
        self.exportSkeletonLe.textChanged.connect(self.setPublishItemExportSkeletonRoot)
        self.exportModelLe.textChanged.connect(self.setPublishItemExportModelRoot)
        self.getDirectoryBtn.clicked.connect(lambda: self.setDirectoryPath(self.exportDirectoryLe))
        self.exportDirectoryLe.textChanged.connect(self.setPublishItemExportDirectory)

    def initializeWidgets(self):
        self.enableChkBox.setCheckState(QtCore.Qt.Checked)
        self.exportSkelChkBox.setCheckState(QtCore.Qt.Checked)
        self.exportModelChkBox.setToolTip('Enable when needs to export blendshape')
        self.exportModelLe.setEnabled(False)

        pixmap = QtGui.QPixmap(self.publishItem.image)
        self.imageLabel.setPixmap(pixmap.scaled(100, 100, QtCore.Qt.KeepAspectRatio))
        self.imageLabelText.setText(self.publishItem.namespace)

        self.getDirectoryBtn.setIcon(QtGui.QIcon(':fileOpen.png'))
        self.exportDirectoryLe.setText(self.publishItem.exportDirectory)

    def setPublishItemEnable(self, state):
        self.publishItem.enable = bool(state)
        if state:
            self.publishOptionWidget.setEnabled(True)
        else:
            self.publishOptionWidget.setEnabled(False)

    def setPublishItemMoveToOrigin(self, val):
        self.publishItem.moveToOrigin = val

    def setPublishItemExportSkeleton(self, val):
        self.publishItem.exportSkeleton = val
        self.exportSkeletonLe.setEnabled(val)
        if not val:
            self.exportSkeletonLe.setText('')

    def setPublishItemExportModel(self, val):
        self.publishItem.exportModel = val
        self.exportModelLe.setEnabled(val)
        if not val:
            self.exportModelLe.setText('')

    def setPublishItemExportSkeletonRoot(self, text):
        self.publishItem.skeletonRoot = text

    def setPublishItemExportModelRoot(self, text):
        self.publishItem.modelRoot = text

    def setDirectoryPath(self, widget):
        curDir = widget.text()
        dirPath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Export Directory', curDir)
        if not dirPath:
            return

        widget.setText(dirPath)
        self.publishItem.exportDirectory = dirPath

    def setPublishItemExportDirectory(self, exportDir):
        if not os.path.exists(exportDir):
            self.exportDirectoryLe.setText(self.publishItem.exportDirectory)
            return

        self.publishItem.exportDirectory = exportDir

    def setPublishItemFilename(self, filename):
        self.publishItem.filename = filename

    @staticmethod
    def addSeparator(layout):
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.VLine)
        separator.setFixedWidth(1)
        separator.setFixedHeight(200)

        separator.setStyleSheet('background-color: rgb(100, 100, 100);')

        layout.addWidget(separator)


class ClipWidget(QtWidgets.QWidget):
    def __init__(self, pubWidget, parent=None):
        super(ClipWidget, self).__init__(parent)

        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.setDefaults()

        self.pubWidget = pubWidget

        self.clip = aniPubModels.Clip()
        self.pubWidget.publishItem.clips.append(self.clip)

        self.pubWidget.clipLayout.addWidget(self)

    def createWidgets(self):
        self.delBtn = QtWidgets.QPushButton()
        self.clipNameLe = QtWidgets.QLineEdit(placeholderText='Clip Name')
        self.startFrameLe = QtWidgets.QLineEdit(placeholderText='Start')
        self.endFrameLe = QtWidgets.QLineEdit(placeholderText='End')
        self.addBtn = QtWidgets.QPushButton()

    def createLayouts(self):
        mainLayout = QtWidgets.QHBoxLayout(self)
        mainLayout.addWidget(self.delBtn)
        mainLayout.addWidget(self.clipNameLe)
        mainLayout.addWidget(self.startFrameLe)
        mainLayout.addWidget(self.endFrameLe)
        mainLayout.addWidget(self.addBtn)

    def createConnections(self):
        self.clipNameLe.textChanged.connect(self.setClipName)
        self.startFrameLe.textChanged.connect(self.setStartFrame)
        self.endFrameLe.textChanged.connect(self.setEndFrame)
        self.delBtn.clicked.connect(self.delWidget)
        self.addBtn.clicked.connect(self.addWidget)

    def setDefaults(self):
        self.delBtn.setIcon(QtGui.QIcon(':trash.png'))
        self.delBtn.setVisible(False)
        self.clipNameLe.setMinimumWidth(300)
        self.clipNameLe.setEnabled(False)
        self.startFrameLe.setMaximumWidth(75)
        self.startFrameLe.setEnabled(False)
        self.endFrameLe.setMaximumWidth(75)
        self.endFrameLe.setEnabled(False)
        self.addBtn.setIcon(QtGui.QIcon(':addCreateGeneric.png'))

    def setClipName(self, val):
        self.clip.name = val

    def setStartFrame(self, val):
        self.clip.startFrame = int(val)

    def setEndFrame(self, val):
        self.clip.endFrame = int(val)

    def delWidget(self):
        self.pubWidget.publishItem.clips.remove(self.clip)
        self.deleteLater()
        for clip in self.pubWidget.publishItem.clips:
            logger.debug('{0}, {1}, {2}, {3}'.format(clip.enable, clip.name, clip.startFrame, clip.endFrame))

    def addWidget(self):
        self.clip.enable = True
        self.enableWidget()
        ClipWidget(self.pubWidget)
        for clip in self.pubWidget.publishItem.clips:
            logger.debug('{0}, {1}, {2}, {3}'.format(clip.enable, clip.name, clip.startFrame, clip.endFrame))

    def enableWidget(self):
        self.delBtn.setVisible(True)
        self.clipNameLe.setEnabled(True)
        self.startFrameLe.setEnabled(True)
        self.endFrameLe.setEnabled(True)
        self.addBtn.setVisible(False)
