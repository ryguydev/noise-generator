import numpy as np
import soundfile as sf
from pathlib import Path


def export_wav(signal: np.ndarray, filename: str, sample_rate: int = 44100, volume: float = 0.8) -> None:
    """Export a noise signal to a WAV file."""
    # Scale by volume and ensure float32 format
    audio = (signal * volume).astype(np.float32)

    # Add .wav extension if not already there
    path = Path(filename)
    if path.suffix.lower() != ".wav":
        path = path.with_suffix(".wav")

    sf.write(str(path), audio, sample_rate)
    print(f"Saved to {path}")


def export_mp3(signal: np.ndarray, filename: str, sample_rate: int = 44100, volume: float = 0.8) -> None:
    """Export a noise signal to an MP3 file."""
    try:
        import pydub
    except ImportError:
        print("MP3 export requires pydub. Run: pip install pydub")
        print("You also need ffmpeg: brew install ffmpeg")
        return

    # First write to a temporary WAV, then convert
    import tempfile
    import os

    audio = (signal * volume).astype(np.float32)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    sf.write(tmp_path, audio, sample_rate)

    path = Path(filename)
    if path.suffix.lower() != ".mp3":
        path = path.with_suffix(".mp3")

    sound = pydub.AudioSegment.from_wav(tmp_path)
    sound.export(str(path), format="mp3")
    os.unlink(tmp_path)
    print(f"Saved to {path}")


EXPORT_FORMATS = {
    "wav": export_wav,
    "mp3": export_mp3,
}