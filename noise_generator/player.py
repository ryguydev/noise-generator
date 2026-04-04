import numpy as np
import sounddevice as sd


def play_noise(signal: np.ndarray, sample_rate: int = 44100, volume: float = 0.8) -> None:
    """Play a noise signal through the speakers in real time."""
    # Scale by volume and ensure float32 format for sounddevice
    audio = (signal * volume).astype(np.float32)

    print("Playing... press Ctrl+C to stop.")
    try:
        sd.play(audio, samplerate=sample_rate)
        sd.wait()  # Wait until playback is finished
    except KeyboardInterrupt:
        sd.stop()
        print("\nPlayback stopped.")


def play_noise_loop(signal: np.ndarray, sample_rate: int = 44100, volume: float = 0.8) -> None:
    """Play a noise signal on a continuous loop until Ctrl+C is pressed."""
    audio = (signal * volume).astype(np.float32)

    print("Looping... press Ctrl+C to stop.")
    try:
        while True:
            sd.play(audio, samplerate=sample_rate)
            sd.wait()
    except KeyboardInterrupt:
        sd.stop()
        print("\nPlayback stopped.")