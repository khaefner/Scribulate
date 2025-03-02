import sounddevice as sd
import numpy as np

class Recorder:
    """
    Recorder encapsulates functionality to record audio from the default microphone.
    
    Attributes:
        sample_rate (int): The sampling rate in Hz.
        channels (int): Number of audio channels.
        dtype (str): Data type for audio samples.
    """
    
    def __init__(self, sample_rate=16000, channels=1, dtype='float32'):
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype

    def record(self, duration):
        """
        Records audio for a specified duration.

        Parameters:
            duration (float): Duration in seconds to record audio.

        Returns:
            np.ndarray: Recorded audio data as a NumPy array.
        """
        #print(f"Recording for {duration} seconds at {self.sample_rate} Hz...")
        try:
            # Calculate the number of samples to record
            num_samples = int(duration * self.sample_rate)
            audio = sd.rec(num_samples, samplerate=self.sample_rate, 
                           channels=self.channels, dtype=self.dtype)
            sd.wait()  # Wait until recording is finished
            # If single channel, squeeze the extra dimension
            if self.channels == 1:
                audio = np.squeeze(audio)
            return audio
        except Exception as e:
            print("Error while recording audio:", e)
            return None

    def list_input_devices(self):
        """
        Lists available input devices.
        """
        print("Available input devices:")
        try:
            devices = sd.query_devices()
            for idx, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    print(f"{idx}: {device['name']}")
        except Exception as e:
            print("Error retrieving input devices:", e)

if __name__ == "__main__":
    # Example usage for testing the recorder functionality.
    recorder = Recorder()
    recorder.list_input_devices()
    
    duration = 5  # Record for 5 seconds
    audio_data = recorder.record(duration)
    
    if audio_data is not None:
        print("Audio recorded successfully. Data shape:", audio_data.shape)
    else:
        print("Recording failed.")

