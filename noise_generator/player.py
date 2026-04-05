import numpy as np
import sounddevice as sd

# Global stop flag
_stop_flag = False


def stop():
    """Signal all playback to stop."""
    global _stop_flag
    _stop_flag = True
    sd.stop()


def play_noise(signal: np.ndarray, sample_rate: int = 44100, volume: float = 0.8) -> None:
    """Play a noise signal through the speakers in real time."""
    global _stop_flag
    _stop_flag = False

    signal = apply_fade_out(signal)
    audio = (signal * volume).astype(np.float32)

    print("Playing... press Ctrl+C to stop.")
    try:
        sd.play(audio, samplerate=sample_rate)
        sd.wait()
    except KeyboardInterrupt:
        sd.stop()
        print("\nPlayback stopped.")


def play_noise_loop(signal: np.ndarray, sample_rate: int = 44100, volume: float = 0.8) -> None:
    """Play a noise signal on a continuous loop until stopped."""
    global _stop_flag
    _stop_flag = False

    audio = (signal * volume).astype(np.float32)

    # Tile the signal 10 times to create a long buffer with no gaps
    looped = np.tile(audio, 10)

    print("Looping... press Ctrl+C to stop.")
    try:
        while not _stop_flag:
            sd.play(looped, samplerate=sample_rate)
            sd.wait()
            if _stop_flag:
                break
    except KeyboardInterrupt:
        pass
    finally:
        sd.stop()
        print("\nPlayback stopped.")

def apply_fade_out(signal: np.ndarray, fade_seconds: float = 1.0, sample_rate: int = 44100) -> np.ndarray:
    """Apply an exponential fade out to the end of a signal."""
    fade_samples = int(fade_seconds * sample_rate)
    # Exponential curve from 1.0 to 0.0
    fade = np.logspace(0, -3, fade_samples)
    fade = fade / fade[0]  # normalize so it starts exactly at 1.0
    signal = signal.copy()
    signal[-fade_samples:] *= fade
    return signal