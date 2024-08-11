from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen
from PySide6.QtCore import Qt
import numpy as np


class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.waveform = None

    def set_waveform(self, waveform):
        self.waveform = waveform
        self.update()

    def paintEvent(self, event):
        if self.waveform is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        mid_height = height // 2

        painter.fillRect(self.rect(), Qt.white)

        pen = QPen(Qt.blue)
        pen.setWidth(1)
        painter.setPen(pen)

        chunk_size = len(self.waveform) // width
        for x in range(width):
            chunk = self.waveform[x * chunk_size : (x + 1) * chunk_size]
            y = int(np.mean(chunk) * mid_height + mid_height)
            painter.drawLine(x, mid_height, x, y)
