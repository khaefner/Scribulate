import torch
import whisper
import numpy as np
from transformers import pipeline

class Transcriber:
    """
    Transcriber uses OpenAI's Whisper model to perform automatic speech recognition,
    and can translate the transcribed text into various languages using Hugging Face's MarianMT.
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
        # Load model on CPU first then move to the chosen device
        self.model = whisper.load_model(model_name, device="cpu")
        if self.device != "cpu":
            try:
                self.model = self.model.to(self.device)
            except Exception as e:
                print("Error moving model to device; falling back to CPU.", e)
                self.device = "cpu"
        else:
            self.device = "cpu"
        
        # Dictionary to hold translation pipelines keyed by target language code
        self.translation_pipelines = {}

    def transcribe(self, audio: np.ndarray) -> str:
        """
        Transcribes a given audio array into text.

        Parameters:
            audio (np.ndarray): Audio data as a 1D NumPy array sampled at 16 kHz.

        Returns:
            str: The transcription text.
        """
        try:
            result = self.model.transcribe(audio)
            return result.get("text", "")
        except Exception as e:
            print("Error during transcription:", e)
            return ""

    def transcribe_stream(self, audio: np.ndarray, language: str = None):
        """
        Transcribes the audio and yields segments of text as they become available.
        Optionally translates each segment if a target language is specified.
        
        Parameters:
            audio (np.ndarray): Audio data as a 1D NumPy array.
            language (str): Target language code for translation (e.g. "fr", "es"). 
                            If None or "en", no translation is done.
                            
        Yields:
            str: Segments of transcribed (and possibly translated) text.
        """
        try:
            result = self.model.transcribe(audio)
            segments = result.get("segments", [])
            for segment in segments:
                text = segment.get("text", "")
                # If a target language is provided and it's not English, translate the segment.
                if language and language.lower() != "en":
                    text = self.translate_text(text, target_lang=language.lower())
                yield text
        except Exception as e:
            print("Error during streaming transcription:", e)
            yield ""

    def translate_text(self, text: str, target_lang: str) -> str:
        """
        Translates a given text from English to the target language using MarianMT.
        
        Parameters:
            text (str): The text to translate.
            target_lang (str): The target language code (e.g., "fr" for French, "es" for Spanish).
            
        Returns:
            str: The translated text.
        """
        # Mapping from target language code to MarianMT model names.
        model_map = {
            'fr': "Helsinki-NLP/opus-mt-en-fr",
            'es': "Helsinki-NLP/opus-mt-en-es",
            'de': "Helsinki-NLP/opus-mt-en-de",
            'it': "Helsinki-NLP/opus-mt-en-it",
            'pt': "Helsinki-NLP/opus-mt-en-pt",
            # Add more mappings as needed.
        }
        if target_lang == "en":
            return text  # No translation needed.
        if target_lang not in model_map:
            print(f"No translation model available for language: {target_lang}. Returning original text.")
            return text

        # Load the translator pipeline if not already loaded.
        if target_lang not in self.translation_pipelines:
            try:
                translator = pipeline("translation", model=model_map[target_lang])
                self.translation_pipelines[target_lang] = translator
            except Exception as e:
                print(f"Error loading translation model for {target_lang}: {e}")
                return text

        translator = self.translation_pipelines[target_lang]
        try:
            translated = translator(text, max_length=512)
            return translated[0]['translation_text']
        except Exception as e:
            print("Error during translation:", e)
            return text

if __name__ == "__main__":
    # Example usage: Generate a dummy audio signal for testing.
    import numpy as np
    duration = 3  # seconds
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    audio = 0.5 * np.sin(2 * np.pi * 440 * t).astype(np.float32)

    transcriber = Transcriber(model_name="base")
    # Transcribe and translate to French.
    for segment in transcriber.transcribe_stream(audio, language="fr"):
        print(segment, end="")
    print()

