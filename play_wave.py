import wave
import numpy as np
import pyaudio
import threading
import time
import sys
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from tqdm import tqdm


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


def calculate_stft(samples, frequencies, sample_rate):
    window_size = sample_rate // 10  # 0.1 seconds
    hop_size = sample_rate // 10  # 0.1 seconds
    n_samples = len(samples)

    # Pad the signal to ensure we can calculate STFT for the entire duration
    padded_samples = np.pad(samples, (0, window_size))

    n_windows = (n_samples - window_size) // hop_size + 1
    stft = np.zeros((len(frequencies), n_windows), dtype=np.complex128)

    for i in tqdm(range(n_windows)):
        start = i * hop_size
        end = start + window_size
        window = padded_samples[start:end]

        for j, freq in enumerate(frequencies):
            t = np.arange(window_size) / sample_rate
            stft[j, i] = np.sum(window * np.exp(-2j * np.pi * freq * t))

    return np.abs(stft) ** 2  # Return power spectrum


def stereo_to_mono_play_and_plot(input_file):
    with wave.open(input_file, "rb") as wf:
        nchannels, sampwidth, framerate, nframes, comptype, compname = wf.getparams()
        frames = wf.readframes(nframes)

    samples = np.frombuffer(frames, dtype=np.int16)
    samples = samples.reshape(-1, nchannels)
    mono_samples = samples.mean(axis=1, dtype=np.int16)

    # Calculate full STFT
    frequencies = generate_piano_frequencies()
    full_stft = calculate_stft(mono_samples, frequencies, framerate)

    # Set up the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    (line,) = ax1.plot([], [])
    segment_len = framerate // 10  # 100ms of data
    ax1.set_xlim(0, segment_len)
    ax1.set_ylim(np.min(mono_samples), np.max(mono_samples))
    ax1.set_title("Real-time Waveform")
    ax1.set_xlabel("Sample")
    ax1.set_ylabel("Amplitude")

    # Normalize the STFT
    normalized_stft = full_stft / np.max(full_stft)

    spectrogram = ax2.imshow(
        normalized_stft,
        aspect="auto",
        origin="lower",
        cmap="Reds",
        extent=[0, len(mono_samples) / framerate, 0, len(frequencies)],
        vmin=0,
        vmax=1,
    )
    fig.colorbar(spectrogram, ax=ax2, label="Normalized Power")
    ax2.set_title("Spectrogram")
    ax2.set_xlabel("Time (seconds)")
    ax2.set_ylabel("Piano Key")
    ax2.set_yticks(np.arange(0, 88, 12))
    ax2.set_yticklabels(["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7"])

    player = AudioPlayer(mono_samples, sampwidth, framerate)
    play_thread = threading.Thread(target=player.play_audio)
    play_thread.start()

    def update_plot(frame):
        start = player.current_position
        end = start + segment_len
        segment = mono_samples[start:end]

        # Update waveform
        line.set_data(range(len(segment)), segment)

        # Update spectrogram view
        current_time = start / framerate
        ax2.set_xlim(max(0, current_time - 10), current_time)

        return line, spectrogram

    ani = FuncAnimation(fig, update_plot, interval=100, blit=True)

    print(
        "Playing audio and plotting waveform and spectrogram. Close the plot window to stop."
    )
    plt.tight_layout()
    plt.show()

    player.stop()
    play_thread.join()

    print("Playback and plotting finished.")


if __name__ == "__main__":
    input_file = "ThatchedVillagers.wav"
    stereo_to_mono_play_and_plot(input_file)
