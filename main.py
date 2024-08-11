import sys
from PySide6.QtWidgets import QApplication
from music_explainer import MusicExplainer

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MusicExplainer()
    window.show()
    sys.exit(app.exec())
