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

        self.setStyleSheet("""
            /* Base */
            QWidget {
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QMainWindow {
                background-color: white;
            }

            /* Default text color */
            QLabel, QTableWidget, QTreeWidget {
                color: #2c3e50;
            }

            /* Form labels in general tab */
            #tabGeneral QLabel {
                font-weight: bold;
            }

            /* Important text */
            QLabel#important {
                color: #0063AF;
                font-weight: bold;
                font-size: 16px;
            }

            /* Very important text */
            QLabel#veryImportant {
                color: #E94F36;
                font-weight: bold;
                font-size: 18px;
            }

            /* Inputs */
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }

            /* Buttons */
            QPushButton {
                background-color: #0063AF;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }

            /* Table headers */
            QHeaderView::section {
                background-color: #0063AF;
                color: white;
            }

            /* Tables */
            QTableWidget {
                background-color: white;
                border: 1px solid #dcdcdc;
            }

            /* Tree */
            QTreeWidget {
                background-color: white;
            }
            QTreeWidget::item {
                padding: 2px;
                min-height: 20px;
            }

            /* Summary totals frame */
            QFrame#totalsFrame {
                background-color: #f9f9f9;
                border-top: 2px solid #f0f0f0;
            }
                           
            QFrame#rowSeparator {
                background-color: #f0f0f0;
                max-height: 1px;
            }
                           
        """)

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
