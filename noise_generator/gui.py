import os
import sys
import threading
import sounddevice as sd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QComboBox, QSlider, QCheckBox,
    QPushButton, QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFont, QIcon
from noise_generator.generators import NOISE_TYPES, normalize
from noise_generator.player import play_noise, play_noise_loop
from noise_generator.exporter import EXPORT_FORMATS


class Signals(QObject):
    status_changed = pyqtSignal(str, str)
    playback_finished = pyqtSignal()
    timer_start = pyqtSignal(int)


class NoiseGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Noise Generator")
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.png')
        self.setWindowIcon(QIcon(icon_path))
        self.setFixedSize(400, 700)

        self.is_playing = False
        self.play_thread = None
        self.signals = Signals()
        self.signals.status_changed.connect(self._update_status)
        self.signals.playback_finished.connect(self._on_playback_finished)
        self.signals.timer_start.connect(self._start_timer)

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

        # Duration display / countdown
        self.duration_display = QLabel("0h 0m 10s")
        self.duration_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.duration_display.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(self.duration_display)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Hours slider
        self.hours_label = QLabel("Hours: 0")
        self.hours_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hours_label)

        self.hours_slider = QSlider(Qt.Orientation.Horizontal)
        self.hours_slider.setRange(0, 12)
        self.hours_slider.setValue(0)
        self.hours_slider.valueChanged.connect(self._update_duration_display)
        layout.addWidget(self.hours_slider)

        # Minutes slider
        self.minutes_label = QLabel("Minutes: 0")
        self.minutes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.minutes_label)

        self.minutes_slider = QSlider(Qt.Orientation.Horizontal)
        self.minutes_slider.setRange(0, 59)
        self.minutes_slider.setValue(0)
        self.minutes_slider.valueChanged.connect(self._update_duration_display)
        layout.addWidget(self.minutes_slider)

        # Seconds slider
        self.seconds_label = QLabel("Seconds: 10")
        self.seconds_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.seconds_label)

        self.seconds_slider = QSlider(Qt.Orientation.Horizontal)
        self.seconds_slider.setRange(0, 59)
        self.seconds_slider.setValue(10)
        self.seconds_slider.valueChanged.connect(self._update_duration_display)
        layout.addWidget(self.seconds_slider)

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
                background-color: #0d1b2a;
                color: #e8f0fe;
            }
            QLabel {
                color: #e8f0fe;
                font-size: 13px;
            }
            QComboBox {
                background-color: #0d1b2a;
                color: #b8d4f0;
                border: 1px solid #1e3a5f;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #122236;
                color: #b8d4f0;
                selection-background-color: #2d7dd2;
                border: 1px solid #1e3a5f;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #1e3a5f;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #2d7dd2;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #2d7dd2;
                border-radius: 2px;
            }
            QCheckBox {
                color: #4a7fa5;
                font-size: 13px;
            }
            QPushButton {
                background-color: #122236;
                color: #4a7fa5;
                border: 1px solid #1e3a5f;
                border-radius: 10px;
                font-size: 14px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #1e3a5f;
                color: #b8d4f0;
            }
            QPushButton:disabled {
                background-color: #0d1b2a;
                color: #1e3a5f;
                border: 1px solid #122236;
            }
            QProgressBar {
                background-color: #1e3a5f;
                border-radius: 2px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #2d7dd2;
                border-radius: 2px;
            }
            #play_button {
                background-color: #2d7dd2;
                color: #e8f0fe;
                border: none;
                font-size: 15px;
                font-weight: bold;
            }
            #play_button:hover {
                background-color: #2270c0;
            }
            #play_button:disabled {
                background-color: #1e3a5f;
                color: #4a7fa5;
            }
            #export_button {
                background-color: #122236;
                color: #4a7fa5;
                border: 1px solid #1e3a5f;
            }
            #export_button:hover {
                background-color: #1e3a5f;
                color: #b8d4f0;
            }
        """)
        self.export_button.setObjectName("export_button")
        self.play_button.setObjectName("play_button")

    def _update_duration_display(self):
        h = self.hours_slider.value()
        m = self.minutes_slider.value()
        s = self.seconds_slider.value()
        self.hours_label.setText(f"Hours: {h}")
        self.minutes_label.setText(f"Minutes: {m}")
        self.seconds_label.setText(f"Seconds: {s}")
        self.duration_display.setText(f"{h}h {m}m {s}s")
    
    def _start_timer(self, total_seconds):
        self._timer_total = total_seconds
        self._timer_remaining = total_seconds
        self.progress_bar.setValue(100)
        self.progress_bar.show()

        self._countdown_timer = QTimer()
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._tick)
        self._countdown_timer.start()

    def _tick(self):
        self._timer_remaining -= 1
        h = self._timer_remaining // 3600
        m = (self._timer_remaining % 3600) // 60
        s = self._timer_remaining % 60
        self.duration_display.setText(f"{h}h {m}m {s}s")

        progress = int((self._timer_remaining / self._timer_total) * 100)
        self.progress_bar.setValue(progress)

        if self._timer_remaining <= 0:
            self._countdown_timer.stop()
            self.progress_bar.hide()
            self._restore_duration_display()

    def _restore_duration_display(self):
        h = self.hours_slider.value()
        m = self.minutes_slider.value()
        s = self.seconds_slider.value()
        self.duration_display.setText(f"{h}h {m}m {s}s")

    def _generate(self):
        noise_type = self.noise_dropdown.currentText()
        h = self.hours_slider.value()
        m = self.minutes_slider.value()
        s = self.seconds_slider.value()
        duration = (h * 3600) + (m * 60) + s
        if duration == 0:
            duration = 10  # fallback to 10 seconds if all sliders are zero
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
                h = self.hours_slider.value()
                m = self.minutes_slider.value()
                s = self.seconds_slider.value()
                total_seconds = (h * 3600) + (m * 60) + s
                if total_seconds == 0:
                    total_seconds = 10
                self.signals.status_changed.emit("Playing...", "green")
                self.signals.timer_start.emit(total_seconds)
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
        if self.is_playing:
            stop()
            if hasattr(self, '_countdown_timer'):
                self._countdown_timer.stop()
            self._restore_duration_display()
            self.progress_bar.hide()
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