import sys
import os
import threading
import queue
import time
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QTextCursor

# Ensure that the parent directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audio.recorder import Recorder
from audio.transcriber import Transcriber

class TranscriptionWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcription UI (PyQt) - Dual Pane")
        self.resize(800, 600)
        
        # Create UI elements.
        self.start_button = QtWidgets.QPushButton("Start")
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.setEnabled(False)
        
        # Language drop-down for selecting target translation language.
        self.language_combo = QtWidgets.QComboBox()
        # Available languages: "en" means no translation; others will translate from English.
        self.language_combo.addItems(["en", "fr", "es", "de", "it", "pt"])
        self.language_combo.setCurrentText("fr")  # Default target language
        
        # Two text widgets: left for English, right for translated text.
        self.english_text_edit = QtWidgets.QTextEdit()
        self.english_text_edit.setReadOnly(True)
        self.translated_text_edit = QtWidgets.QTextEdit()
        self.translated_text_edit.setReadOnly(True)
        
        # Layout for the text panes (side-by-side).
        text_layout = QtWidgets.QHBoxLayout()
        text_layout.addWidget(self.english_text_edit)
        text_layout.addWidget(self.translated_text_edit)
        
        # Layout for buttons and language selection.
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(QtWidgets.QLabel("Target Language:"))
        button_layout.addWidget(self.language_combo)
        
        # Overall layout.
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addLayout(text_layout)
        self.setLayout(main_layout)
        
        # Connect signals.
        self.start_button.clicked.connect(self.start_transcription)
        self.stop_button.clicked.connect(self.stop_transcription)
        
        # Queues for inter-thread communication.
        self.audio_queue = queue.Queue()
        self.english_text_queue = queue.Queue()
        self.translated_text_queue = queue.Queue()
        
        # Event to signal threads to stop.
        self.stop_event = threading.Event()
        
        # Initialize Recorder and Transcriber.
        self.recorder = Recorder(sample_rate=16000, channels=1, dtype="float32")
        self.transcriber = Transcriber(model_name="base")
        
        # Timer to update text panes.
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_text_edits)
        self.timer.start(50)  # Poll every 50 ms.
    
    def start_transcription(self):
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.english_text_edit.clear()
        self.translated_text_edit.clear()
        self.stop_event.clear()
        
        # Start background threads.
        self.recording_thread = threading.Thread(target=self.recording_loop, daemon=True)
        self.transcription_thread = threading.Thread(target=self.transcription_loop, daemon=True)
        self.recording_thread.start()
        self.transcription_thread.start()
    
    def stop_transcription(self):
        self.stop_event.set()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def recording_loop(self):
        """Continuously record audio segments and put them in the audio queue."""
        segment_duration = 5  # seconds per segment.
        while not self.stop_event.is_set():
            audio_data = self.recorder.record(segment_duration)
            if audio_data is not None:
                self.audio_queue.put(audio_data)
            time.sleep(0.1)
    
    def transcription_loop(self):
        """
        For each audio segment, obtain the English transcription and then translate it.
        Both outputs are streamed character-by-character to separate queues.
        """
        while not self.stop_event.is_set():
            try:
                audio_data = self.audio_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            # Transcribe to English.
            for english_segment in self.transcriber.transcribe_stream(audio_data, language="en"):
                # Stream English text.
                for char in english_segment:
                    self.english_text_queue.put(char)
                    time.sleep(0.03)
                self.english_text_queue.put("\n")
                
                # Get target language from the drop-down.
                target_lang = self.language_combo.currentText().lower()
                if target_lang != "en":
                    # Translate the English segment.
                    translated_segment = self.transcriber.translate_text(english_segment, target_lang)
                else:
                    translated_segment = english_segment
                # Stream translated text.
                for char in translated_segment:
                    self.translated_text_queue.put(char)
                    time.sleep(0.03)
                self.translated_text_queue.put("\n")
            
            self.audio_queue.task_done()
    
    def update_text_edits(self):
        """Poll the text queues and update the corresponding text widgets."""
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

