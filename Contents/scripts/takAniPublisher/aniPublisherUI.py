import maya.OpenMayaUI as omui

import os
from shiboken2 import wrapInstance
from PySide2 import QtWidgets, QtCore, QtGui

from . import settingsUI
from . import constants

reload(settingsUI)  # type: ignore


def getMayaMainWin():
    mayaMainWinWidget = None

    mayaMainWinPtr = omui.MQtUtil.mainWindow()
    mayaMainWinWidget = wrapInstance(long(mayaMainWinPtr), QtWidgets.QWidget)  # type: ignore

    return mayaMainWinWidget


class AniPublisherUI(QtWidgets.QDialog):
    NAME = 'TAK Ani Publisher_Personal'

    def __init__(self, aniPublisher=None, parent=getMayaMainWin()):
        super(AniPublisherUI, self).__init__(parent)

        self.aniPubObj = aniPublisher
        self.publishItemWidgets = []

        self.setWindowTitle('{0} - {1}'.format(AniPublisherUI.NAME, constants.VERSION))
        self.setWindowIcon(QtGui.QIcon(':out_timeEditorAnimSource.png'))
        self.resize(1000, 1000)

        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.setInitialState()

    def createWidgets(self):
        self.menuBar = QtWidgets.QMenuBar()
        self.editMenu = self.menuBar.addMenu('Edit')
        self.settingsAction = self.editMenu.addAction('Settings')

        self.itemMasterChkBox = QtWidgets.QCheckBox()
        self.itemMasterMoveToOriginChkBox = QtWidgets.QCheckBox()
        self.itemMasterExportDirLe = QtWidgets.QLineEdit()
        self.itemMasterGetDirectoryBtn = QtWidgets.QPushButton()
        self.itemMasterStartFrameLe = QtWidgets.QLineEdit()
        self.itemMasterEndFrameLe = QtWidgets.QLineEdit()

        for item in self.aniPubObj.publishItems:
            self.publishItemWidgets.append(PublishItemWidget(item))

        self.publishBtn = QtWidgets.QPushButton('Publish Animation')

    def createLayouts(self):
        mainLayout = QtWidgets.QVBoxLayout(self)

        mainLayout.addWidget(self.menuBar)

        itemMasterLayout = QtWidgets.QHBoxLayout()
        itemMasterLayout.addWidget(self.itemMasterChkBox)
        itemMasterLayout.addWidget(self.itemMasterMoveToOriginChkBox)
        itemMasterLayout.addWidget(self.itemMasterExportDirLe)
        itemMasterLayout.addWidget(self.itemMasterGetDirectoryBtn)
        masterFrameWdg = QtWidgets.QWidget()
        masterFrameWdg.setFixedWidth(200)
        masterFrameLo = QtWidgets.QHBoxLayout(masterFrameWdg)
        masterFrameLo.addWidget(self.itemMasterStartFrameLe)
        masterFrameLo.addWidget(QtWidgets.QLabel('~'))
        masterFrameLo.addWidget(self.itemMasterEndFrameLe)
        itemMasterLayout.addWidget(masterFrameWdg)
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
        self.itemMasterStartFrameLe.textChanged.connect(self.setItemWidgetsStartFrame)
        self.itemMasterEndFrameLe.textChanged.connect(self.setItemWidgetsEndFrame)
        self.publishBtn.clicked.connect(self.publishAnimation)

    def showSettingsUI(self):
        setUI = settingsUI.SettingsUI(self)
        setUI.show()

    def setInitialState(self):
        self.itemMasterChkBox.setCheckState(QtCore.Qt.Checked)
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

    def setItemWidgetsStartFrame(self, text):
        for itemWidget in self.publishItemWidgets:
            if itemWidget.publishItem.enable:
                itemWidget.startFrameLe.setText(text)

    def setItemWidgetsEndFrame(self, text):
        for itemWidget in self.publishItemWidgets:
            if itemWidget.publishItem.enable:
                itemWidget.endFrameLe.setText(text)

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

        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.initializeWidgets()

    def createWidgets(self):
        self.enableChkBox = QtWidgets.QCheckBox()

        self.publishOptionWidget = QtWidgets.QWidget()

        self.moveToOriginLabel = QtWidgets.QLabel('Move to Origin:')
        self.moveToOriginChkBox = QtWidgets.QCheckBox()

        self.exportDirectoryLabel = QtWidgets.QLabel('Export Directory:')
        self.exportDirectoryLe = QtWidgets.QLineEdit()
        self.getDirectoryBtn = QtWidgets.QPushButton()

        self.filenameLabel = QtWidgets.QLabel('Filename:')
        self.filenameLe = QtWidgets.QLineEdit()

        self.frameRangeLabel = QtWidgets.QLabel('Frame Range:')
        self.startFrameLe = QtWidgets.QLineEdit()
        self.endFrameLe = QtWidgets.QLineEdit()

        self.exportNodesLabel = QtWidgets.QLabel('Export Nodes:')
        self.exportSkeletonLe = QtWidgets.QLineEdit(placeholderText='Skeleton Root Node')
        self.exportModelLe = QtWidgets.QLineEdit(placeholderText='Model Root Node')

    def createLayouts(self):
        mainLayout = QtWidgets.QHBoxLayout(self)

        mainLayout.addWidget(self.enableChkBox)

        publishOptionLayout = QtWidgets.QGridLayout()
        publishOptionLayout.addWidget(self.moveToOriginLabel, 0, 0, QtCore.Qt.AlignRight)
        publishOptionLayout.addWidget(self.moveToOriginChkBox, 0, 1)

        publishOptionLayout.addWidget(self.exportDirectoryLabel, 1, 0, QtCore.Qt.AlignRight)
        publishOptionLayout.addWidget(self.exportDirectoryLe, 1, 1)
        publishOptionLayout.addWidget(self.getDirectoryBtn, 1, 2)

        publishOptionLayout.addWidget(self.filenameLabel, 2, 0, QtCore.Qt.AlignRight)
        publishOptionLayout.addWidget(self.filenameLe, 2, 1)

        publishOptionLayout.addWidget(self.frameRangeLabel, 3, 0, QtCore.Qt.AlignRight)
        frameWdg = QtWidgets.QWidget()
        frameWdg.setFixedWidth(200)
        frameLo = QtWidgets.QHBoxLayout(frameWdg)
        frameLo.addWidget(self.startFrameLe)
        waveSign = QtWidgets.QLabel('~')
        frameLo.addWidget(waveSign)
        frameLo.addWidget(self.endFrameLe)
        publishOptionLayout.addWidget(frameWdg, 3, 1)

        publishOptionLayout.addWidget(self.exportNodesLabel, 4, 0, QtCore.Qt.AlignRight)
        exportNodesWidget = QtWidgets.QWidget()
        exportNodesLayout = QtWidgets.QHBoxLayout(exportNodesWidget)
        exportNodesLayout.addWidget(self.exportSkeletonLe)
        exportNodesLayout.addWidget(self.exportModelLe)
        publishOptionLayout.addWidget(exportNodesWidget, 4, 1)

        self.publishOptionWidget.setLayout(publishOptionLayout)
        mainLayout.addWidget(self.publishOptionWidget)

    def createConnections(self):
        self.enableChkBox.stateChanged.connect(self.setPublishItemEnable)
        self.moveToOriginChkBox.stateChanged.connect(self.setPublishItemMoveToOrigin)
        self.getDirectoryBtn.clicked.connect(lambda: self.setDirectoryPath(self.exportDirectoryLe))
        self.exportDirectoryLe.textChanged.connect(self.setPublishItemExportDirectory)
        self.filenameLe.textChanged.connect(self.setPublishItemFilename)
        self.startFrameLe.textChanged.connect(self.setStartFrame)
        self.endFrameLe.textChanged.connect(self.setEndFrame)
        self.exportSkeletonLe.textChanged.connect(self.setPublishItemExportSkeleton)
        self.exportModelLe.textChanged.connect(self.setPublishItemExportModel)

    def initializeWidgets(self):
        self.enableChkBox.setCheckState(QtCore.Qt.Checked)

        self.getDirectoryBtn.setIcon(QtGui.QIcon(':fileOpen.png'))
        self.exportDirectoryLe.setText(self.publishItem.exportDirectory)
        self.filenameLe.setText(self.publishItem.filename)

        self.startFrameLe.setText(str(self.publishItem.startFrame))
        self.endFrameLe.setText(str(self.publishItem.endFrame))

    def setPublishItemEnable(self, state):
        self.publishItem.enable = bool(state)
        if state:
            self.publishOptionWidget.setEnabled(True)
        else:
            self.publishOptionWidget.setEnabled(False)

    def setPublishItemMoveToOrigin(self, val):
        self.publishItem.moveToOrigin = val

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

    def setStartFrame(self, frame):
        self.publishItem.startFrame = frame

    def setEndFrame(self, frame):
        self.publishItem.endFrame = frame

    def setPublishItemExportSkeleton(self, text):
        self.publishItem.skeletonRoot = text

    def setPublishItemExportModel(self, text):
        self.publishItem.modelRoot = text

    @staticmethod
    def addSeparator(layout):
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.VLine)
        separator.setFixedWidth(1)
        separator.setFixedHeight(75)

        separator.setStyleSheet('background-color: rgb(100, 100, 100);')

        layout.addWidget(separator)
