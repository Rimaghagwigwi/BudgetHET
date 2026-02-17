from PyQt6.QtWidgets import QSpinBox, QDoubleSpinBox
from PyQt6.QtGui import QValidator

class NoWheelSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(self.focusPolicy()) # Keep default focus policy

    def wheelEvent(self, event):
        # Ignore wheel events to prevent accidental changes
        event.ignore()

class NoWheelDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(self.focusPolicy())

    def wheelEvent(self, event):
        event.ignore()

class CoeffSpinBox(NoWheelDoubleSpinBox):
    """A SpinBox that displays an empty string when the value is 1.0."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0.0, 100.0)
        self.setSingleStep(0.1)
        self.setDecimals(2)
        self.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)

    def textFromValue(self, value):
        if abs(value - 1.0) < 0.0001: # Epsilon check for float
            return ""
        return super().textFromValue(value)

    def validate(self, text, pos):
        # Allow empty input to be valid (interpreted as 1.0 usually, or we handle it)
        if text == "":
            return QValidator.State.Acceptable, text, pos
        return super().validate(text, pos)

    def valueFromText(self, text):
        if text == "":
            return 1.0
        return super().valueFromText(text)
