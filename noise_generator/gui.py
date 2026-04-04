import sys
import threading
import sounddevice as sd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QComboBox, QSlider, QCheckBox,
    QPushButton, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont
from noise_generator.generators import NOISE_TYPES, normalize
from noise_generator.player import play_noise, play_noise_loop
from noise_generator.exporter import EXPORT_FORMATS


class Signals(QObject):
    status_changed = pyqtSignal(str, str)
    playback_finished = pyqtSignal()


class NoiseGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Noise Generator")
        self.setFixedSize(400, 520)

        self.is_playing = False
        self.play_thread = None
        self.signals = Signals()
        self.signals.status_changed.connect(self._update_status)
        self.signals.playback_finished.connect(self._on_playback_finished)

        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(12)

        # Title
        title = QLabel("Noise Generator")
        title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Noise type
        noise_label = QLabel("Noise Type")
        noise_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(noise_label)

        self.noise_dropdown = QComboBox()
        self.noise_dropdown.addItems(list(NOISE_TYPES.keys()))
        layout.addWidget(self.noise_dropdown)

        # Volume
        self.volume_label = QLabel("Volume: 80%")
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.volume_label)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(
            lambda v: self.volume_label.setText(f"Volume: {v}%")
        )
        layout.addWidget(self.volume_slider)

        # Duration
        self.duration_label = QLabel("Duration: 10s")
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.duration_label)

        self.duration_slider = QSlider(Qt.Orientation.Horizontal)
        self.duration_slider.setRange(1, 60)
        self.duration_slider.setValue(10)
        self.duration_slider.valueChanged.connect(
            lambda v: self.duration_label.setText(f"Duration: {v}s")
        )
        layout.addWidget(self.duration_slider)

        # Loop
        self.loop_checkbox = QCheckBox("Loop")
        self.loop_checkbox.setStyleSheet("margin-left: 130px;")
        layout.addWidget(self.loop_checkbox)

        # Play button
        self.play_button = QPushButton("Play")
        self.play_button.setFixedHeight(44)
        self.play_button.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.play_button.clicked.connect(self._play)
        layout.addWidget(self.play_button)

        # Stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.setFixedHeight(44)
        self.stop_button.setFont(QFont("Arial", 14))
        self.stop_button.clicked.connect(self._stop)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        # Export button
        self.export_button = QPushButton("Export WAV")
        self.export_button.setFixedHeight(44)
        self.export_button.setFont(QFont("Arial", 14))
        self.export_button.clicked.connect(self._export)
        layout.addWidget(self.export_button)

        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
            QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 6px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #ffffff;
                selection-background-color: #3a7ebf;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #444;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #3a7ebf;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #3a7ebf;
                border-radius: 3px;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3a7ebf;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2d6da8;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
            #export_button {
                background-color: #2d6a4f;
            }
            #export_button:hover {
                background-color: #1b4332;
            }
        """)
        self.export_button.setObjectName("export_button")

    def _generate(self):
        noise_type = self.noise_dropdown.currentText()
        duration = self.duration_slider.value()
        volume = self.volume_slider.value() / 100
        generator = NOISE_TYPES[noise_type]
        signal = generator(duration)
        return normalize(signal, volume)

    def _play(self):
        if self.is_playing:
            return

        self.is_playing = True
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.signals.status_changed.emit("Generating...", "orange")

        def run():
            try:
                signal = self._generate()
                self.signals.status_changed.emit("Playing...", "green")
                if self.loop_checkbox.isChecked():
                    play_noise_loop(signal, volume=1.0)
                else:
                    play_noise(signal, volume=1.0)
            except Exception as e:
                self.signals.status_changed.emit(f"Error: {e}", "red")
            finally:
                self.signals.playback_finished.emit()

        self.play_thread = threading.Thread(target=run, daemon=True)
        self.play_thread.start()

    def _stop(self):
        from noise_generator.player import stop
        stop()
        self.is_playing = False
        self.play_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Stopped")
        self.status_label.setStyleSheet("color: gray;")

    def _update_status(self, text, color):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")

    def _on_playback_finished(self):
        self.is_playing = False
        self.play_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("color: gray;")
    
    def _export(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Noise",
            "noise.wav",
            "WAV files (*.wav);;MP3 files (*.mp3)"
        )
        if not filename:
            return

        self.signals.status_changed.emit("Exporting...", "orange")
        try:
            signal = self._generate()
            ext = filename.split(".")[-1].lower()
            exporter = EXPORT_FORMATS.get(ext, EXPORT_FORMATS["wav"])
            exporter(signal, filename)
            self.signals.status_changed.emit("Exported!", "green")
        except Exception as e:
            self.signals.status_changed.emit(f"Error: {e}", "red")

    
    def closeEvent(self, event):
        sd.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = NoiseGeneratorApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()