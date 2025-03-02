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
from audio.translator import Translator

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
        # "en" means no translation; others will show a translation pane.
        self.language_combo.addItems(["en", "fr", "es", "de", "it", "pt"])
        self.language_combo.setCurrentText("en")  # Default target language is English.
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        
        # Two text widgets: left for English transcription, right for translated text.
        self.english_text_edit = QtWidgets.QTextEdit()
        self.english_text_edit.setReadOnly(True)
        self.translated_text_edit = QtWidgets.QTextEdit()
        self.translated_text_edit.setReadOnly(True)
        
        # By default, if language is "en", hide the translation pane.
        self.translated_text_edit.hide()
        
        # Layout for the text panes (side-by-side).
        self.text_layout = QtWidgets.QHBoxLayout()
        self.text_layout.addWidget(self.english_text_edit)
        self.text_layout.addWidget(self.translated_text_edit)
        
        # Layout for buttons and language selection.
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(QtWidgets.QLabel("Target Language:"))
        button_layout.addWidget(self.language_combo)
        
        # Overall layout.
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addLayout(self.text_layout)
        self.setLayout(main_layout)
        
        # Connect signals.
        self.start_button.clicked.connect(self.start_transcription)
        self.stop_button.clicked.connect(self.stop_transcription)
        
        # Queues for inter-thread communication.
        self.audio_queue = queue.Queue()
        self.english_text_queue = queue.Queue()     # For streaming English text.
        self.raw_transcription_queue = queue.Queue()  # For full English segments to translate.
        self.translated_text_queue = queue.Queue()    # For streaming translated text.
        
        # Event to signal threads to stop.
        self.stop_event = threading.Event()
        
        # Initialize Recorder, Transcriber, and Translator.
        self.recorder = Recorder(sample_rate=16000, channels=1, dtype="float32")
        self.transcriber = Transcriber(model_name="base")
        self.translator = Translator()
        
        # Timer to update text panes.
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_text_edits)
        self.timer.start(50)  # Poll every 50 ms.
    
    def on_language_changed(self, lang):
        target_lang = lang.lower()
        if target_lang == "en":
            # Hide the translation pane if no translation is needed.
            self.translated_text_edit.hide()
        else:
            # Show the translation pane for any language other than English.
            self.translated_text_edit.show()
    
    def start_transcription(self):
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.english_text_edit.clear()
        self.translated_text_edit.clear()
        self.stop_event.clear()
        
        # Start background threads.
        self.recording_thread = threading.Thread(target=self.recording_loop, daemon=True)
        self.transcription_thread = threading.Thread(target=self.transcription_loop, daemon=True)
        self.translation_thread = threading.Thread(target=self.translation_loop, daemon=True)
        
        self.recording_thread.start()
        self.transcription_thread.start()
        self.translation_thread.start()
    
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
        For each audio segment, obtain the English transcription and stream it
        character-by-character to the English text queue. Also, enqueue the full
        segment for translation.
        """
        while not self.stop_event.is_set():
            try:
                audio_data = self.audio_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            for english_segment in self.transcriber.transcribe_stream(audio_data):
                # Stream English text character-by-character.
                for char in english_segment:
                    self.english_text_queue.put(char)
                    time.sleep(0.03)
                self.english_text_queue.put("\n")
                # Enqueue the full segment for translation.
                self.raw_transcription_queue.put(english_segment)
            
            self.audio_queue.task_done()
    
    def translation_loop(self):
        """
        For each full English transcription segment in the raw transcription queue,
        translate it to the target language (if not English) and stream the result
        character-by-character to the translated text queue.
        """
        while not self.stop_event.is_set():
            try:
                english_segment = self.raw_transcription_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            target_lang = self.language_combo.currentText().lower()
            if target_lang != "en":
                translated_segment = self.translator.translate(english_segment, target_lang)
            else:
                # If English is selected, do not perform translation.
                translated_segment = ""
            
            for char in translated_segment:
                self.translated_text_queue.put(char)
                time.sleep(0.03)
            self.translated_text_queue.put("\n")
            
            self.raw_transcription_queue.task_done()
    
    def update_text_edits(self):
        """Polls the text queues and updates the corresponding text widgets."""
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
