import pyaudio
import threading
import queue
import time

# Constants
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

# Global buffer for audio data
audio_buffer = bytearray()

# Queues for transferring data between threads
recorded_chunks_queue = queue.Queue()
playback_chunks_queue = queue.Queue()

# Delay time
DELAY_SECONDS = 0.20

def record_audio():
    """ Record audio in chunks and put them in the recording queue. Also append to the global buffer. """
    global audio_buffer
    print("Recording thread started.")
    while recording:
        try:
            data = input_stream.read(CHUNK, exception_on_overflow=False)
            recorded_chunks_queue.put((data, time.time()))
            # Append data to the global buffer
            audio_buffer.extend(data)
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

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open streams
input_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
output_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)

# Start recording, playback, and transcription threads
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
