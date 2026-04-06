import os
import sys
import threading
import sounddevice as sd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
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
        self.setFixedSize(400, 720)

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
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Title
        title = QLabel("Noise Generator")
        title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #e8f0fe; font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("sleep · focus · relax")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #4a7fa5; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(subtitle)

        # Noise type card
        noise_card = QWidget()
        noise_card.setStyleSheet("background-color: #122236; border-radius: 10px;")
        noise_layout = QVBoxLayout(noise_card)
        noise_layout.setContentsMargins(18, 14, 18, 14)
        noise_layout.setSpacing(8)

        noise_section_label = QLabel("NOISE TYPE")
        noise_section_label.setStyleSheet("color: #4a7fa5; font-size: 11px; letter-spacing: 1px;")
        noise_layout.addWidget(noise_section_label)

        self.noise_dropdown = QComboBox()
        self.noise_dropdown.addItems([k.capitalize() for k in NOISE_TYPES.keys()])
        noise_layout.addWidget(self.noise_dropdown)
        layout.addWidget(noise_card)

        # Volume card
        volume_card = QWidget()
        volume_card.setStyleSheet("background-color: #122236; border-radius: 10px;")
        volume_layout = QVBoxLayout(volume_card)
        volume_layout.setContentsMargins(18, 14, 18, 14)
        volume_layout.setSpacing(8)

        volume_header = QWidget()
        volume_header_layout = QHBoxLayout(volume_header)
        volume_header_layout.setContentsMargins(0, 0, 0, 0)

        volume_section_label = QLabel("VOLUME")
        volume_section_label.setStyleSheet("color: #4a7fa5; font-size: 11px; letter-spacing: 1px;")
        volume_header_layout.addWidget(volume_section_label)

        self.volume_label = QLabel("80%")
        self.volume_label.setStyleSheet("color: #b8d4f0; font-size: 13px;")
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        volume_header_layout.addWidget(self.volume_label)
        volume_layout.addWidget(volume_header)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(
            lambda v: self.volume_label.setText(f"{v}%")
        )
        volume_layout.addWidget(self.volume_slider)
        layout.addWidget(volume_card)

        # Duration card
        duration_card = QWidget()
        duration_card.setStyleSheet("background-color: #122236; border-radius: 10px;")
        duration_layout = QVBoxLayout(duration_card)
        duration_layout.setContentsMargins(18, 14, 18, 14)
        duration_layout.setSpacing(8)

        duration_section_label = QLabel("DURATION")
        duration_section_label.setStyleSheet("color: #4a7fa5; font-size: 11px; letter-spacing: 1px;")
        duration_layout.addWidget(duration_section_label)

        self.duration_display = QLabel("0h 0m 10s")
        self.duration_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.duration_display.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.duration_display.setStyleSheet("color: #e8f0fe; font-size: 24px; margin: 4px 0;")
        duration_layout.addWidget(self.duration_display)

        # Progress bar inside duration card
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.hide()
        duration_layout.addWidget(self.progress_bar)

        # Hours slider
        hours_header = QWidget()
        hours_header_layout = QHBoxLayout(hours_header)
        hours_header_layout.setContentsMargins(0, 0, 0, 0)
        hours_section_label = QLabel("Hours")
        hours_section_label.setStyleSheet("color: #4a7fa5; font-size: 12px;")
        hours_header_layout.addWidget(hours_section_label)
        self.hours_label = QLabel("0")
        self.hours_label.setStyleSheet("color: #b8d4f0; font-size: 12px;")
        self.hours_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        hours_header_layout.addWidget(self.hours_label)
        duration_layout.addWidget(hours_header)

        self.hours_slider = QSlider(Qt.Orientation.Horizontal)
        self.hours_slider.setRange(0, 12)
        self.hours_slider.setValue(0)
        self.hours_slider.valueChanged.connect(self._update_duration_display)
        duration_layout.addWidget(self.hours_slider)

        # Minutes slider
        minutes_header = QWidget()
        minutes_header_layout = QHBoxLayout(minutes_header)
        minutes_header_layout.setContentsMargins(0, 0, 0, 0)
        minutes_section_label = QLabel("Minutes")
        minutes_section_label.setStyleSheet("color: #4a7fa5; font-size: 12px;")
        minutes_header_layout.addWidget(minutes_section_label)
        self.minutes_label = QLabel("0")
        self.minutes_label.setStyleSheet("color: #b8d4f0; font-size: 12px;")
        self.minutes_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        minutes_header_layout.addWidget(self.minutes_label)
        duration_layout.addWidget(minutes_header)

        self.minutes_slider = QSlider(Qt.Orientation.Horizontal)
        self.minutes_slider.setRange(0, 59)
        self.minutes_slider.setValue(0)
        self.minutes_slider.valueChanged.connect(self._update_duration_display)
        duration_layout.addWidget(self.minutes_slider)

        # Seconds slider
        seconds_header = QWidget()
        seconds_header_layout = QHBoxLayout(seconds_header)
        seconds_header_layout.setContentsMargins(0, 0, 0, 0)
        seconds_section_label = QLabel("Seconds")
        seconds_section_label.setStyleSheet("color: #4a7fa5; font-size: 12px;")
        seconds_header_layout.addWidget(seconds_section_label)
        self.seconds_label = QLabel("10")
        self.seconds_label.setStyleSheet("color: #b8d4f0; font-size: 12px;")
        self.seconds_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        seconds_header_layout.addWidget(self.seconds_label)
        duration_layout.addWidget(seconds_header)

        self.seconds_slider = QSlider(Qt.Orientation.Horizontal)
        self.seconds_slider.setRange(0, 59)
        self.seconds_slider.setValue(10)
        self.seconds_slider.valueChanged.connect(self._update_duration_display)
        duration_layout.addWidget(self.seconds_slider)

        layout.addWidget(duration_card)

        # Loop checkbox
        self.loop_checkbox = QCheckBox("Loop")
        self.loop_checkbox.setStyleSheet("color: #4a7fa5; font-size: 13px; margin-left: 4px;")
        layout.addWidget(self.loop_checkbox)

        # Play and Stop buttons side by side
        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)

        self.play_button = QPushButton("Play")
        self.play_button.setFixedHeight(46)
        self.play_button.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        self.play_button.clicked.connect(self._play)
        button_layout.addWidget(self.play_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setFixedHeight(46)
        self.stop_button.setFont(QFont("Arial", 15))
        self.stop_button.clicked.connect(self._stop)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        layout.addWidget(button_row)

        # Export button
        self.export_button = QPushButton("Export WAV")
        self.export_button.setFixedHeight(42)
        self.export_button.setFont(QFont("Arial", 13))
        self.export_button.clicked.connect(self._export)
        layout.addWidget(self.export_button)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #2d5a7a; font-size: 12px;")
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
        noise_type = self.noise_dropdown.currentText().lower()
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