# Noise Generator

A software-based noise generator built in Python. Supports white, pink, brown, blue, and violet noise with real-time playback and file export.

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
brew install portaudio
```

## Usage

Play white noise for 10 seconds:
```bash
python -m noise_generator.cli --type white
```

Loop pink noise until Ctrl+C:
```bash
python -m noise_generator.cli --type pink --loop
```

Export brown noise to a WAV file:
```bash
python -m noise_generator.cli --type brown --duration 60 --export my_noise.wav
```

## Noise Types
- white — equal energy at all frequencies
- pink — gentle low frequency emphasis (-3dB per octave)
- brown — steep low frequency emphasis (-6dB per octave)
- blue — gentle high frequency emphasis (+3 dB per octave)
- violet — steep high frequency emphasis (+6 dB per octave)

## MP3 Export

MP3 export requires two additional dependencies:
```bash
pip install pydub
brew install ffmpeg
```

Then export as MP3:
```bash
python -m noise_generator.cli --type pink --duration 60 --export my_noise.mp3 --format mp3
```

## Notes
- As of right now, brown noise is much quieter than the others. Some normalization has been tried but not perfected, for now expect a quieter signal from brown noise.