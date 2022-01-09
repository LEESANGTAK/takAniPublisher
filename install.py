import os
import sys

import maya.cmds as cmds
import maya.mel as mel


MAYA_VERSION = int(cmds.about(version=True))
MODULE_NAME = os.path.dirname(__file__).rsplit('/', 1)[-1]
MODULE_VERSION = '1.0.0'
MODULE_PATH = os.path.dirname(__file__) + '/Contents'


def onMayaDroppedPythonFile(*args, **kwargs):
    modulesDir = getModulesDirectory()
    createModuleFile(modulesDir)
    addScriptPath()
    loadPlugins()
    addShelfButtons()


def getModulesDirectory():
    modulesDir = None

    documentDir = os.path.expanduser('~')
    mayaAppDir = os.path.join(documentDir, 'maya')
    modulesDir = os.path.join(mayaAppDir, 'modules')

    if not os.path.exists(modulesDir):
        os.mkdir(modulesDir)

    return modulesDir


def createModuleFile(modulesDir):
    moduleFileName = '{0}.mod'.format(MODULE_NAME)
    contents = '+ MAYAVERSION:{0} {1} {2} {3}'.format(MAYA_VERSION, MODULE_NAME, MODULE_VERSION, MODULE_PATH)

    with open(os.path.join(modulesDir, moduleFileName), 'w') as f:
        f.write(contents)


def addScriptPath():
    scriptPath = os.path.join(MODULE_PATH, 'scripts')
    sys.path.append(scriptPath)


def loadPlugins():
    pluginsPath = os.path.join(MODULE_PATH, 'plug-ins')
    if os.path.exists(pluginsPath):
        pluginFiles = os.listdir(pluginsPath)
        if pluginFiles:
            for pluginFile in pluginFiles:
                cmds.loadPlugin(os.path.join(pluginsPath, pluginFile))


def addShelfButtons():
    curShelf = getCurrentShelf()

    command = '''
import takAniPublisher.aniPublisherCtrl as apCtrl
reload(apCtrl)

apCtrlObj = apCtrl.AniPublisherCtrl()
apCtrlObj.showUI()
'''
    cmds.shelfButton(
        command=command,
        annotation=MODULE_NAME,
        sourceType='Python',
        image='out_timeEditorAnimSource.png',
        image1='out_timeEditorAnimSource.png',
        parent=curShelf
    )


def getCurrentShelf():
    curShelf = None

    shelf = mel.eval('$gShelfTopLevel = $gShelfTopLevel')
    curShelf = cmds.tabLayout(shelf, query=True, selectTab=True)

    return curShelf
