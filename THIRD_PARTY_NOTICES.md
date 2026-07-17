# Third-Party Software Notices

BeeTales Translator Lens is distributed under the MIT License. Its Windows package also contains unmodified third-party libraries with their own licenses.

Important runtime components include PySide6/Qt, PaddlePaddle, PaddleOCR, OpenCV, NumPy, Argos Translate, CTranslate2, MiniSBD, ONNX Runtime, Lingua, MSS, and platformdirs. BeeTales includes the unmodified English, Spanish, Polish, Japanese, and Portuguese MiniSBD ONNX models from the upstream MiniSBD v0.0.1 release so sentence splitting is available offline. Translation model packages downloaded after installation may have additional notices supplied by their respective authors.

The corresponding package metadata and license files are included inside the `_internal` directory of the `onedir` distribution where provided by upstream packages. Before redistributing a build, review the licenses of every bundled dependency and downloaded model for the intended distribution context.

Project pages:

- PySide6: https://doc.qt.io/qtforpython-6/
- PaddlePaddle: https://www.paddlepaddle.org.cn/
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- OpenCV: https://opencv.org/
- Argos Translate: https://github.com/argosopentech/argos-translate
- CTranslate2: https://github.com/OpenNMT/CTranslate2
- MiniSBD and bundled sentence models: https://github.com/LibreTranslate/MiniSBD
- ONNX Runtime: https://onnxruntime.ai/
- Lingua: https://github.com/pemistahl/lingua-py
- PyInstaller: https://pyinstaller.org/
