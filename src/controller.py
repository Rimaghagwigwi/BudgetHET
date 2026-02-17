from typing import List, Dict, Any, Optional
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal
from src.model import Model, Project
from src.view import MainWindow
from src.utils.Task import GeneralTask, LPDCDocument, Calcul, Option
from src.tabs.TabGeneral import TabGeneral, TabGeneralController

from src.tabs.TabTasks import TabTasks
from src.tabs.GeneralTaskTabController import GeneralTaskTabController
from src.tabs.CalculsTabController import CalculsTabController
from src.tabs.OptionsTabController import OptionsTabController
from src.tabs.LPDCTabController import LPDCTabController
from src.tabs.TabSummary import TabSummary, TabSummaryController

class Controller:
    def __init__(self, application_data):
        self.app_data = application_data
        self.model = Model(app_data=application_data)

        self.window = MainWindow(application_data)

        self._create_tabs()

        self.window.show()
    
    def _create_tabs(self):
        self.tabGeneral = TabGeneral()
        self.tabGeneralController = TabGeneralController(self.model, self.tabGeneral)
        self.window.add_tab(self.tabGeneral, "Général")

        self.tabTasks = TabTasks()
        self.tabTasksController = GeneralTaskTabController(self.model, self.tabTasks)
        self.window.add_tab(self.tabTasks, "Tâches")

        self.tabCalculs = TabTasks()
        self.tabCalculsController = CalculsTabController(self.model, self.tabCalculs)
        self.window.add_tab(self.tabCalculs, "Calculs")

        self.tabOptions = TabTasks()
        self.tabOptionsController = OptionsTabController(self.model, self.tabOptions)
        self.window.add_tab(self.tabOptions, "Options")

        self.tabLPDC = TabTasks()
        self.tabLPDCController = LPDCTabController(self.model, self.tabLPDC)
        self.window.add_tab(self.tabLPDC, "LPDC")

        self.tabSummary = TabSummary()
        self.tabSummaryController = TabSummaryController(self.model, self.tabSummary)
        self.window.add_tab(self.tabSummary, "Résumé")

    def on_apply_defaults(self):
        pass