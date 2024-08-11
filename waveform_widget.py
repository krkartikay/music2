from PySide6.QtWidgets import QWidget, QScrollBar
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import Qt, Signal, QPointF
import numpy as np


class WaveformWidget(QWidget):
    playhead_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.waveform = None
        self.zoom_factor = 1
        self.scroll_position = 0
        self.playhead_position = 0
        self.setMouseTracking(True)

    def set_waveform(self, waveform):
        self.waveform = waveform
        self.update()

    def set_zoom(self, factor):
        self.zoom_factor = max(1, factor)
        self.update()

    def set_scroll(self, position):
        self.scroll_position = max(0, min(position, self.get_max_scroll()))
        self.update()

    def set_playhead(self, position):
        self.playhead_position = max(
            0, min(position, len(self.waveform) - 1 if self.waveform is not None else 0)
        )
        self.update()

    def get_max_scroll(self):
        if self.waveform is None:
            return 0
        return max(0, int(len(self.waveform) * self.zoom_factor - self.width()))

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

        samples_per_pixel = max(1, int(len(self.waveform) / (width * self.zoom_factor)))
        start_sample = int(self.scroll_position / self.zoom_factor)
        end_sample = min(len(self.waveform), start_sample + width * samples_per_pixel)

        for x in range(width):
            sample_start = start_sample + x * samples_per_pixel
            sample_end = min(sample_start + samples_per_pixel, end_sample)
            if sample_start >= sample_end:
                break
            chunk = self.waveform[sample_start:sample_end]
            if len(chunk) > 0:
                y = int(np.mean(chunk) * mid_height + mid_height)
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
                1, int(len(self.waveform) / (self.width() * self.zoom_factor))
            )
            start_sample = int(self.scroll_position / self.zoom_factor)
            clicked_sample = start_sample + event.x() * samples_per_pixel
            self.set_playhead(clicked_sample)
            self.playhead_changed.emit(self.playhead_position)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            # Zoom
            zoom_change = event.angleDelta().y() / 120
            new_zoom = max(1, self.zoom_factor + zoom_change)
            self.set_zoom(new_zoom)
        else:
            # Scroll
            self.set_scroll(self.scroll_position - event.angleDelta().y())
