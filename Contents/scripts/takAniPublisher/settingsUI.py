from PySide2 import QtWidgets, QtCore

import os
import json

from . import constants
reload(constants)  # type: ignore


class SettingsUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SettingsUI, self).__init__(parent)

        self.defaultSettingFile = constants.DEFAULT_SETTING_FILE
        self.userSettingFile = constants.USER_SETTING_FILE
        self.settings = None

        self.setWindowTitle('Settings')
        self.setWindowFlags(QtCore.Qt.Tool)

        self.loadSettings()

        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.setDefaults()

    def createWidgets(self):
        self.useCustomExportDirChkBox = QtWidgets.QCheckBox('Use custom export directory as default.')
        self.customExportDirLe = QtWidgets.QLineEdit()

        self.saveBtn = QtWidgets.QPushButton('Save')
        self.cancelBtn = QtWidgets.QPushButton('Cancel')

    def createLayouts(self):
        mainLayout = QtWidgets.QVBoxLayout(self)

        formLayout = QtWidgets.QFormLayout()
        formLayout.addRow('Use Custom Export Directory: ', self.useCustomExportDirChkBox)
        formLayout.addRow('Custom Export Directory: ', self.customExportDirLe)
        mainLayout.addLayout(formLayout)

        btnLayout = QtWidgets.QHBoxLayout()
        btnLayout.addWidget(self.saveBtn)
        btnLayout.addWidget(self.cancelBtn)
        mainLayout.addLayout(btnLayout)

    def createConnections(self):
        self.useCustomExportDirChkBox.stateChanged.connect(self.useCustomExportDirChkBoxSlot)
        self.customExportDirLe.textChanged.connect(lambda text: self.settings.update({'customExportDirectory': text}))
        self.saveBtn.clicked.connect(self.saveSettings)
        self.cancelBtn.clicked.connect(self.close)

    def setDefaults(self):
        self.useCustomExportDirChkBox.setChecked(self.settings['useCustomExportDirectory'])
        self.customExportDirLe.setText(self.settings['customExportDirectory'])

        self.useCustomExportDirChkBoxSlot(self.settings['useCustomExportDirectory'])

    def useCustomExportDirChkBoxSlot(self, checked):
        self.settings.update({'useCustomExportDirectory': bool(checked)})

        if not checked:
            self.customExportDirLe.clear()
            self.customExportDirLe.setStyleSheet('background-color: grey;')
            self.customExportDirLe.setDisabled(True)
        else:
            self.customExportDirLe.setStyleSheet('')
            self.customExportDirLe.setDisabled(False)

    def loadSettings(self):
        settingsFile = self.userSettingFile if os.path.exists(self.userSettingFile) else self.defaultSettingFile
        with open(settingsFile, 'r') as f:
            self.settings = json.load(f)

    def saveSettings(self):
        if not os.path.exists(constants.APP_PREFERENCE_DIR):
            os.mkdir(constants.APP_PREFERENCE_DIR)

        with open(self.userSettingFile, 'w') as f:
            json.dump(self.settings, f, indent=4)

        self.close()
