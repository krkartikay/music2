import wave
import numpy as np
import pyaudio
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Rectangle
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
    return [440 * (2 ** ((i - 49) / 12)) for i in range(88)]  # A4 is 49th key


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


def freq_to_pitch(freq):
    return 12 * np.log2(freq / 440) + 49  # A4 is 49th key


def pitch_to_note(pitch):
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = (pitch // 12) - 1
    note = note_names[pitch % 12]
    return f"{note}{octave}"


def create_piano_keyboard(ax):
    white_keys = [0, 2, 4, 5, 7, 9, 11]  # C, D, E, F, G, A, B
    black_keys = [1, 3, 6, 8, 10]  # C#, D#, F#, G#, A#
    key_width = 1
    black_key_width = 0.7
    black_key_height = 0.6

    keys = []
    total_white_keys = 52  # 88-key piano has 52 white keys

    for i in range(88):  # 88 keys total
        octave = (i + 9) // 12  # Start from A0 (9 keys before C1)
        note = (i + 9) % 12

        if note in white_keys:
            x = len(
                [k for k in keys if isinstance(k, Rectangle) and k.get_height() == 1]
            )
            key = Rectangle(
                (x, 0), key_width, 1, facecolor="white", edgecolor="black", zorder=1
            )
        else:
            prev_white = (
                len(
                    [
                        k
                        for k in keys
                        if isinstance(k, Rectangle) and k.get_height() == 1
                    ]
                )
                - 1
            )
            x = prev_white + 0.65
            key = Rectangle(
                (x, 0.4),
                black_key_width,
                black_key_height,
                facecolor="black",
                edgecolor="black",
                zorder=2,
            )

        ax.add_patch(key)
        keys.append(key)

    ax.set_xlim(0, total_white_keys)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return keys


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

    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(12, 8), gridspec_kw={"height_ratios": [1, 1, 0.5]}
    )
    (line,) = ax1.plot([], [])
    segment_len = framerate // 10  # 100ms of data
    ax1.set_xlim(0, segment_len)
    ax1.set_ylim(np.min(mono_samples), np.max(mono_samples))
    ax1.set_title("Real-time Waveform")
    ax1.set_xlabel("Sample")
    ax1.set_ylabel("Amplitude")

    fft_history = deque(maxlen=100)  # Store 10 seconds of FFT data
    freqs, _ = calculate_fft(mono_samples[:segment_len], framerate)
    pitches = freq_to_pitch(freqs)

    # Filter pitches to show A0 (MIDI note 21) to C8 (MIDI note 108)
    pitch_mask = (pitches >= 21) & (pitches <= 108)
    pitches = pitches[pitch_mask]

    spectrogram = ax2.imshow(
        np.zeros((len(pitches), 100)),
        aspect="auto",
        origin="lower",
        cmap="Reds",
        extent=[0, 10, 21, 108],
        vmin=0,
        vmax=1,
    )
    fig.colorbar(spectrogram, ax=ax2, label="Normalized Magnitude")
    ax2.set_title("Piano Roll Spectrogram (A0-C8)")
    ax2.set_xlabel("Time (seconds)")
    ax2.set_ylabel("Pitch")

    # Set y-axis ticks to show octaves
    ax2.set_yticks([21, 33, 45, 57, 69, 81, 93, 105])
    ax2.set_yticklabels(["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7"])

    piano_freqs = generate_piano_frequencies()
    dominant_notes_text = ax2.text(
        0.02, 0.95, "", transform=ax2.transAxes, verticalalignment="top"
    )

    # Create piano keyboard visualization
    keys = create_piano_keyboard(ax3)
    ax3.set_title("Piano Keyboard Visualization")

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
        pitches = freq_to_pitch(freqs)
        pitch_mask = (pitches >= 48) & (pitches <= 96)

        normalized_magnitudes = magnitudes / np.max(magnitudes)
        fft_history.append(normalized_magnitudes[pitch_mask])

        # Update spectrogram
        spectrogram.set_array(np.array(fft_history).T)
        spectrogram.set_extent([start / framerate - 10, start / framerate, 48, 96])

        # Find and display dominant notes
        dominant_notes = find_dominant_notes(freqs, magnitudes, piano_freqs)
        dominant_notes_text.set_text(f"Dominant Notes: {', '.join(dominant_notes)}")

        # Update piano keyboard visualization
        for i, key in enumerate(keys):
            pitch = i + 21  # Start from A0 (MIDI note 21)
            if pitch <= 108:  # Up to C8 (MIDI note 108)
                freq = 440 * (
                    2 ** ((pitch - 69) / 12)
                )  # Calculate frequency for the pitch
                intensity = normalized_magnitudes[np.argmin(np.abs(freqs - freq))]
                if isinstance(key, Rectangle) and key.get_height() < 1:  # Black key
                    key.set_facecolor((intensity, 0, 0))
                else:  # White key
                    key.set_facecolor((1, 1 - intensity, 1 - intensity))
        return line, spectrogram, dominant_notes_text, *keys

    ani = FuncAnimation(fig, update_plot, interval=100, blit=True)

    print(
        "Playing audio and plotting waveform, piano roll spectrogram, and piano visualization. Close the plot window to stop."
    )
    plt.tight_layout()
    plt.show()

    player.stop()
    play_thread.join()

    print("Playback and plotting finished.")


if __name__ == "__main__":
    input_file = "ThatchedVillagers.wav"
    mono_play_and_plot(input_file)
