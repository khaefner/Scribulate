from PyQt5 import QtWidgets, QtCore
from audio.transcriber import Transcriber

class ModelLoaderThread(QtCore.QThread):
    # Signal that sends the loaded transcriber when finished.
    modelLoaded = QtCore.pyqtSignal(object)
    
    def __init__(self, model_name="base", parent=None):
        super().__init__(parent)
        self.model_name = model_name

    def run(self):
        # Load the Whisper model (this may download it if not cached).
        transcriber = Transcriber(model_name=self.model_name)
        self.modelLoaded.emit(transcriber)

class ModelLoaderDialog(QtWidgets.QDialog):
    """
    A modal dialog that shows a progress bar while the Whisper model is loaded.
    When finished, the loaded Transcriber is available via getTranscriber().
    """
    def __init__(self, model_name="base", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loading Whisper Model")
        self.resize(400, 150)
        self.model_name = model_name

        # Create UI elements.
        self.label = QtWidgets.QLabel("Loading Whisper model. Please wait...", self)
        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)

        # Layout.
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progressBar)
        self.setLayout(layout)

        # Start the loader thread.
        self.loaderThread = ModelLoaderThread(model_name=self.model_name)
        self.loaderThread.modelLoaded.connect(self.onModelLoaded)
        self.loaderThread.start()

        # Timer to simulate progress updates.
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.updateProgress)
        self.timer.start(100)  # update every 100 ms
        self.currentProgress = 0

    def updateProgress(self):
        # Simulate progress until near completion.
        if self.currentProgress < 90:
            self.currentProgress += 5
            self.progressBar.setValue(self.currentProgress)
        else:
            self.progressBar.setValue(100)

    def onModelLoaded(self, transcriber):
        # Stop the timer, record the loaded model, and close the dialog.
        self.timer.stop()
        self.transcriber = transcriber
        self.accept()

    def getTranscriber(self):
        """Return the loaded Transcriber instance."""
        return self.transcriber

