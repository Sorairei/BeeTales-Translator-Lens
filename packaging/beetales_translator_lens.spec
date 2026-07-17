"""Reproducible Windows onedir build for BeeTales Translator Lens."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, copy_metadata

project_root = Path(SPECPATH).resolve().parent

binaries = []
datas = [
    (
        str(project_root / "beetales_translator_lens" / "resources" / "icons" / "beetales_translator_lens.png"),
        "beetales_translator_lens/resources/icons",
    ),
    (
        str(project_root / "beetales_translator_lens" / "resources" / "minisbd_models"),
        "beetales_translator_lens/resources/minisbd_models",
    ),
]
hiddenimports = []

for package_name in ("argostranslate", "minisbd", "paddleocr", "paddlex"):
    datas += collect_data_files(package_name)

for package_name in ("argostranslate", "ctranslate2", "lingua-language-detector", "minisbd", "paddleocr", "paddlex"):
    datas += copy_metadata(package_name)

for package_name in ("ctranslate2", "paddle"):
    binaries += collect_dynamic_libs(package_name)

hiddenimports += [
    "paddleocr._pipelines.ocr",
    "paddlex.inference.pipelines.ocr",
    "paddlex.inference.pipelines.doc_preprocessor",
    "paddlex.inference.models.text_detection",
    "paddlex.inference.models.text_recognition",
]

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "IPython",
        "fastapi",
        "functorch",
        "gradio",
        "jupyter",
        "matplotlib",
        "modelscope",
        "notebook",
        "pptx",
        "pypdfium2",
        "pytest",
        "spacy",
        "stanza",
        "thinc",
        "tkinter",
        "torch",
        "transformers",
        "uvicorn",
        "xlsxwriter",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BeeTalesTranslatorLens",
    icon=str(project_root / "packaging" / "beetales_translator_lens.ico"),
    version=str(project_root / "packaging" / "version_info.txt"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="BeeTales Translator Lens",
)
