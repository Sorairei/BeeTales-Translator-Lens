"""Tema oscuro compacto con acento verde."""

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
    padding: 2px 9px;
}
QComboBox:hover, QPushButton:hover { border-color: #78ad87; background-color: #37443b; }
QPushButton:pressed { background-color: #26322a; }
QPushButton:checked { background-color: #456a50; border-color: #85c797; }
QPushButton#accentButton { background-color: #4d7658; border-color: #72a980; font-weight: 600; }
QPushButton#closeButton { min-width: 28px; max-width: 28px; padding: 1px; }
QPushButton#closeButton:hover { background-color: #7b3f45; border-color: #aa5960; }
QComboBox QAbstractItemView { background-color: #29312c; selection-background-color: #4d7658; }
QToolTip { background-color: #171c19; color: white; border: 1px solid #53665a; }
"""
