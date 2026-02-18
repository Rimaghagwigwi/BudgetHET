from src.model import Model
from src.view import MainWindow
from src.tabs.TabGeneral import TabGeneral, TabGeneralController
from src.tabs.TabTasks import TabTasks
from src.tabs.GeneralTaskTabController import GeneralTaskTabController
from src.tabs.CalculsTabController import CalculsTabController
from src.tabs.OptionsTabController import OptionsTabController
from src.tabs.LPDCTabController import LPDCTabController
from src.tabs.LaboTabController import LaboTabController
from src.tabs.TabSummary import TabSummary, TabSummaryController


class Controller:
    def __init__(self, application_data):
        self.model = Model(app_data=application_data)
        self.window = MainWindow(application_data)
        self.controllers = self._create_tabs()
        self.window.show()

    def _create_tabs(self):
        """Crée tous les onglets et leurs contrôleurs."""
        tab_configs = [
            (TabGeneral(),  TabGeneralController,     "Général"),
            (TabTasks(),    GeneralTaskTabController,  "Tâches"),
            (TabTasks(),    CalculsTabController,      "Calculs"),
            (TabTasks(),    OptionsTabController,      "Options"),
            (TabTasks(),    LPDCTabController,         "LPDC"),
            (TabTasks(),    LaboTabController,         "Labo"),
            (TabSummary(),  TabSummaryController,      "Résumé"),
        ]

        controllers = []
        for view, ctrl_class, title in tab_configs:
            controllers.append(ctrl_class(self.model, view))
            self.window.add_tab(view, title)
        return controllers