# FretTrain 🎸

> **Real-Time Guitar, Bass & Ukulele Fretboard Trainer powered by Python, Flet, and Aubio DSP**

**FretTrain** is a high-performance desktop application designed to accelerate fretboard note memorization for guitarists, bassists, and ukulele players. By combining low-latency digital signal processing (DSP) pitch detection with configurable practice timers and instrument presets, FretTrain listens to your physical instrument in real-time and automatically verifies notes as you play.

---

## ✨ Key Features

* **🎙️ Real-Time Pitch Detection**: Uses `aubio` (YIN algorithm) and `sounddevice` to analyze live audio input, displaying detected notes, octaves, exact frequency (Hz), and pitch deviation in cents.
* **🎯 Interactive Target Circle**: Animated visual feedback target that turns amber while listening and flashes green when a target note is matched in tune.
* **🎸 Comprehensive Instrument Presets**: Built-in support for:
* 6-String, 7-String, and 8-String Standard Guitars
* 4-String and 5-String Standard Basses
* Standard, 5-String, and Baritone Ukuleles
* Fully customizable string counts (1–8 strings) and per-string tunings.


* **🎛️ Custom Rotary Guitar Knobs**: Tactile step controls for tweaking string counts and practice interval durations on the fly.
* **⏱️ Non-Blocking Async Timer Engine**: Powered by a custom `TrainerTimer` supporting Auto-Advance flashcard mode with visual progress meters.
* **🔊 Intelligent Audio Device Pipeline**: Automatically filters out virtual audio cables, system mappers, and secondary host API duplicates to present a clean list of physical microphones (with "System Default Microphone" support).
* **🎨 Modern Responsive UI & Themes**: Built with Flet featuring dark/light mode switching, custom asset integration, and fluid responsive layouts.

---

## 🏗️ Project Architecture

```text
FretTrain/
├── assets/
│   └── bg.png                  # App background asset
├── src/
│   ├── audio/
│   │   ├── pitch_detector.py   # Sounddevice & Aubio DSP worker thread
│   │   └── audio_worker.py     # Thread-safe pitch match debouncer engine
│   ├── components/
│   │   ├── guitar_knob.py      # Custom rotary/step knob control
│   │   ├── header.py          # Application top bar with theme toggle
│   │   └── note_display.py    # Interactive target note circle
│   ├── utils/
│   │   ├── music_theory.py    # Tunings, presets, and octave calculations
│   │   ├── theme_manager.py   # Global theme state listener
│   │   └── timer_manager.py   # High-frequency async practice timers
│   └── views/
│       └── trainer_view.py    # Main view integrating UI, audio, and state
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
└── README.md

```

---

Here is the updated section with macOS removed and Linux added to the pre-built installer options:

```markdown
## 🚀 Quick Start & Installation

Master the fretboard in minutes—no terminal wizardry required. Choose your path below:

---

### 🎛️ Option 1: Fast Track (Recommended for Players)

Grab the ready-to-run installer or binary for your OS and jump straight into training.

1. Go to the **[Latest Releases](../../releases)** page.
2. Download and run the file for your operating system:
   * **Windows:** Download and run `FretTrain-Setup.exe`
   * **Linux:** Download `FretTrain.AppImage`, make it executable (`chmod +x FretTrain.AppImage`), and run!
3. Launch `FretTrain` and start plugging in!

---

### 🛠️ Option 2: Developer Setup (Run from Source)

Want to tweak the DSP, contribute code, or build new features? Spin up the source in an isolated virtual environment:

#### Prerequisites
* **Python**: 3.10 or higher
* **PortAudio**: Audio backend library (installed automatically via `sounddevice` on Windows; install via package manager on Linux, e.g., `sudo apt install portaudio19-dev`).

```bash
# 1. Clone the repo & enter project directory
git clone [https://github.com/your-username/FretTrain.git](https://github.com/your-username/FretTrain.git)
cd FretTrain

# 2. Set up virtual environment
# Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux:
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies & launch
pip install -r requirements.txt
python main.py

```

---

### ⚡ Troubleshooting & Tips

* **Windows Execution Policy:** If PowerShell blocks script activation, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

```


* **Linux Permissions:** If using the AppImage, make sure execution permissions are granted:
```bash
chmod +x FretTrain.AppImage

```


* **Audio Drivers:** For lowest latency while training, ensure your primary audio interface driver (ASIO/WASAPI on Windows or ALSA/PulseAudio/PIPEWIRE on Linux) is selected in settings.


---

### ⚡ Troubleshooting & Tips

* **Windows Execution Policy:** If PowerShell blocks script activation, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

```


* **Audio Drivers:** For lowest latency while training, ensure your primary audio interface driver (ASIO on Windows) is selected in settings.

---

## 🛠️ Usage Guide

1. **Select Microphone**: Choose your input microphone from the dropdown list in the **Instrument & Mic Setup** panel.
2. **Choose Instrument**: Pick a preset (e.g., *Guitar 6-String Standard* or *Bass 4-String*) or construct a custom setup using the **Strings** knob.
3. **Set Practice Mode**:
* **Manual Mode**: Click **Next Note** or play the target note on your instrument to advance upon a correct match.
* **Auto-Advance Mode**: Toggle **Auto-Advance Mode** to enable timed intervals configured via the **Timer** knob.


4. **Play!**: Pluck the target note on your instrument. The central target circle provides live feedback showing your detected note and cents deviation, flashing green once the note is held in tune.

---

## 📣 Feedback & Community Testing

FretTrain is under active development, and user feedback is essential to fine-tuning its performance!

We are specifically seeking feedback on:

* **Audio Performance & Latency**: How responsive is the pitch detection on your microphone or audio interface setup?
* **Low-Frequency Accuracy**: How accurately does pitch detection perform on low-E ($E_2$) guitar strings or 4/5-string bass notes ($E_1 / B_0$)?
* **UI & Workflow**: Are the controls intuitive? What additional practice modes or features (e.g., specific fret ranges, chord recognition) would you like to see?

If you encounter any bugs, pitch detection anomalies, or performance bottlenecks, please **Open an Issue** or submit a **Pull Request** with your audio interface details and OS specifications.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
