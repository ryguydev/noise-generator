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
- pink — 1/f spectrum, warm and natural
- brown — deep and rumbly
- blue — bright, high frequency emphasis
- violet — very bright, steepest high frequency emphasis