# -*- coding: utf-8 -*-

"""
***************************************************************************
    provider.py
    ---------------------
    Date                 : August 2012
    Copyright            : (C) 2012 by Victor Olaya
    Email                : volayaf at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import os
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (Qgis,
                       QgsProcessingProvider,
                       QgsMessageLog)

from processing.core.ProcessingConfig import ProcessingConfig, Setting
from processing.gui.ProviderActions import (ProviderActions,
                                            ProviderContextMenuActions)
from processing.tools.system import isWindows

from r.processing.actions.create_new_script import CreateNewScriptAction
from r.processing.actions.edit_script import EditScriptAction
from r.processing.actions.delete_script import DeleteScriptAction
from r.processing.exceptions import InvalidScriptException
from r.processing.utils import RUtils
from r.processing.algorithm import RAlgorithm
from r.gui.gui_utils import GuiUtils


class RAlgorithmProvider(QgsProcessingProvider):
    """
    Processing provider for executing R scripts
    """

    def __init__(self):
        super().__init__()
        self.algs = []
        self.actions = []
        create_script_action = CreateNewScriptAction()
        self.actions.append(create_script_action)
        self.contextMenuActions = [EditScriptAction(),
                                   DeleteScriptAction()]

    def load(self):
        ProcessingConfig.settingIcons[self.name()] = self.icon()
        ProcessingConfig.addSetting(Setting(self.name(), 'ACTIVATE_R',
                                            self.tr('Activate'), False))
        ProcessingConfig.addSetting(Setting(
            self.name(), RUtils.RSCRIPTS_FOLDER,
            self.tr('R scripts folder'), RUtils.default_scripts_folder(),
            valuetype=Setting.MULTIPLE_FOLDERS))

        ProcessingConfig.addSetting(Setting(self.name(), 'ACTIVATE_R',
                                            self.tr('Activate'), False))

        ProcessingConfig.addSetting(Setting(self.name(), RUtils.R_USE_USER_LIB,
                                            self.tr('Use user library folder instead of system libraries'), True))
        ProcessingConfig.addSetting(Setting(
            self.name(),
            RUtils.R_LIBS_USER, self.tr('User library folder'),
            RUtils.r_library_folder(), valuetype=Setting.FOLDER))

        ProcessingConfig.addSetting(Setting(
            self.name(),
            RUtils.R_REPO, self.tr('Package repository'),
            "http://cran.at.r-project.org/", valuetype=Setting.STRING))

        # if isWindows():
        #    ProcessingConfig.addSetting(Setting(#
        #        self.name(),
        #        RUtils.R_FOLDER, self.tr('R folder'), RUtils.RFolder(),
        #        valuetype=Setting.FOLDER))
        #    ProcessingConfig.addSetting(Setting(
        #        self.name(),
        #        RUtils.R_USE64, self.tr('Use 64 bit version'), False))
        ProviderActions.registerProviderActions(self, self.actions)
        ProviderContextMenuActions.registerProviderContextMenuActions(self.contextMenuActions)
        ProcessingConfig.readSettings()
        self.refreshAlgorithms()
        return True

    def unload(self):
        ProcessingConfig.removeSetting('ACTIVATE_R')
        ProcessingConfig.removeSetting(RUtils.RSCRIPTS_FOLDER)
        ProcessingConfig.removeSetting(RUtils.R_LIBS_USER)
        # if isWindows():
        #     ProcessingConfig.removeSetting(RUtils.R_FOLDER)
        #
        #     ProcessingConfig.removeSetting(RUtils.R_USE64)
        ProviderActions.deregisterProviderActions(self)
        ProviderContextMenuActions.deregisterProviderContextMenuActions(self.contextMenuActions)

    def isActive(self):
        return ProcessingConfig.getSetting('ACTIVATE_R')

    def setActive(self, active):
        ProcessingConfig.setSettingValue('ACTIVATE_R', active)

    def icon(self):
        return GuiUtils.get_icon("providerR.svg")

    def svgIconPath(self):
        return GuiUtils.get_icon_svg("providerR.svg")

    def name(self):
        return self.tr('R')

    def longName(self):
        return self.tr('R')

    def id(self):
        return 'r'

    def loadAlgorithms(self):
        algs = []
        for f in RUtils.script_folders():
            algs.extend(self.load_scripts_from_folder(f))

        for a in algs:
            self.addAlgorithm(a)

    def load_scripts_from_folder(self, folder):
        """
        Loads all scripts found under the specified subfolder
        """
        if not os.path.exists(folder):
            return []

        algs = []
        for path, _, files in os.walk(folder):
            for description_file in files:
                if description_file.lower().endswith('rsx'):
                    try:
                        fullpath = os.path.join(path, description_file)
                        alg = RAlgorithm(fullpath)
                        if alg.name().strip():
                            algs.append(alg)
                    except InvalidScriptException as e:
                        QgsMessageLog.logMessage(e.msg, self.tr('Processing'), Qgis.Critical)
                    except Exception as e:  # pylint: disable=broad-except
                        QgsMessageLog.logMessage(
                            self.tr('Could not load R script: {0}\n{1}').format(description_file, str(e)),
                            self.tr('Processing'), Qgis.Critical)
        return algs

    def tr(self, string, context=''):
        """
        Translates a string
        """
        if context == '':
            context = 'RAlgorithmProvider'
        return QCoreApplication.translate(context, string)
