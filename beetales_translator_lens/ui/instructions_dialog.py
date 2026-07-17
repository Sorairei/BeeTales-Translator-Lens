"""Detailed in-application operating guide."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
)

from beetales_translator_lens.constants import APP_NAME


class InstructionsDialog(QDialog):
    """Explain the complete BeeTales workflow without leaving the application."""

    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.setWindowTitle(f"How to use {APP_NAME}")
        self.setMinimumSize(680, 560)
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.setObjectName("instructionsTabs")
        tabs.addTab(self._page(self._quick_start_html()), "Quick start")
        tabs.addTab(self._page(self._controls_html()), "Controls")
        tabs.addTab(self._page(self._models_privacy_html()), "Models and privacy")
        tabs.addTab(self._page(self._troubleshooting_html()), "Troubleshooting")
        layout.addWidget(tabs)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _page(html: str) -> QTextBrowser:
        page = QTextBrowser()
        page.setOpenExternalLinks(True)
        page.setHtml(html)
        return page

    @staticmethod
    def _quick_start_html() -> str:
        return """
        <h2>Translate text on your screen</h2>
        <ol>
          <li>Move and resize the green lens so it covers only the text you want to read.</li>
          <li>Select the text language under <b>Source language</b>. Use <b>Automatic</b>
              when the language is unknown.</li>
          <li>Select the desired translation language under <b>Target language</b>.</li>
          <li>Leave <b>Image preprocessing</b> on <b>Automatic</b> for most applications.</li>
          <li>Click <b>Start</b>. The first use of a language may download local OCR and
              translation models after asking for permission.</li>
          <li>Read the recognized text and translation in the two adjustable panes.</li>
        </ol>
        <h3>Recommended starting settings</h3>
        <ul>
          <li><b>Capture interval: 2000 ms</b> — responsive without keeping the CPU busy.</li>
          <li><b>Change sensitivity: Normal</b> — suitable for chats and documents.</li>
          <li><b>Image preprocessing: Automatic</b> — adapts to light and dark backgrounds.</li>
        </ul>
        <p>Drag the divider between <b>Detected text</b> and <b>Translation</b> to give either
        pane more room. Drag the lower-right corner to resize the complete window.</p>
        """

    @staticmethod
    def _controls_html() -> str:
        return """
        <h2>Main controls</h2>
        <dl>
          <dt><b>Start / Force read</b></dt><dd>Starts scanning. While active, forces an
          immediate scan even if the image appears unchanged.</dd>
          <dt><b>Pause</b></dt><dd>Temporarily stops scanning without closing the lens.</dd>
          <dt><b>Copy / Copy original</b></dt><dd>Copies the translation or recognized text.</dd>
          <dt><b>Clear</b></dt><dd>Clears both text panes.</dd>
          <dt><b>Swap</b></dt><dd>Exchanges source and target languages when the source is
          not Automatic.</dd>
          <dt><b>Lock lens</b></dt><dd>Prevents accidental movement or resizing.</dd>
          <dt><b>Capture preview</b></dt><dd>Shows what OCR receives and performance details.</dd>
          <dt><b>Click-through</b></dt><dd>Lets mouse clicks pass through the lens to the
          application underneath.</dd>
          <dt><b>Models</b></dt><dd>Shows installed translation models and lets you remove
          models you no longer need.</dd>
        </dl>
        <h3>Capture profiles</h3>
        <p>Use <b>Small text</b> for tiny chat fonts, the light/dark profiles when Automatic
        chooses poorly, and <b>Japanese horizontal text</b> for horizontal Japanese writing.</p>
        """

    @staticmethod
    def _models_privacy_html() -> str:
        return """
        <h2>Local models</h2>
        <p>BeeTales uses PaddleOCR for recognition and Argos Translate for translation.
        Models are downloaded only after confirmation and then run locally. Some language
        pairs use English as a private local bridge, for example Polish → English → Spanish.</p>
        <h2>Privacy</h2>
        <ul>
          <li>Screen captures are processed in memory and are not saved.</li>
          <li>Telemetry is not included.</li>
          <li>Translation history is disabled by default.</li>
          <li>Enable <b>Save translation history</b> only if you want text stored locally.</li>
          <li><b>Clear saved data</b> removes saved history and the persistent translation cache.</li>
        </ul>
        <p>Downloaded models, settings, and optional history are stored in the BeeTales folder
        under your local Windows application data.</p>
        """

    @staticmethod
    def _troubleshooting_html() -> str:
        return """
        <h2>If no text appears</h2>
        <ol>
          <li>Make the lens slightly larger than the text and avoid covering it with another window.</li>
          <li>Choose the exact source language instead of Automatic.</li>
          <li>Try <b>Small text</b> or the matching light/dark preprocessing profile.</li>
          <li>Use <b>Force read</b> after changing the lens position.</li>
          <li>Increase the application zoom or font size when possible.</li>
        </ol>
        <h2>If scanning feels slow</h2>
        <ul>
          <li>Use a 1500–2000 ms capture interval.</li>
          <li>Cover only the useful text area; a larger lens requires more OCR work.</li>
          <li>The first scan is slower because local models must be loaded into memory.</li>
          <li>Later scans reuse the loaded model and translation cache.</li>
        </ul>
        <h2>If translation is unavailable</h2>
        <p>Accept the model installation prompt while connected to the internet. After the
        required models are installed, translation continues locally and can work offline.</p>
        """
