# Noise Generator

A software-based noise generator built in Python. Supports white, pink, brown, blue, and violet noise with real-time playback and file export.

<img src="images/screenshot.png" width="400"/>

## Requirements

- Python 3.9+
- Homebrew (Mac)

## Installation

Clone the repository:
```bash
git clone git@github.com:ryguydev/noise-generator.git
cd noise-generator
```

Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
brew install portaudio
```

## Usage

Launch the GUI:
```bash
python -m noise_generator.gui
```

Launch from the CLI:
```bash
python -m noise_generator.cli --type pink --duration 30
```

Loop noise until Ctrl+C:
```bash
python -m noise_generator.cli --type brown --loop
```

Export to WAV:
```bash
python -m noise_generator.cli --type white --duration 60 --export my_noise.wav
```

## MP3 Export
MP3 export currently command line only

MP3 export requires two additional dependencies:
```bash
pip install pydub
brew install ffmpeg
```

Then export as MP3:
```bash
python -m noise_generator.cli --type pink --duration 60 --export my_noise.mp3 --format mp3
```

## Noise Types
- white — equal energy at all frequencies
- pink — gentle low frequency emphasis (-3dB per octave)
- brown — steep low frequency emphasis (-6dB per octave)
- blue — gentle high frequency emphasis (+3 dB per octave)
- violet — steep high frequency emphasis (+6 dB per octave)