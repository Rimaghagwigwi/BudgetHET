import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from src.controller import Controller
from src.model import ApplicationData


def _get_startup_project_path(argv: list[str]) -> str | None:
    """Retourne le premier fichier projet existant passé en argument, sinon None."""
    for arg in argv[1:]:
        candidate = os.path.abspath(arg.strip('"'))
        if os.path.isfile(candidate) and candidate.lower().endswith((".json", ".het")):
            return candidate
    return None


def _runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _find_logo_path(base_dir: Path) -> str | None:
    for relative in ("src/img/logo.png", "src/img/logo.jpg", "src/img/logo.jpeg"):
        candidate = (base_dir / relative).resolve()
        if candidate.is_file():
            return str(candidate)
    return None


def _create_startup_splash(base_dir: Path) -> QWidget:
    splash = QWidget()
    splash.setWindowFlags(
        Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.CustomizeWindowHint
        | Qt.WindowType.WindowStaysOnTopHint
    )
    splash.setFixedSize(400, 400)
    splash.setStyleSheet("background-color: white;")

    layout = QVBoxLayout(splash)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    logo_label = QLabel()
    logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    logo_path = _find_logo_path(base_dir)
    if logo_path:
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo_label.setPixmap(
                pixmap.scaled(
                    400,
                    400,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
    layout.addWidget(logo_label)

    return splash

if __name__ == "__main__":
    startup_project_path = _get_startup_project_path(sys.argv)
    app = QApplication(sys.argv)

    base_dir = _runtime_base_dir()
    splash = _create_startup_splash(base_dir)
    splash.show()
    app.processEvents()

    # Chargement des données
    application_data = ApplicationData()
    application_data.sort_raw_data()

    # Lancement de l'application
    app.setStyle(application_data.ui_theme) # Look plus moderne par défaut sur Windows

    controller = Controller(application_data, startup_project_path=startup_project_path)
    splash.close()
    
    sys.exit(app.exec())