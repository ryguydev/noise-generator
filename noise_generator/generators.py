import numpy as np
from scipy.signal import lfilter


def generate_white_noise(duration: float, sample_rate: int = 44100) -> np.ndarray:
    """Generate white noise - equal energy at all frequencies."""
    samples = int(duration * sample_rate)
    return np.random.randn(samples)


def generate_pink_noise(duration: float, sample_rate: int = 44100) -> np.ndarray:
    """Generate pink noise - 1/f spectrum, equal energy per octave."""
    samples = int(duration * sample_rate)
    white = np.random.randn(samples)

    # Voss-McCartney filter coefficients for 1/f response
    b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
    a = [1, -2.494956002, 2.017265875, -0.522189400]

    return lfilter(b, a, white)


def generate_brown_noise(duration: float, sample_rate: int = 44100) -> np.ndarray:
    """Generate brown noise - 1/f^2 spectrum, deep rumble."""
    samples = int(duration * sample_rate)
    white = np.random.randn(samples)
    brown = np.cumsum(white)

    # Remove DC offset first, then normalize
    brown = brown - np.mean(brown)
    brown = brown / np.max(np.abs(brown))

    # Fade in and out over 50ms to prevent popping
    fade_samples = int(sample_rate * 0.05)
    fade = np.linspace(0, 1, fade_samples)
    brown[:fade_samples] *= fade
    brown[-fade_samples:] *= fade[::-1]

    return brown


def generate_blue_noise(duration: float, sample_rate: int = 44100) -> np.ndarray:
    """Generate blue noise - high frequency emphasis."""
    samples = int(duration * sample_rate)
    white = np.random.randn(samples)

    # Differentiate white noise to boost high frequencies
    blue = np.diff(white, prepend=white[0])
    blue = blue / np.max(np.abs(blue))
    return blue


def generate_violet_noise(duration: float, sample_rate: int = 44100) -> np.ndarray:
    """Generate violet noise - steepest high frequency emphasis."""
    samples = int(duration * sample_rate)
    white = np.random.randn(samples)

    violet = np.diff(np.diff(white, prepend=white[0]), prepend=white[0])
    violet = violet / np.max(np.abs(violet))
    return violet


def normalize(signal: np.ndarray, volume: float = 0.8) -> np.ndarray:
    """Normalize a signal to a target volume level (0.0 to 1.0)."""
    max_val = np.max(np.abs(signal))
    if max_val == 0:
        return signal
    return (signal / max_val) * volume


NOISE_TYPES = {
    "white": generate_white_noise,
    "pink": generate_pink_noise,
    "brown": generate_brown_noise,
    "blue": generate_blue_noise,
    "violet": generate_violet_noise,
}