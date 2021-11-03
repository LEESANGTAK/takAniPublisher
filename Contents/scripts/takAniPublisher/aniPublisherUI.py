"""
Test Code:
import pipeline.aniPublisherUI as apui
reload(apui)

try:
    apuiObj.close()
    apuiObj.deleteLater()
except:
    pass

apuiObj = apui.AniPublisherUI()
apuiObj.show()
"""
import maya.OpenMayaUI as omui
import maya.cmds as cmds

import os
from shiboken2 import wrapInstance
from PySide2 import QtWidgets, QtCore, QtGui

from . import settingsUI
reload(settingsUI)


def getMayaMainWin():
        mayaMainWinWidget = None

        mayaMainWinPtr = omui.MQtUtil.mainWindow()
        mayaMainWinWidget = wrapInstance(long(mayaMainWinPtr), QtWidgets.QWidget)

        return mayaMainWinWidget


class AniPublisherUI(QtWidgets.QDialog):
    def __init__(self, aniPublisher=None, parent=getMayaMainWin()):
        super(AniPublisherUI, self).__init__(parent)

        self.aniPubObj = aniPublisher
        self.publishItemWidgets = []

        self.setWindowTitle('{0} - {1}'.format(self.aniPubObj.NAME, self.aniPubObj.VERSION))
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
        self.itemMasterBakeSpaceCb = QtWidgets.QComboBox()
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
        itemMasterLayout.addWidget(self.itemMasterBakeSpaceCb)
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
        self.itemMasterBakeSpaceCb.currentTextChanged.connect(self.setItemWidgetsBakeSapce)
        self.itemMasterGetDirectoryBtn.clicked.connect(lambda : self.setDirectoryPath(self.itemMasterExportDirLe))
        self.itemMasterExportDirLe.textChanged.connect(self.setItemWidgetsExportDir)
        self.itemMasterStartFrameLe.textChanged.connect(self.setItemWidgetsStartFrame)
        self.itemMasterEndFrameLe.textChanged.connect(self.setItemWidgetsEndFrame)
        self.publishBtn.clicked.connect(self.publishAnimation)

    def showSettingsUI(self):
        setUI = settingsUI.SettingsUI(self)
        setUI.show()

    def setInitialState(self):
        self.itemMasterChkBox.setCheckState(QtCore.Qt.Checked)
        self.itemMasterBakeSpaceCb.addItems(['world', 'local'])
        self.itemMasterGetDirectoryBtn.setIcon(QtGui.QIcon(':fileOpen.png'))

    def setItemWidgetsBakeSapce(self, space):
        for itemWidget in self.publishItemWidgets:
            if itemWidget.publishItem.enable:
                itemWidget.bakeSpaceCb.setCurrentText(space)

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
        jobDone = self.aniPubObj.publish()

        if jobDone:
            self.close()

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

        self.imageLabel = QtWidgets.QLabel()
        self.imageLabelText = QtWidgets.QLabel()

        self.bakeSpaceLabel = QtWidgets.QLabel('Bake Space:')
        self.bakeSpaceCb = QtWidgets.QComboBox()

        self.exportDirectoryLabel = QtWidgets.QLabel('Export Directory:')
        self.exportDirectoryLe = QtWidgets.QLineEdit()
        self.getDirectoryBtn = QtWidgets.QPushButton()

        self.filenameLabel = QtWidgets.QLabel('Filename:')
        self.filenameLe = QtWidgets.QLineEdit()

        self.frameRangeLabel = QtWidgets.QLabel('Frame Range:')
        self.startFrameLe = QtWidgets.QLineEdit()
        self.endFrameLe = QtWidgets.QLineEdit()

        self.exportOptionLabel = QtWidgets.QLabel('Export Options:')
        self.exportSkeletonChkBox = QtWidgets.QCheckBox('Skeleton')
        self.exportBlendshapeChkBox = QtWidgets.QCheckBox('Blendshape')

    def createLayouts(self):
        mainLayout = QtWidgets.QHBoxLayout(self)

        mainLayout.addWidget(self.enableChkBox)
        PublishItemWidget.addSeparator(mainLayout)

        imageLayout = QtWidgets.QVBoxLayout()
        imageLayout.addWidget(self.imageLabel, 1, QtCore.Qt.AlignCenter)
        imageLayout.addWidget(self.imageLabelText, 1, QtCore.Qt.AlignCenter)
        mainLayout.addLayout(imageLayout)
        PublishItemWidget.addSeparator(mainLayout)

        publishOptionLayout = QtWidgets.QGridLayout()
        publishOptionLayout.addWidget(self.bakeSpaceLabel, 0, 0, QtCore.Qt.AlignRight)
        publishOptionLayout.addWidget(self.bakeSpaceCb, 0, 1)

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

        publishOptionLayout.addWidget(self.exportOptionLabel, 4, 0, QtCore.Qt.AlignRight)
        exportOptionWidget = QtWidgets.QWidget()
        exportOptionWidget.setFixedWidth(250)
        exportOptionLayout = QtWidgets.QHBoxLayout(exportOptionWidget)
        exportOptionLayout.addWidget(self.exportSkeletonChkBox)
        exportOptionLayout.addWidget(self.exportBlendshapeChkBox)
        publishOptionLayout.addWidget(exportOptionWidget, 4, 1)

        mainLayout.addLayout(publishOptionLayout)

    def createConnections(self):
        self.enableChkBox.stateChanged.connect(self.setPublishItemEnable)
        self.bakeSpaceCb.currentTextChanged.connect(self.setPublishItemBakeSapce)
        self.getDirectoryBtn.clicked.connect(lambda : self.setDirectoryPath(self.exportDirectoryLe))
        self.exportDirectoryLe.textChanged.connect(self.setPublishItemExportDirectory)
        self.filenameLe.textChanged.connect(self.setPublishItemFilename)
        self.startFrameLe.textChanged.connect(self.setStartFrame)
        self.endFrameLe.textChanged.connect(self.setEndFrame)
        self.exportSkeletonChkBox.stateChanged.connect(self.setPublishItemExportSkeleton)
        self.exportBlendshapeChkBox.stateChanged.connect(self.setPublishItemExportBlendshape)

    def initializeWidgets(self):
        self.enableChkBox.setCheckState(QtCore.Qt.Checked)

        pixmap = QtGui.QPixmap(self.publishItem.image)
        self.imageLabel.setPixmap(pixmap.scaled(100, 100, QtCore.Qt.KeepAspectRatio))

        self.imageLabelText.setText(self.publishItem.namespace)
        self.bakeSpaceCb.addItems(self.publishItem.BAKE_SPACES)
        self.getDirectoryBtn.setIcon(QtGui.QIcon(':fileOpen.png'))
        self.exportDirectoryLe.setText(self.publishItem.exportDirectory)
        self.filenameLe.setText(self.publishItem.filename)

        self.startFrameLe.setText(str(self.publishItem.startFrame))
        self.endFrameLe.setText(str(self.publishItem.endFrame))

        self.exportSkeletonChkBox.setChecked(True)
        self.exportBlendshapeChkBox.setChecked(False)

    def setPublishItemEnable(self, state):
        self.publishItem.enable = bool(state)

    def setPublishItemBakeSapce(self, text):
        self.publishItem.bakeSpace = text

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

    def setPublishItemExportSkeleton(self, state):
        self.publishItem.exportSkeleton = bool(state)

    def setPublishItemExportBlendshape(self, state):
        self.publishItem.exportBlendshape = bool(state)

    @staticmethod
    def addSeparator(layout):
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.VLine)
        separator.setFixedWidth(1)
        separator.setFixedHeight(75)

        separator.setStyleSheet('background-color: rgb(100, 100, 100);')

        layout.addWidget(separator)