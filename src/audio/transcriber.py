import torch
import whisper
import numpy as np

class Transcriber:
    """
    Transcriber uses OpenAI's Whisper model to perform automatic speech recognition.
    """
    def __init__(self, model_name="base", device=None):
        """
        Initializes the Transcriber with the specified Whisper model.

        Parameters:
            model_name (str): The Whisper model variant to use.
            device (str): Device to run the model on (e.g., "mps", "cuda", or "cpu").
                          If None, auto-detects the best available device.
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
    
    def transcribe(self, audio: np.ndarray) -> str:
        """
        Transcribes a given audio array into text.

        Parameters:
            audio (np.ndarray): Audio data as a 1D NumPy array sampled at 16 kHz.

        Returns:
            str: The full transcription text.
        """
        try:
            result = self.model.transcribe(audio)
            return result.get("text", "")
        except Exception as e:
            print("Error during transcription:", e)
            return ""
    
    def transcribe_stream(self, audio: np.ndarray):
        """
        Transcribes the audio and yields segments of text as they become available.

        Parameters:
            audio (np.ndarray): Audio data as a 1D NumPy array.

        Yields:
            str: Segments of transcribed text.
        """
        try:
            result = self.model.transcribe(audio)
            segments = result.get("segments", [])
            for segment in segments:
                text = segment.get("text", "")
                yield text
        except Exception as e:
            print("Error during streaming transcription:", e)
            yield ""

