import wave
import numpy as np
import pyaudio
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.fft import fft
from scipy.signal import find_peaks
from collections import deque


class AudioPlayer:
    def __init__(self, mono_samples, sampwidth, framerate):
        self.mono_samples = mono_samples
        self.sampwidth = sampwidth
        self.framerate = framerate
        self.playing = False
        self.p = None
        self.stream = None
        self.current_position = 0

    def play_audio(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.p.get_format_from_width(self.sampwidth),
            channels=1,
            rate=self.framerate,
            output=True,
            stream_callback=self.callback,
        )

        self.playing = True
        self.stream.start_stream()

        while self.stream.is_active() and self.playing:
            time.sleep(0.1)

        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def callback(self, in_data, frame_count, time_info, status):
        data = self.mono_samples[
            self.current_position : self.current_position + frame_count
        ]
        self.current_position += frame_count
        return (data.tobytes(), pyaudio.paContinue)

    def stop(self):
        self.playing = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.p:
            self.p.terminate()


def generate_piano_frequencies():
    return [27.5 * (2 ** (i / 12)) for i in range(88)]


def calculate_fft(samples, sample_rate):
    fft_result = fft(samples)
    freqs = np.fft.fftfreq(len(samples), 1 / sample_rate)
    return freqs[: len(freqs) // 2], np.abs(fft_result[: len(fft_result) // 2])


def find_dominant_notes(freqs, magnitudes, piano_freqs, num_notes=3):
    peaks, _ = find_peaks(magnitudes, height=np.max(magnitudes) / 10)
    dominant_freqs = freqs[peaks]
    dominant_mags = magnitudes[peaks]

    sorted_indices = np.argsort(dominant_mags)[::-1]
    top_freqs = dominant_freqs[sorted_indices][:num_notes]

    notes = []
    for freq in top_freqs:
        note_index = np.argmin(np.abs(np.array(piano_freqs) - freq))
        note_name = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"][
            note_index % 12
        ]
        octave = note_index // 12
        notes.append(f"{note_name}{octave}")

    return notes


def mono_play_and_plot(input_file):
    with wave.open(input_file, "rb") as wf:
        nchannels, sampwidth, framerate, nframes, comptype, compname = wf.getparams()
        frames = wf.readframes(nframes)

    samples = np.frombuffer(frames, dtype=np.int16)
    if nchannels == 2:
        samples = samples.reshape(-1, nchannels)
        mono_samples = samples.mean(axis=1, dtype=np.int16)
    else:
        mono_samples = samples

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    (line,) = ax1.plot([], [])
    segment_len = framerate // 10  # 100ms of data
    ax1.set_xlim(0, segment_len)
    ax1.set_ylim(np.min(mono_samples), np.max(mono_samples))
    ax1.set_title("Real-time Waveform")
    ax1.set_xlabel("Sample")
    ax1.set_ylabel("Amplitude")

    fft_history = deque(maxlen=100)  # Store 10 seconds of FFT data
    freqs, _ = calculate_fft(mono_samples[:segment_len], framerate)
    spectrogram = ax2.imshow(
        np.zeros((len(freqs), 100)),
        aspect="auto",
        origin="lower",
        cmap="Reds",
        extent=[0, 10, 0, framerate // 2],
        vmin=0,
        vmax=1,
    )
    fig.colorbar(spectrogram, ax=ax2, label="Normalized Magnitude")
    ax2.set_title("FFT Spectrogram")
    ax2.set_xlabel("Time (seconds)")
    ax2.set_ylabel("Frequency (Hz)")

    piano_freqs = generate_piano_frequencies()
    dominant_notes_text = ax2.text(
        0.02, 0.95, "", transform=ax2.transAxes, verticalalignment="top"
    )

    player = AudioPlayer(mono_samples, sampwidth, framerate)
    play_thread = threading.Thread(target=player.play_audio)
    play_thread.start()

    def update_plot(frame):
        start = player.current_position
        end = start + segment_len
        segment = mono_samples[start:end]

        # Update waveform
        line.set_data(range(len(segment)), segment)

        # Calculate and update FFT
        freqs, magnitudes = calculate_fft(segment, framerate)
        normalized_magnitudes = magnitudes / np.max(magnitudes)
        fft_history.append(normalized_magnitudes)

        # Update spectrogram
        spectrogram.set_array(np.array(fft_history).T)
        spectrogram.set_extent(
            [start / framerate - 10, start / framerate, 0, framerate // 2]
        )

        # Find and display dominant notes
        dominant_notes = find_dominant_notes(freqs, magnitudes, piano_freqs)
        dominant_notes_text.set_text(f"Dominant Notes: {', '.join(dominant_notes)}")

        return line, spectrogram, dominant_notes_text

    ani = FuncAnimation(fig, update_plot, interval=100, blit=True)

    print(
        "Playing audio and plotting waveform and FFT spectrogram. Close the plot window to stop."
    )
    plt.tight_layout()
    plt.show()

    player.stop()
    play_thread.join()

    print("Playback and plotting finished.")


if __name__ == "__main__":
    input_file = "ThatchedVillagers.wav"
    mono_play_and_plot(input_file)
