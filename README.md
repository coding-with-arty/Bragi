# 🎸 FretTrain - Fretboard Note Trainer

**FretTrain** is a modern, cross-platform desktop application built with Python and [Flet](https://flet.dev/). Designed for guitarists, bassists, and ukulele players, FretTrain helps musicians master note recognition across any fretboard layout, string count, or custom tuning setup.

---

## ✨ Features

- 🎵 **Multi-Instrument Presets**: Built-in standard tunings for:
  - **Guitar**: 6-String, 7-String, and 8-String Standard
  - **Bass**: 4-String and 5-String Standard
  - **Ukulele**: Standard 4-String, 5-String, and Baritone
- 🛠️ **Custom Instrument & Tuning Setup**: Adjust the string count (1–8 strings) and select custom tuning per string.
- 🎯 **Interactive Note Generator**: Focuses practice on active strings and target notes with clear visual feedback.
- 🌗 **Material Design 3 UI**: Dynamic theme switcher (Dark / Light Mode) with a clean glassmorphism UI over customizable wallpaper backdrops (`assets/bg.png`).
- 🏗️ **Modular Code Base**: Architected using clean UI separation (`views/`, `components/`, `utils/`).

---

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **UI Framework**: [Flet](https://flet.dev/) (Flutter for Python)
- **Design System**: Material Design 3

---

## 📁 Project Structure

```text
FretTrain/
├── assets/
│   └── bg.png               # Custom background graphic
├── src/
│   ├── components/          # Reusable UI controls
│   │   ├── header.py        # Top bar & theme controls
│   │   └── note_display.py  # Central note display target
│   ├── utils/               # Logic & helper modules
│   │   ├── music_theory.py  # Note array & preset calculations
│   │   └── theme_manager.py # Dark/Light theme controller
│   ├── views/               # Main application views
│   │   └── trainer_view.py  # Setup controls & main trainer grid
│   └── main.py              # Application entry point
└── requirements.txt         # Project dependencies
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- `pip` (Python package installer)

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/FretboardTrainer.git
   cd FretboardTrainer
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Background Image**
   Ensure an image named `bg.png` exists in the `assets/` directory (or supply your own custom wallpaper).

4. **Run the Application**
   ```bash
   python src/main.py
   ```

---

## 📦 Building Executables

FretTrain can be compiled into standalone native executables using the Flet CLI:

- **Windows**:
  ```bash
  flet build windows
  ```
- **macOS**:
  ```bash
  flet build macos
  ```
- **Android APK**:
  ```bash
  flet build apk
  ```

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests for new feature requests, additional instrument presets, or UI enhancements.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.