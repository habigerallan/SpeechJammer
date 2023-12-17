import pyaudio
import threading
import queue
import time
import speech_recognition as sr

# Constants
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
DELAY_SECONDS = 2
RECOGNIZER = sr.Recognizer()

# Queues for transferring data between threads
recorded_chunks_queue = queue.Queue()
playback_chunks_queue = queue.Queue()

def record_audio():
    """ Record audio in chunks and put them in the recording queue. """
    print("Recording thread started.")
    while recording:
        try:
            data = input_stream.read(CHUNK, exception_on_overflow=False)
            recorded_chunks_queue.put((data, time.time()))
        except Exception as e:
            print(f"Recording thread error: {e}")
            break

def playback_audio():
    """ Play audio chunks from the playback queue. """
    print("Playback thread started.")
    while playing:
        if not playback_chunks_queue.empty():
            data, _ = playback_chunks_queue.get()
            output_stream.write(data)

def transcribe(data):
    """ Transcribe audio to text. """
    try:
        with sr.AudioFile(data) as source:
            audio_data = RECOGNIZER.record(source)
            text = RECOGNIZER.recognize_google(audio_data)
            print(f"Transcribed: {text}")
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open streams
input_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
output_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)

# Start recording and playback threads
recording = True
playing = True
recording_thread = threading.Thread(target=record_audio)
playback_thread = threading.Thread(target=playback_audio)
recording_thread.start()
playback_thread.start()

print("Main thread: Managing data transfer...")
try:
    while True:
        if not recorded_chunks_queue.empty():
            data, record_time = recorded_chunks_queue.get()
            while time.time() < record_time + DELAY_SECONDS:
                continue
            transcribe(data)  # Transcribe the audio
            playback_chunks_queue.put((data, record_time))
except KeyboardInterrupt:
    print("\nStopping...")

# Signal threads to stop
recording = False
playing = False

# Wait for threads to finish
recording_thread.join()
playback_thread.join()

# Close streams
input_stream.stop_stream()
input_stream.close()
output_stream.stop_stream()
output_stream.close()
p.terminate()

print("Terminated")
