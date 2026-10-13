# FretTrain 🎸

> **Real-Time Guitar & Bass Fretboard Trainer powered by Python, Flet, and Aubio DSP**

**FretTrain** is a desktop application designed to accelerate fretboard note memorization for guitarists, bassists, and ukulele players. By combining low-latency digital signal processing (DSP) pitch detection with configurable practice timers and instrument presets, FretTrain listens to your physical instrument via your microphone and automatically verifies notes as you play.

---

## ✨ Key Features

- **🎙️ Real-Time Pitch Detection**: Uses `aubio` (YIN algorithm) and `sounddevice` to analyze audio input in real-time, displaying detected notes, octaves, frequency in Hz, and pitch deviation in cents.
- **🎯 Interactive Note Prompting**: Clean, animated circular note target that provides instant visual feedback—turning amber when listening and green when a target note is matched in tune.
- **🎸 Comprehensive Instrument Presets**: Pre-configured tunings for:
- 6-String, 7-String, and 8-String Standard Guitars
- 4-String and 5-String Standard Basses
- Regular, 5-String, and Baritone Ukuleles
- Fully customizable custom string counts (1 to 8 strings) and per-string tunings.

- **🎛️ Custom Rotary Guitar Knobs**: Tactile step controls for tweaking string counts and practice interval duration on the fly.
- **⏱️ Non-Blocking Async Timer Engine**: Custom `TrainerTimer` supporting Auto-Advance flashcard mode with visual progress meters.
- **🔊 Intelligent Audio Device Pipeline**: Automatically filters out virtual audio cables, system mappers, and secondary host API duplicates to present a clean list of physical microphones (with "System Default Microphone" support).
- **🎨 Modern Responsive UI & Themes**: Built with Flet using dark/light theme switching, custom assets integration, and responsive column layouts.

---

## 🏗️ Project Architecture

```text
FretTrain/
├── assets/
│   └── bg.png                      # App background asset
├── src/
│   ├── audio/
│   │   ├── pitch_detector.py       # Sounddevice & Aubio DSP worker thread
│   │   └── audio_worker.py        # Thread-safe pitch match debouncer engine
│   ├── components/
│   │   ├── guitar_knob.py         # Custom rotary/step knob control
│   │   ├── header.py              # Application top bar with theme toggle
│   │   └── note_display.py        # Interactive target note circle
│   ├── utils/
│   │   ├── music_theory.py        # Tunings, presets, and octave calculations
│   │   ├── theme_manager.py       # Global theme state listener
│   │   └── timer_manager.py       # High-frequency async practice timers
│   └── views/
│       └── trainer_view.py        # Main view integrating UI, audio, and state
├── main.py                         # Application entry point
├── requirements.txt                # Python dependencies
└── README.md

```

---

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.10 or higher
- **PortAudio**: Standard audio backend library (installed automatically via `sounddevice` on most platforms).

### Installation

1. **Clone the repository**:

```bash
git clone https://github.com/your-username/FretTrain.git
cd FretTrain

```

2. **Create and activate a virtual environment**:

- **Windows**:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1

```

- **macOS / Linux**:

```bash
python3 -m venv venv
source venv/bin/activate

```

3. **Install dependencies**:

```bash
pip install -r requirements.txt

```

### Running the Application

Launch the trainer by running `main.py` from the project root:

```bash
python main.py

```

---

## 🛠️ Usage Guide

1. **Select Microphone**: Choose your input microphone from the dropdown list in the **Instrument & Mic Setup** panel.
2. **Choose Instrument**: Pick a preset (e.g., _Guitar 6-String Standard_ or _Bass 4-String_) or construct a custom setup using the **Strings** knob.
3. **Set Practice Mode**:

- **Manual Mode**: Click **Next Note** or play the note on your guitar to advance automatically upon a correct match.
- **Auto-Advance Mode**: Toggle the **Auto-Advance Mode** switch to enable countdown intervals configured by the **Timer** knob.

4. **Play!**: Pluck the target note on your instrument. The central circle will provide live feedback showing your detected note, cents deviation, and turn green once the note is held in tune.

---

## 📣 Feedback & Community Testing

FretTrain is currently under active development, and user input is crucial to refining its performance!

We are specifically seeking feedback on:

- **Audio Performance & Latency**: How responsive is the pitch detection on your microphone setup?
- **Low-Frequency Accuracy**: How accurately does pitch detection perform on low-E (E2) guitar strings or 4/5-string bass notes (E1/B0)?
- **UI & Workflow**: Are the controls intuitive? What additional practice modes or pitch options (e.g., specific fret ranges, chord recognition) would you like to see?

If you encounter any bugs, pitch detection anomalies, or performance bottlenecks, please **Open an Issue** or submit a **Pull Request** with your audio interface details and OS specifications.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---
