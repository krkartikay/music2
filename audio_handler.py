import pyaudio
import wave
import threading
import numpy as np


class AudioHandler:
    def __init__(self):
        self.audio_file = None
        self.is_playing = False
        self.play_thread = None
        self.waveform = None

    def load_file(self, file_path):
        self.audio_file = file_path
        self.load_waveform()

    def load_waveform(self):
        if self.audio_file:
            with wave.open(self.audio_file, "rb") as wf:
                self.waveform = np.frombuffer(
                    wf.readframes(wf.getnframes()), dtype=np.int16
                )
                self.waveform = (
                    self.waveform.astype(np.float32) / 32768.0
                )  # Normalize to [-1, 1]

    def play(self):
        if not self.audio_file or self.is_playing:
            return

        self.is_playing = True
        self.play_thread = threading.Thread(target=self._play_audio_thread)
        self.play_thread.start()

    def _play_audio_thread(self):
        chunk = 1024
        wf = wave.open(self.audio_file, "rb")
        p = pyaudio.PyAudio()

        stream = p.open(
            format=p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True,
        )

        data = wf.readframes(chunk)

        while data and self.is_playing:
            stream.write(data)
            data = wf.readframes(chunk)

        stream.stop_stream()
        stream.close()
        p.terminate()
        self.is_playing = False

    def stop(self):
        self.is_playing = False
        if self.play_thread:
            self.play_thread.join()
