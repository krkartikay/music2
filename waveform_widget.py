from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import Qt, Signal, QPointF
import numpy as np


class WaveformWidget(QWidget):
    playhead_changed = Signal(int)
    zoom_changed = Signal(float, float)  # Emit horizontal and vertical zoom factors
    scroll_changed = Signal(int)  # Signal to inform when scrolling occurs

    def __init__(self, parent=None):
        super().__init__(parent)
        self.waveform = None
        self.horizontal_zoom_factor = 1
        self.vertical_zoom_factor = 1
        self.scroll_position = 0
        self.playhead_position = 0
        self.setMouseTracking(True)

    def set_waveform(self, waveform):
        self.waveform = waveform
        self.update()

    def set_horizontal_zoom(self, factor):
        self.horizontal_zoom_factor = max(1, factor)
        self.zoom_changed.emit(self.horizontal_zoom_factor, self.vertical_zoom_factor)
        self.update()

    def set_vertical_zoom(self, factor):
        self.vertical_zoom_factor = max(1, factor)
        self.zoom_changed.emit(self.horizontal_zoom_factor, self.vertical_zoom_factor)
        self.update()

    def set_scroll(self, position):
        self.scroll_position = max(0, min(position, self.get_max_scroll()))
        self.update()

    def set_playhead(self, position):
        self.playhead_position = max(
            0, min(position, len(self.waveform) - 1 if self.waveform is not None else 0)
        )
        self.ensure_playhead_visible()
        self.update()

    def ensure_playhead_visible(self):
        if self.waveform is None:
            return

        samples_per_pixel = max(
            1, int(len(self.waveform) / (self.width() * self.horizontal_zoom_factor))
        )
        playhead_pixel = self.playhead_position // samples_per_pixel

        # Check if playhead is outside the visible area
        if (
            playhead_pixel < self.scroll_position
            or playhead_pixel >= self.scroll_position + self.width()
        ):
            # Center the playhead in the view
            new_scroll = max(
                0, min(playhead_pixel - self.width() // 2, self.get_max_scroll())
            )
            self.set_scroll(new_scroll)
            self.scroll_changed.emit(new_scroll)

    def set_scroll(self, position):
        self.scroll_position = max(0, min(position, self.get_max_scroll()))
        self.update()

    def get_max_scroll(self):
        if self.waveform is None:
            return 0
        return max(
            0, int(len(self.waveform) * self.horizontal_zoom_factor - self.width())
        )

    def paintEvent(self, event):
        if self.waveform is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        mid_height = height // 2

        painter.fillRect(self.rect(), Qt.white)

        # Draw waveform
        pen = QPen(Qt.blue)
        pen.setWidth(1)
        painter.setPen(pen)

        samples_per_pixel = max(
            1, int(len(self.waveform) / (width * self.horizontal_zoom_factor))
        )
        start_sample = int(self.scroll_position / self.horizontal_zoom_factor)
        end_sample = min(len(self.waveform), start_sample + width * samples_per_pixel)

        for x in range(width):
            sample_start = start_sample + x * samples_per_pixel
            sample_end = min(sample_start + samples_per_pixel, end_sample)
            if sample_start >= sample_end:
                break
            chunk = self.waveform[sample_start:sample_end]
            if len(chunk) > 0:
                y = int(
                    np.mean(chunk) * mid_height * self.vertical_zoom_factor + mid_height
                )
                painter.drawLine(x, mid_height, x, y)

        # Draw playhead
        if start_sample <= self.playhead_position < end_sample:
            playhead_x = int(
                (self.playhead_position - start_sample) / samples_per_pixel
            )
            painter.setPen(QPen(Qt.red, 2))
            painter.drawLine(playhead_x, 0, playhead_x, height)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.waveform is not None:
            samples_per_pixel = max(
                1,
                int(len(self.waveform) / (self.width() * self.horizontal_zoom_factor)),
            )
            start_sample = int(self.scroll_position / self.horizontal_zoom_factor)
            clicked_sample = start_sample + event.x() * samples_per_pixel
            self.set_playhead(clicked_sample)
            self.playhead_changed.emit(self.playhead_position)

    def wheelEvent(self, event):
        modifiers = event.modifiers()
        if (
            modifiers & Qt.ControlModifier
        ):  # Command key on macOS, Windows key on Windows
            # Horizontal zoom
            zoom_change = event.angleDelta().y() / 120
            new_zoom = max(1, self.horizontal_zoom_factor * (1.1**zoom_change))
            self.set_horizontal_zoom(new_zoom)
        elif modifiers & Qt.AltModifier:  # Option key on macOS, Alt key on Windows
            # Vertical zoom
            zoom_change = event.angleDelta().y() / 120
            new_zoom = max(1, self.vertical_zoom_factor * (1.1**zoom_change))
            self.set_vertical_zoom(new_zoom)
        else:
            # Scroll
            self.set_scroll(self.scroll_position - event.angleDelta().y())
