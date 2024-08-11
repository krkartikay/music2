from PySide6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QLabel,
    QSlider,
)
from PySide6.QtCore import Qt
from waveform_widget import WaveformWidget
from audio_handler import AudioHandler


class MusicExplainer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Explainer")
        self.setGeometry(100, 100, 800, 600)

        self.audio_handler = AudioHandler()
        self.setup_ui()

    def setup_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        self.waveform_widget = WaveformWidget()
        main_layout.addWidget(self.waveform_widget, 3)

        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)

        analysis_panel = self.create_analysis_panel()
        main_layout.addWidget(analysis_panel)

        self.setCentralWidget(main_widget)

    def create_control_panel(self):
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_audio)
        control_layout.addWidget(self.play_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_audio)
        control_layout.addWidget(self.stop_button)

        self.open_button = QPushButton("Open File")
        self.open_button.clicked.connect(self.open_file)
        control_layout.addWidget(self.open_button)

        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setEnabled(False)
        control_layout.addWidget(self.time_slider)

        return control_panel

    def create_analysis_panel(self):
        analysis_panel = QWidget()
        analysis_layout = QVBoxLayout(analysis_panel)

        self.bpm_label = QLabel("BPM: ")
        analysis_layout.addWidget(self.bpm_label)

        self.key_label = QLabel("Key: ")
        analysis_layout.addWidget(self.key_label)

        return analysis_panel

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Audio File", "", "Audio Files (*.wav)"
        )
        if file_name:
            self.audio_handler.load_file(file_name)
            self.waveform_widget.set_waveform(self.audio_handler.waveform)
            self.time_slider.setEnabled(True)
            self.time_slider.setRange(0, len(self.audio_handler.waveform))

    def play_audio(self):
        self.audio_handler.play()

    def stop_audio(self):
        self.audio_handler.stop()
