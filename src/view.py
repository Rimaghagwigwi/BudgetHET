from PyQt6.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QTabWidget

from src.utils.ApplicationData import ApplicationData

class MainWindow(QMainWindow): 
    def __init__(self, app_data: ApplicationData=None):
        super().__init__()

        title = "Chiffrage HET"
        width = 1080
        height = 720

        if app_data:
            title = app_data.window_title
            width = app_data.window_width
            height = app_data.window_height

        self.setWindowTitle(title)
        self.resize(width, height)

        if app_data and app_data.stylesheet:
            self.setStyleSheet(app_data.stylesheet)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Sidebar Layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Sidebar with Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        main_layout.addWidget(self.tabs)

    def add_tab(self, widget: QWidget, title: str):
        self.tabs.addTab(widget, title)
