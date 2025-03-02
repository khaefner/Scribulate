from PyQt5 import QtWidgets, QtCore

class DownloadProgressDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Downloading Model")
        self.resize(400, 150)
        # Ensure the dialog stays on top and is modal.
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        
        self.bytes_label = QtWidgets.QLabel("Downloaded: 0 / 0 bytes")
        self.speed_label = QtWidgets.QLabel("Speed: 0.00 bits/s")
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Downloading Whisper model..."))
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.bytes_label)
        layout.addWidget(self.speed_label)
        self.setLayout(layout)
    
    @QtCore.pyqtSlot(int, int, int, float)
    def update_progress(self, percentage, downloaded, total, speed):
        self.progress_bar.setValue(percentage)
        self.bytes_label.setText(f"Downloaded: {downloaded} / {total} bytes")
        self.speed_label.setText(f"Speed: {speed:.2f} bits/s")
