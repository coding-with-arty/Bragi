# Bragi — Fretboard, Tuner & Ear Training Suite

**Bragi** is a cross-platform desktop application designed for musicians, guitarists, and bassists seeking to master fretboard navigation, pitch recognition, instrument tuning, and ear training. Powered by a low-latency Digital Signal Processing (DSP) engine and a responsive UI built on **Flet**, Bragi provides real-time visual feedback for single-note picking, chromatic tuning, 11-chord quality arpeggiation, multi-instrument setups, and multi-user analytics tracking.

---

## Key Features

### 🎸 Real-Time Pitch, Tuner & Polyphonic Chord Detection

- **Real-Time Chromatic Instrument Tuner**:
  - Features an asynchronous main-thread polling loop (~25 FPS) rendering needle gauge indicators, frequency readouts (Hz), and cents deviation error.
  - Visual status alerts highlight in-tune notes within a $\pm 5\text{ cents}$ threshold.
- **Low-Frequency Guitar & Bass Pickup Optimization**:
  - Processed using an expanded 4096-sample buffer window combined with software peak normalization to capture low pitch frequencies down to $30\text{ Hz}$ (supporting 4-string and 5-string bass low B).
  - Adaptive silence gating ($-52\text{ dBFS}$) captures soft string picks without requiring gain increases that cause hardware microphone clipping.
- **11 Chord Qualities & Arpeggio Accumulator**:
  - Detects triads and 4-note 7th chords (Major, Minor, Dominant 7th, Major 7th, Minor 7th, Diminished, Half-Diminished, Augmented, Suspended) across a $2.5\text{s}$ sliding arpeggio time window.
  - Utilizes essential-tone matching rules to validate complex chords even when string intervals are played as arpeggios or intermediate tones decay.
- **Interactive Fretboard Grid**:
  - Displays recognized pitch classes ($C, C\sharp, D, \dots, B$) live on an interactive fretboard with standard fret markers ($3, 5, 7, 9, 12, 15, 17, 19, 21, 24$).

---

### 🛠️ Multi-Instrument Support & Custom Builder

- **Preset Instrument Profiles**: Built-in support for Standard 6-String Guitar, 7-String, 8-String, Bass Guitar (4/5/6 string), Ukulele, Mandolin, and Banjo.
- **Custom Instrument Builder**: Interactively configure custom instruments from 1 to 10 strings with custom pitch assignments.
- **Streamlined Tuning Sidebar**: Adjust string tuning by picking note names while octave boundaries are automatically calculated and preserved.
- **Persistent Profiles**: Custom instruments and tunings save automatically to `custom_instruments.json`.

---

### 👂 Acoustic Ear Training Suite

- **4 Interactive Training Modes**:
  1. Single Pitch Identification
  2. Interval Recognition
  3. Chord Quality Identification (Major, Minor, Dominant 7th)
  4. Inversion Trainer
- **Built-in Synthesis (`AudioSynth`)**: Karplus-Strong style string synthesis generates realistic acoustic plucks without external audio sample libraries.
- **Custom Difficulty**: Control accidentals, octave ranges, and chord difficulty from the configuration panel.

---

### 📊 Multi-User Analytics & Gamification

- **Multi-User Profile System**: Switch between user profiles with automated database schema migration handling column initialization (`user_id`).
- **XP Progression & Leveling**: Earn experience points for correct notes, held tuning accuracy, and completed ear training rounds.
- **Practice Streaks & Mastery Tiers**: Track daily streaks and view note accuracy ranked from Bronze, Silver, Gold, to Platinum (90%+ accuracy).
- **Daily Quests & Achievement Badges**: Complete daily practice goals and unlock filterable achievement badges.

---

## Tech Stack & Frameworks

| Subsystem | Technologies / Frameworks Used |
| :--- | :--- |
| **Language** | Python 3.10+ |
| **UI Framework** | [Flet](https://flet.dev/) (Flutter engine for Python) |
| **DSP Signal Processing** | NumPy, SciPy (FFT Autocorrelation, Parabolic Interpolation, Windowing) |
| **Audio I/O** | SoundDevice / PortAudio (Real-time PCM stream capture) |
| **Audio Synthesis** | Native PCM Wave Generator (`AudioSynth` acoustic synthesizer) |
| **Data Persistence** | SQLite3 (`bragi_progress.db` with dynamic schema migrations), JSON |
| **Packaging** | PyInstaller (`bragi.spec` executable build configuration) |

---

## Project Structure


```

Bragi/
├── main.py                          # Application entry point
├── bragi.spec                       # PyInstaller packaging configuration
├── requirements.txt                 # Dependencies
├── assets/                          # App icon and background graphics
└── src/
├── app_layout.py                # Main shell container & tab router
├── audio/
│   └── audio_worker.py          # Background pitch accumulation worker
├── engine/
│   ├── chord_evaluator.py       # Triad & 7th chord essential-tone matching
│   └── chord_generator.py       # Chord theory definitions
├── models/                      # Instrument and user profile models
├── services/
│   └── audio_manager.py         # Hardware microphone stream & DSP pitch engine
├── storage/
│   ├── path_utils.py            # App data directory resolution
│   └── progress_repository.py   # SQLite database & dynamic migration logic
├── utils/                       # Music theory calculations & theme management
└── views/
├── trainer_view.py          # Interactive fretboard & pitch practice view
├── components/              # Dialogs, tuning sidebar & audio settings
└── subviews/
├── tuner_view.py        # Real-time chromatic tuner view (~25 FPS polling)
├── ear_training_view.py # Ear training exercise engine
└── progress_view.py     # Analytics & profile progress dashboard

```

---

## Installation & Setup Guide

### Prerequisites

* **Python 3.10** or higher.
* Working microphone or instrument audio interface input.

---

### 1. Clone the Repository

```bash
git clone [https://github.com/YourUsername/Bragi.git](https://github.com/YourUsername/Bragi.git)
cd Bragi

```

---

### 2. Set Up Virtual Environment

#### Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1

```

#### macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate

```

---

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt

```

> **Note for Linux Users**: Ensure `portaudio19-dev` is installed prior to running pip (`sudo apt install portaudio19-dev`).

---

### 4. Run the Application

```bash
python src/main.py

```

---

## Packaging Executable (PyInstaller)

To build a standalone executable for distribution:

```bash
pip install pyinstaller
pyinstaller bragi.spec

```

The compiled output binary will be generated inside the `dist/` directory.

---

## 🔒 License & Intellectual Property Notice

```
                                PROPRIETARY LICENSE NOTICE
                                --------------------------

Copyright © Arthur Belanger. All Rights Reserved.

This software, source code, visual design, audio synthesis routines, and compiled binaries
("Bragi") are the exclusive intellectual property of Arthur Belanger.

TERMS OF USE (BETA TESTING PHASE):
1. AUTHORIZED EVALUATION: You are granted a limited, non-exclusive, non-transferable license
   to download, execute, and test Bragi solely for personal evaluation and Beta testing
   purposes.
2. STRICTLY NON-COMMERCIAL: Bragi is NOT FOR SALE. It may not be sold, resold, leased,
   licensed, sublicensed, or otherwise exploited for commercial gain under any circumstances.
3. NO REDISTRIBUTION OR MONETIZATION: You may not distribute, re-package, host, or offer
   Bragi as a paid product, service, or embedded component without explicit written
   consent from Arthur Belanger.
4. NO WARRANTY: Bragi is provided "AS IS" during this Beta testing phase without warranty
   of any kind, express or implied.

For permissions or inquiries regarding commercial licensing, contact Arthur Belanger.

