import sys
import os
import threading
import queue
import time
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QTextCursor

from download_dialog import DownloadProgressDialog
from settings_dialog import SettingsDialog

#audio waveform
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

# Ensure that the parent directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audio.recorder import Recorder
from audio.transcriber import Transcriber
from audio.translator import Translator
from audio.waveform import WaveformUpdater

def is_model_cached(model_name):
    cache_dir = os.path.expanduser("~/.cache/whisper")
    model_path = os.path.join(cache_dir, f"{model_name}.pt")
    return os.path.exists(model_path)

class ModelLoader(QtCore.QThread):
    # Emit percentage, downloaded bytes, total bytes, and speed (in bits/s)
    loaded = QtCore.pyqtSignal(object)
    progress = QtCore.pyqtSignal(int, int, int, float)

    def __init__(self, model_name="base", parent=None):
        super().__init__(parent)
        self.model_name = model_name

    def run(self):
        # Simulated download parameters
        total_bytes = 100 * 1024 * 1024  # Example: 100 MB total
        downloaded = 0
        start_time = time.time()
        
        while downloaded < total_bytes:
            time.sleep(0.5)  # simulate waiting for a chunk
            downloaded += 5 * 1024 * 1024  # simulate a 5 MB chunk
            if downloaded > total_bytes:
                downloaded = total_bytes
            elapsed = time.time() - start_time
            speed = (downloaded * 8) / elapsed if elapsed > 0 else 0  # bits per second
            percentage = int((downloaded / total_bytes) * 100)
            self.progress.emit(percentage, downloaded, total_bytes, speed)
        
        # Once "download" is complete, load the model.
        transcriber = Transcriber(model_name=self.model_name)
        self.loaded.emit(transcriber)

class AudioWaveform(FigureCanvas):
    def __init__(self, parent=None, width=5, height=2, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setup_plot()

    def setup_plot(self):
        # Removing axes for a cleaner look
        self.axes.axis('off')
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)  # No margins

    def update_waveform(self, audio_data):
        self.axes.clear()
        self.setup_plot()  # Reset the plot styling after clearing

        # Convert audio data to numpy array (assuming float32 format)
        audio_array = np.frombuffer(audio_data, dtype=np.float32)

        # Plot the waveform
        self.axes.plot(audio_array, color='blue', lw=0.5)

        # Update the canvas
        self.draw()

class TranscriptionWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcription UI (PyQt) - Dual Pane with Logs")
        self.resize(800, 600)
        self.selected_device = None
        self.waveform_audio_queue = queue.Queue()

        # Create UI elements.
        self.start_button = QtWidgets.QPushButton("Start")
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.settings_button = QtWidgets.QPushButton("Settings")
        self.toggle_waveform_button = QtWidgets.QPushButton("Show Waveform")
        self.stop_button.setEnabled(False)
        
        self.language_combo = QtWidgets.QComboBox()
        self.language_combo.addItems(["en", "fr", "es", "de", "it", "pt"])
        self.language_combo.setCurrentText("en")
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        
        self.english_text_edit = QtWidgets.QTextEdit()
        self.english_text_edit.setReadOnly(True)
        self.translated_text_edit = QtWidgets.QTextEdit()
        self.translated_text_edit.setReadOnly(True)
        self.translated_text_edit.hide()
        
        self.log_text_edit = QtWidgets.QTextEdit()
        self.log_text_edit.setReadOnly(True)

        self.waveform_widget = AudioWaveform(self)
        self.waveform_widget.setVisible(False)

        self.text_layout = QtWidgets.QHBoxLayout()
        self.text_layout.addWidget(self.english_text_edit)
        self.text_layout.addWidget(self.translated_text_edit)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.settings_button)
        button_layout.addWidget(self.toggle_waveform_button)
        button_layout.addWidget(QtWidgets.QLabel("Target Language:"))
        button_layout.addWidget(self.language_combo)
        
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addLayout(self.text_layout)
        main_layout.addWidget(self.waveform_widget)  
        main_layout.addWidget(self.log_text_edit)  # Log text box

        self.setLayout(main_layout)
        
        self.start_button.clicked.connect(self.start_transcription)
        self.stop_button.clicked.connect(self.stop_transcription)
        self.settings_button.clicked.connect(self.show_settings)
        self.toggle_waveform_button.clicked.connect(self.toggle_waveform)
        self.start_button.setEnabled(False)
        
        self.audio_queue = queue.Queue()
        self.english_text_queue = queue.Queue()
        self.raw_transcription_queue = queue.Queue()
        self.translated_text_queue = queue.Queue()
        
        self.stop_event = threading.Event()
        
        self.recorder = Recorder(sample_rate=16000, channels=1, dtype="float32")
        self.update_log("Recorder Ready")
        self.recorder.log_signal.connect(self.update_log)

        self.translator = Translator()
        self.transcriber = None
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_text_edits)
        self.timer.start(50)
        
        self.model_loader = ModelLoader(model_name="base")
        self.model_loader.loaded.connect(self.on_model_loaded)
        self.update_log("Ready")
        
        if not is_model_cached("base"):
            self.download_dialog = DownloadProgressDialog(self)
            self.model_loader.progress.connect(self.download_dialog.update_progress)
            self.download_dialog.show()
        self.model_loader.start()


    def toggle_waveform(self):
        # Toggle visibility
        visible = self.waveform_widget.isVisible()
        self.waveform_widget.setVisible(not visible)

        # Update button text
        if visible:
            self.toggle_waveform_button.setText("Show Waveform")
        else:
            self.toggle_waveform_button.setText("Hide Waveform")

    def show_settings(self):
        # Placeholder method for settings dialog
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec_()
        self.selected_device = settings_dialog.get_selected_device_object()
        self.update_log(f"Selected input device: {self.selected_device['name']}")
        self.recorder.set_input_device(self.selected_device)
    
    def update_log(self, message):
        self.log_text_edit.append(message)
        self.log_text_edit.moveCursor(QTextCursor.End) 

    def update_waveform(self, audio_data):
        # Update the waveform widget using the audio data signal
        self.waveform_widget.update_waveform(audio_data)

    def on_model_loaded(self, transcriber):
        self.transcriber = transcriber
        self.start_button.setEnabled(True)
        if hasattr(self, 'download_dialog'):
            self.download_dialog.close()
    
    def on_language_changed(self, lang):
        if lang.lower() == "en":
            self.translated_text_edit.hide()
        else:
            self.translated_text_edit.show()
    
    def start_transcription(self):
        if self.transcriber is None:
            QtWidgets.QMessageBox.warning(self, "Model not loaded", "The transcription model is still loading. Please wait.")
            return
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.english_text_edit.clear()
        self.translated_text_edit.clear()
        self.stop_event.clear()
        
        self.recording_thread = threading.Thread(target=self.recording_loop, daemon=True)
        self.transcription_thread = threading.Thread(target=self.transcription_loop, daemon=True)
        self.translation_thread = threading.Thread(target=self.translation_loop, daemon=True)
        self.waveform_thread = WaveformUpdater(self.waveform_widget, self.waveform_audio_queue, self.stop_event)
        
        self.recording_thread.start()
        self.transcription_thread.start()
        self.translation_thread.start()
        self.waveform_thread.start()
    
    def stop_transcription(self):
        self.stop_event.set()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def recording_loop(self):
        segment_duration = 5
        while not self.stop_event.is_set():
            audio_data = self.recorder.record(segment_duration)
            if audio_data is not None:
                self.audio_queue.put(audio_data)
                self.waveform_widget.update_waveform(audio_data)
            time.sleep(0.1)
    
    def transcription_loop(self):
        while not self.stop_event.is_set():
            try:
                audio_data = self.audio_queue.get(timeout=1)
            except queue.Empty:
                continue
            for english_segment in self.transcriber.transcribe_stream(audio_data):
                for char in english_segment:
                    self.english_text_queue.put(char)
                    time.sleep(0.03)
                self.english_text_queue.put("\n")
                self.raw_transcription_queue.put(english_segment)
            self.audio_queue.task_done()
    
    def translation_loop(self):
        while not self.stop_event.is_set():
            try:
                english_segment = self.raw_transcription_queue.get(timeout=1)
            except queue.Empty:
                continue
            target_lang = self.language_combo.currentText().lower()
            if target_lang != "en":
                translated_segment = self.translator.translate(english_segment, target_lang)
            else:
                translated_segment = ""
            for char in translated_segment:
                self.translated_text_queue.put(char)
                time.sleep(0.03)
            self.translated_text_queue.put("\n")
            self.raw_transcription_queue.task_done()
    
    def update_text_edits(self):
        try:
            while True:
                char = self.english_text_queue.get_nowait()
                self.english_text_edit.moveCursor(QTextCursor.End)
                self.english_text_edit.insertPlainText(char)
                self.english_text_queue.task_done()
        except queue.Empty:
            pass
        try:
            while True:
                char = self.translated_text_queue.get_nowait()
                self.translated_text_edit.moveCursor(QTextCursor.End)
                self.translated_text_edit.insertPlainText(char)
                self.translated_text_queue.task_done()
        except queue.Empty:
            pass

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = TranscriptionWindow()
    window.show()
    sys.exit(app.exec_())
