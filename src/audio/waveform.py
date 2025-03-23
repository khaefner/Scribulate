import threading
import queue
from PyQt5.QtCore import QThread, pyqtSignal

class WaveformUpdater(threading.Thread):
    audio_data_signal = pyqtSignal(object)
    def __init__(self, waveform_widget, audio_queue, stop_event):
        super().__init__(daemon=True)
        self.waveform_widget = waveform_widget
        self.audio_queue = audio_queue
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            try:
                # Fetch audio data from the queue
                audio_data = self.audio_queue.get(timeout=1)
                if audio_data is not None:
                    self.audio_data_signal.emit(audio_data)
                    #self.waveform_widget.update_waveform(audio_data)
                self.audio_queue.task_done()
            except queue.Empty:
                continue
