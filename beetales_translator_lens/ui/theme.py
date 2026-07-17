"""BeeTales dark and light themes using the official brand palette."""

APP_STYLESHEET = """
QWidget {
    color: #fff3cf;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QDialog { background-color: #111713; }
QWidget#translationPanel, QWidget#toolbarSurface {
    background-color: #111713;
    border: 1px solid #4f6b28;
    border-radius: 10px;
}
QWidget#titleBar { background-color: #082b18; border-radius: 8px; }
QWidget#panelBody { background: transparent; border: none; }
QSplitter::handle { background-color: #4f6b28; border-radius: 3px; }
QSplitter::handle:hover { background-color: #a8db34; }
QSizeGrip#panelSizeGrip { width: 18px; height: 18px; }
QTabWidget::pane { border: 1px solid #4f6b28; border-radius: 6px; }
QTabBar::tab { background: #1b251d; color: #fff3cf; padding: 7px 12px; }
QTabBar::tab:selected { background: #526f20; color: #fff8df; }
QTabBar::tab:hover { background: #26351f; }
QLabel#appTitle { font-size: 11pt; font-weight: 600; color: #f4f8f5; }
QLabel#sectionTitle, QLabel#aboutVersion { color: #a8db34; font-weight: 600; }
QLabel#statusActive { color: #a8db34; font-weight: 600; }
QLabel#statusPaused { color: #ffb818; font-weight: 600; }
QTextEdit {
    background-color: #090d0b;
    border: 1px solid #3f5128;
    border-radius: 6px;
    padding: 7px;
    selection-background-color: #526f20;
}
QComboBox, QPushButton {
    background-color: #1b251d;
    border: 1px solid #536c2f;
    border-radius: 6px;
    min-height: 27px;
}
QPushButton { padding: 2px 9px; }
QComboBox { padding: 2px 28px 2px 9px; }
QComboBox::drop-down { width: 24px; border-left: 1px solid #536c2f; }
QComboBox:hover, QPushButton:hover { border-color: #a8db34; background-color: #26351f; }
QPushButton:pressed { background-color: #0d2115; }
QPushButton:checked { background-color: #405c1f; border-color: #a8db34; }
QPushButton#accentButton { background-color: #d96b0b; border-color: #ffb818; color: #fff7df; font-weight: 700; }
QPushButton#closeButton { min-width: 28px; max-width: 28px; padding: 1px; }
QPushButton#closeButton:hover { background-color: #7b3f45; border-color: #aa5960; }
QComboBox QAbstractItemView { background-color: #142018; selection-background-color: #526f20; }
QToolTip { background-color: #090d0b; color: #fff3cf; border: 1px solid #a8db34; }
"""

LIGHT_STYLESHEET = """
QWidget { color: #183018; font-family: "Segoe UI"; font-size: 10pt; }
QDialog { background-color: #fff8df; }
QWidget#translationPanel, QWidget#toolbarSurface {
    background-color: #fff8df; border: 1px solid #87a33b; border-radius: 10px;
}
QWidget#titleBar { background-color: #eaf3bf; border-radius: 8px; }
QWidget#panelBody { background: transparent; border: none; }
QSplitter::handle { background-color: #9bad62; border-radius: 3px; }
QSplitter::handle:hover { background-color: #79a51f; }
QSizeGrip#panelSizeGrip { width: 18px; height: 18px; }
QTabWidget::pane { border: 1px solid #87a33b; border-radius: 6px; }
QTabBar::tab { background: #f1f5d9; color: #183018; padding: 7px 12px; }
QTabBar::tab:selected { background: #d6e6a0; color: #183018; }
QTabBar::tab:hover { background: #e8f1bd; }
QLabel#appTitle { font-size: 11pt; font-weight: 600; color: #152219; }
QLabel#sectionTitle, QLabel#aboutVersion { color: #315d1d; font-weight: 600; }
QLabel#statusActive { color: #477c1e; font-weight: 600; }
QLabel#statusPaused { color: #a95b0c; font-weight: 600; }
QTextEdit { background-color: #fffef8; border: 1px solid #a6b86d; border-radius: 6px; padding: 7px; }
QComboBox, QPushButton, QLineEdit, QSpinBox {
    background-color: #f1f5d9; border: 1px solid #9bad62; border-radius: 6px;
    min-height: 27px;
}
QPushButton, QLineEdit, QSpinBox { padding: 2px 9px; }
QComboBox { padding: 2px 28px 2px 9px; }
QComboBox::drop-down { width: 24px; border-left: 1px solid #9bad62; }
QComboBox:hover, QPushButton:hover { border-color: #79a51f; background-color: #e8f1bd; }
QPushButton:checked { background-color: #d6e6a0; border-color: #79a51f; }
QPushButton#accentButton { background-color: #e57a14; border-color: #bd5c08; color: white; font-weight: 700; }
QPushButton#closeButton { min-width: 28px; max-width: 28px; padding: 1px; }
QPushButton#closeButton:hover { background-color: #a94e58; color: white; }
QToolTip { background-color: #fffef8; color: #183018; border: 1px solid #87a33b; }
"""


def stylesheet(theme: str) -> str:
    return LIGHT_STYLESHEET if theme == "light" else APP_STYLESHEET
