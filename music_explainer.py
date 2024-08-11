from PySide6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QLabel,
    QSlider,
    QScrollBar,
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
        self.setup_audio_handler()

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

        # Add horizontal scroll bar
        self.h_scroll = QScrollBar(Qt.Horizontal)
        self.h_scroll.valueChanged.connect(self.waveform_widget.set_scroll)
        main_layout.addWidget(self.h_scroll)

        # Remove the zoom slider, as we now use keyboard shortcuts for zooming
        # Instead, add labels to display current zoom levels
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Horizontal Zoom:"))
        self.horizontal_zoom_label = QLabel("1.00x")
        zoom_layout.addWidget(self.horizontal_zoom_label)
        zoom_layout.addWidget(QLabel("Vertical Zoom:"))
        self.vertical_zoom_label = QLabel("1.00x")
        zoom_layout.addWidget(self.vertical_zoom_label)
        main_layout.addLayout(zoom_layout)

    def setup_audio_handler(self):
        self.audio_handler = AudioHandler()
        self.audio_handler.playback_position_changed.connect(self.update_playhead)
        self.waveform_widget.playhead_changed.connect(self.seek_audio)
        self.waveform_widget.zoom_changed.connect(self.update_zoom_labels)

    def update_zoom_labels(self, h_zoom, v_zoom):
        self.horizontal_zoom_label.setText(f"{h_zoom:.2f}x")
        self.vertical_zoom_label.setText(f"{v_zoom:.2f}x")
        self.h_scroll.setRange(0, self.waveform_widget.get_max_scroll())

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Audio File", "", "Audio Files (*.wav)"
        )
        if file_name:
            self.audio_handler.load_file(file_name)
            self.waveform_widget.set_waveform(self.audio_handler.waveform)
            self.update_ui_for_new_file()

    def update_ui_for_new_file(self):
        self.time_slider.setEnabled(True)
        self.time_slider.setRange(0, len(self.audio_handler.waveform))
        self.h_scroll.setRange(0, self.waveform_widget.get_max_scroll())
        self.update_zoom()

    def update_zoom(self):
        zoom_factor = self.zoom_slider.value() / 100
        self.waveform_widget.set_zoom(zoom_factor)
        self.h_scroll.setRange(0, self.waveform_widget.get_max_scroll())

    def update_playhead(self, position):
        self.waveform_widget.set_playhead(position)
        self.time_slider.setValue(position)

    def seek_audio(self, position):
        self.audio_handler.seek(position)
        self.time_slider.setValue(position)

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
