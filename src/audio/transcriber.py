import torch
import whisper
import numpy as np
import time

class Transcriber:
    """
    Transcriber uses OpenAI's Whisper model to perform automatic speech recognition.
    """
    def __init__(self, model_name="base", device=None, progress_callback=None):
        """
        Initializes the Transcriber with the specified Whisper model.

        Parameters:
            model_name (str): The Whisper model variant to use.
            device (str): Device to run the model on (e.g., "mps", "cuda", or "cpu").
                          If None, auto-detects the best available device.
            progress_callback (callable): A callback to report progress (0-100).
        """
        if device is None:
            if torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
        self.device = device
        print(f"Loading Whisper model: {model_name} on {self.device} ...")
        
        # If a progress callback is provided, simulate progress.
        if progress_callback:
            total_steps = 5
            for step in range(total_steps):
                time.sleep(0.3)  # simulate work
                progress = int((step + 1) / total_steps * 80)
                progress_callback(progress)
        
        # Load model on CPU first then move to the chosen device.
        self.model = whisper.load_model(model_name, device="cpu")
        if self.device != "cpu":
            try:
                self.model = self.model.to(self.device)
            except Exception as e:
                print("Error moving model to device; falling back to CPU.", e)
                self.device = "cpu"
        else:
            self.device = "cpu"
        
        # Finish progress if callback provided.
        if progress_callback:
            progress_callback(100)

    def transcribe(self, audio: np.ndarray) -> str:
        try:
            result = self.model.transcribe(audio)
            return result.get("text", "")
        except Exception as e:
            print("Error during transcription:", e)
            return ""
    
    def transcribe_stream(self, audio: np.ndarray):
        try:
            result = self.model.transcribe(audio)
            segments = result.get("segments", [])
            for segment in segments:
                text = segment.get("text", "")
                yield text
        except Exception as e:
            print("Error during streaming transcription:", e)
            yield ""
