"""Compact dark and light themes with a green accent."""

APP_STYLESHEET = """
QWidget {
    color: #eef2ef;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QWidget#translationPanel, QWidget#toolbarSurface {
    background-color: #202622;
    border: 1px solid #53665a;
    border-radius: 10px;
}
QWidget#titleBar { background-color: #2c352f; border-radius: 8px; }
QScrollArea#panelScrollArea, QWidget#panelBody { background: transparent; border: none; }
QLabel#appTitle { font-size: 11pt; font-weight: 600; color: #f4f8f5; }
QLabel#sectionTitle { color: #9eb7a5; font-weight: 600; }
QLabel#statusActive { color: #78c58e; font-weight: 600; }
QLabel#statusPaused { color: #e3b45e; font-weight: 600; }
QTextEdit {
    background-color: #171c19;
    border: 1px solid #3e4a42;
    border-radius: 6px;
    padding: 7px;
    selection-background-color: #537b5e;
}
QComboBox, QPushButton {
    background-color: #303a33;
    border: 1px solid #53665a;
    border-radius: 6px;
    min-height: 27px;
}
QPushButton { padding: 2px 9px; }
QComboBox { padding: 2px 28px 2px 9px; }
QComboBox::drop-down { width: 24px; border-left: 1px solid #53665a; }
QComboBox:hover, QPushButton:hover { border-color: #78ad87; background-color: #37443b; }
QPushButton:pressed { background-color: #26322a; }
QPushButton:checked { background-color: #456a50; border-color: #85c797; }
QPushButton#accentButton { background-color: #4d7658; border-color: #72a980; font-weight: 600; }
QPushButton#closeButton { min-width: 28px; max-width: 28px; padding: 1px; }
QPushButton#closeButton:hover { background-color: #7b3f45; border-color: #aa5960; }
QComboBox QAbstractItemView { background-color: #29312c; selection-background-color: #4d7658; }
QToolTip { background-color: #171c19; color: white; border: 1px solid #53665a; }
"""

LIGHT_STYLESHEET = """
QWidget { color: #18221b; font-family: "Segoe UI"; font-size: 10pt; }
QWidget#translationPanel, QWidget#toolbarSurface {
    background-color: #f2f6f3; border: 1px solid #829789; border-radius: 10px;
}
QWidget#titleBar { background-color: #dfe9e2; border-radius: 8px; }
QScrollArea#panelScrollArea, QWidget#panelBody { background: transparent; border: none; }
QLabel#appTitle { font-size: 11pt; font-weight: 600; color: #152219; }
QLabel#sectionTitle { color: #42624b; font-weight: 600; }
QLabel#statusActive { color: #287b3f; font-weight: 600; }
QLabel#statusPaused { color: #9a651c; font-weight: 600; }
QTextEdit { background-color: white; border: 1px solid #a8b7ad; border-radius: 6px; padding: 7px; }
QComboBox, QPushButton, QLineEdit, QSpinBox {
    background-color: #e8efe9; border: 1px solid #96a99b; border-radius: 6px;
    min-height: 27px;
}
QPushButton, QLineEdit, QSpinBox { padding: 2px 9px; }
QComboBox { padding: 2px 28px 2px 9px; }
QComboBox::drop-down { width: 24px; border-left: 1px solid #96a99b; }
QComboBox:hover, QPushButton:hover { border-color: #4e8d5e; background-color: #dce9df; }
QPushButton:checked { background-color: #b8d4bf; border-color: #4e8d5e; }
QPushButton#accentButton { background-color: #5b9368; color: white; font-weight: 600; }
QPushButton#closeButton { min-width: 28px; max-width: 28px; padding: 1px; }
QPushButton#closeButton:hover { background-color: #a94e58; color: white; }
QToolTip { background-color: white; color: #18221b; border: 1px solid #829789; }
"""


def stylesheet(theme: str) -> str:
    return LIGHT_STYLESHEET if theme == "light" else APP_STYLESHEET
