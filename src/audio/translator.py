from transformers import pipeline

class Translator:
    """
    Translator uses Hugging Face's MarianMT models to translate text from English to a target language.
    """
    def __init__(self):
        # Dictionary to cache translation pipelines keyed by target language code.
        self.translation_pipelines = {}
        # Mapping from target language code to MarianMT model names.
        self.model_map = {
            'fr': "Helsinki-NLP/opus-mt-en-fr",
            'es': "Helsinki-NLP/opus-mt-en-es",
            'de': "Helsinki-NLP/opus-mt-en-de",
            'it': "Helsinki-NLP/opus-mt-en-it",
            'pt': "Helsinki-NLP/opus-mt-en-pt",
            # Add more mappings as needed.
        }
    
    def translate(self, text: str, target_lang: str) -> str:
        """
        Translates a given text from English to the target language using MarianMT.

        Parameters:
            text (str): The text to translate.
            target_lang (str): The target language code (e.g., "fr" for French, "es" for Spanish).

        Returns:
            str: The translated text.
        """
        target_lang = target_lang.lower()
        if target_lang == "en":
            return text  # No translation needed.
        if target_lang not in self.model_map:
            print(f"No translation model available for language: {target_lang}. Returning original text.")
            return text
        
        # Load the translator pipeline if not already cached.
        if target_lang not in self.translation_pipelines:
            try:
                translator = pipeline("translation", model=self.model_map[target_lang])
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

