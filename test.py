from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App pro")

        label = QLabel("Contenu principal")
        self.setCentralWidget(label)

app = QApplication([])
window = MainWindow()
window.show()
app.exec()
