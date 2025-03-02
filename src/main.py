import threading
import queue
import time
from audio.recorder import Recorder
from audio.transcriber import Transcriber

# Thread-safe queue for recorded audio segments.
audio_queue = queue.Queue()

def recording_thread(recorder, segment_duration):
    """
    Continuously record audio segments and put them in the shared queue.
    """
    while True:
        audio_data = recorder.record(segment_duration)
        if audio_data is not None:
            audio_queue.put(audio_data)


def transcription_thread(transcriber):
    """
    Continuously retrieve audio segments from the queue, transcribe them,
    and print out each segment character by character to simulate streaming.
    """
    while True:
        audio_data = audio_queue.get()  # Block until a segment is available.
        for segment in transcriber.transcribe_stream(audio_data):
            for char in segment:
                print(char, end="", flush=True)
                # Adjust the delay to control the streaming speed (in seconds)
                time.sleep(0.03)
        # Print a newline after finishing the segment
        print("", flush=True)
        audio_queue.task_done()

def main():
    # Initialize the recorder and transcriber.
    recorder = Recorder(sample_rate=16000, channels=1, dtype='float32')
    transcriber = Transcriber(model_name="base")
    segment_duration = 5  # seconds per recorded segment

    # Set up threads for recording and transcription.
    t_record = threading.Thread(
        target=recording_thread, 
        args=(recorder, segment_duration),
        daemon=True
    )
    t_transcribe = threading.Thread(
        target=transcription_thread, 
        args=(transcriber,),
        daemon=True
    )

    t_record.start()
    t_transcribe.start()

    print("Continuous streaming transcription started. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting continuous transcription.")

if __name__ == "__main__":
    main()

