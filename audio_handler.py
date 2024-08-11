import pyaudio
import wave
import threading
import numpy as np

from PySide6.QtCore import QObject, Signal


class AudioHandler(QObject):
    playback_position_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_file = None
        self.is_playing = False
        self.play_thread = None
        self.waveform = None
        self.current_position = 0

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
            self.current_position += chunk
            self.playback_position_changed.emit(self.current_position)

        stream.stop_stream()
        stream.close()
        p.terminate()
        self.is_playing = False

    def seek(self, position):
        if self.audio_file:
            with wave.open(self.audio_file, "rb") as wf:
                wf.setpos(position)
            self.current_position = position
            self.playback_position_changed.emit(self.current_position)

    def stop(self):
        self.is_playing = False
        if self.play_thread:
            self.play_thread.join()
