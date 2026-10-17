# Bragi — Fretboard & Ear Training Suite

**Bragi** is a cross-platform desktop application designed for musicians, students, and guitarists seeking to master fretboard navigation, pitch class recognition, and ear training. Powered by a real-time Digital Signal Processing (DSP) engine and a responsive UI built on **Flet**, Bragi provides instant visual feedback for single-note picking, strummed dual-chord recognition, multi-instrument tuning configurations, and comprehensive gamification analytics.

---

## Key Features

### 🎸 Real-Time Pitch & Chord Detection

- **Acoustic Microphone Recognition**: Listens to live instrument input via microphone and extracts pitch classes ($C, C\sharp, D, \dots, B$) in real time.
- **Dual-Chord & Strum Recognition**: Utilizes global magnitude scaling, harmonic overtone filtering, and top-peak spectral extraction to identify chord qualities (Major, Minor, Dominant 7th) and multi-note strums.
- **Interactive Fretboard Visualization**: Highlights detected pitch classes live across an adjustable fretboard grid complete with fret landmarks ($3, 5, 7, 9, 12, 15, 17, 19, 21, 24$).

---

### 🛠️ Multi-Instrument Support & Custom Builder

- **Preset Instrument Profiles**: Native support for Standard Guitar (6-string), 7-String, 8-String, Bass Guitar (4/5/6 string), Ukulele, Mandolin, and Banjo.
- **Custom Instrument Builder Dialog**: Interactively build custom stringed instruments from 1 to 10 strings with custom pitch assignments.
- **Streamlined Tuning Sidebar**: Beginners can adjust per-string tunings by selecting note pitch classes alone (`E`, `A`, `D`, `G`, `B`, `E` or `D`, `A`, `D`, `G`, `B`, `E`) while underlying octave frequencies are automatically calculated and preserved.
- **Persistent Profiles**: Saved custom instruments and custom tunings are stored in `custom_instruments.json` for seamless recall across sessions.

---

### 👂 Acoustic Ear Training Suite

- **Interactive Exercises**: Four dedicated training modes:

1. **Single Pitch Identification**
2. **Interval Recognition**
3. **Chord Quality Identification** (Major, Minor, Dominant 7th)
4. **Inversion Trainer**

- **Acoustic String Synthesis Engine**: Built-in Karplus-Strong style acoustic synthesizer (`AudioSynth`) plays realistic pluck sounds for training feedback without requiring external sample packs.
- **Customizable Difficulty**: Toggle accidentals, octave ranges, and chord complexity directly from the settings bar.

---

### 📊 Analytics & Gamification Hub

- **Level Progression & XP**: Earn experience points for every correct pitch recognized and ear training challenge completed.
- **Daily Practice Streaks**: Automatically tracks consecutive practice days and personal best records.
- **12-Note Chromatic Mastery Tiers**: Evaluates accuracy across all 12 pitch classes, ranking note recognition from **Bronze**, **Silver**, and **Gold** up to **Platinum** (90%+ accuracy).
- **Daily Quests & Challenges**: Progress bars track real-time completion of daily quests with bonus XP rewards.
- **Category Badge Filtering**: Unlocked achievement badges filterable by category (_Trainer_, _Ear Training_, _Streaks_).

---

### 🎨 Responsive UI, Branding & User Assistance

- **Responsive Layout Shell**: Automatically adapts layout across desktop, tablet, and mobile breakpoints using side rails or bottom navigation bars.
- **Custom Window & Asset Branding**: Integrated `logo.ico` window application icon and full-bleed `bg.png` cover background with theme-adaptive translucency scrims.
- **Integrated User Guide (`?`)**: Floating top-right question mark button opens a modal guide (`HelpDialog`) detailing app navigation, tuning tips, ear training rules, and analytics tracking.

---

## Tech Stack & Frameworks

| Subsystem                    | Technologies / Packages Used                                                     |
| ---------------------------- | -------------------------------------------------------------------------------- |
| **Language**                 | Python 3.10+                                                                     |
| **UI Framework**             | [Flet](https://flet.dev/) (Flutter-backed UI framework for Python)               |
| **Signal Processing & Math** | NumPy, SciPy (FFT analysis, peak detection, spectral filtering)                  |
| **Audio Input / Capture**    | SoundDevice / PyAudio (real-time microphone PCM streaming)                       |
| **Audio Synthesis**          | Native PCM Wave Generator (`AudioSynth` acoustic pluck synthesizer)              |
| **Data Persistence**         | SQLite3 (Progress repository & user analytics), JSON (`custom_instruments.json`) |

---

## Project Structure

```
Bragi/
├── main.py                          # Main entry point & window asset routing
├── requirements.txt                 # Python package dependencies
├── assets/                          # Static assets directory
│   ├── logo.ico                     # Window branding icon
│   └── bg.png                       # Application background wallpaper
└── src/
    ├── app_layout.py                # Shell container, stack layering, navigation & help trigger
    ├── models/                      # Domain data models (InstrumentProfile, StringConfig)
    ├── storage/                     # SQLite progress repo & JSON instrument store
    ├── utils/                       # Music theory helpers, theme manager & responsive layouts
    └── views/                       # Application view layers
        ├── trainer_view.py          # Main live fretboard & pitch detection view
        ├── components/              # Reusable UI widgets
        │   ├── tuning_panel.py      # Note-only sidebar tuning control
        │   ├── custom_instrument_dialog.py # Custom 1-10 string instrument builder
        │   └── help_dialog.py       # Modal user guide and instructions
        └── subviews/                # Tab subviews
            ├── ear_training_view.py # Ear training exercise engine
            └── progress_view.py     # Analytics & gamification dashboard

```

---

## Installation & Setup Guide

### Prerequisites

- **Python 3.10** or higher installed on your system.
- Working microphone / audio input hardware.

---

### 1. Clone the Repository

```bash
git clone https://github.com/YourUsername/Bragi.git
cd Bragi

```

---

### 2. Create and Activate a Virtual Environment

#### On Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1

```

#### On macOS / Linux:

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

> **Note for Linux Users**: Ensure `portaudio19-dev` is installed on your system if `sounddevice` compilation is required (`sudo apt install portaudio19-dev`).

---

### 4. Run the Application

```bash
python main.py

```

---

## Usage Quick Start

1. **Start Live Pitch Detection**: Navigate to the **Trainer** tab, select your instrument profile from the header, and click **"Start Listening"**. Grant microphone permissions if prompted.
2. **Tune Your Instrument**: Tweak per-string note pitches in the **Custom Tuning** sidebar on the left.
3. **Build a Custom Instrument**: Click the **`+`** icon in the instrument picker header to configure an instrument with 1–10 strings.
4. **Practice Ear Training**: Switch to the **Ear Training** tab, select an exercise mode (_Single Note_, _Interval_, _Chord Quality_, or _Inversion_), click **"Play Sound"**, and choose your answer.
5. **View Your Stats**: Switch to the **Analytics** tab to track your XP, daily practice streaks, 12-note chromatic mastery levels, and achievement badges.
6. **Need Directions?**: Click the floating **`?`** button in the top right corner at any time to open the in-app user guide.

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

```
