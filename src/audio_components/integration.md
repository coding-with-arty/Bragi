Integrating audio pitch detection and time management into an existing Flet application requires moving from a pure button-driven UI to an event-driven architecture. The integration is broken down into four core steps below, complete with copy-paste AI prompts to generate the exact glue code for each phase.

---

## Integration Plan Overview

1. **State & Architecture Setup:** Refactor the existing Flet state to centralize game flow, target notes, and audio configuration.
2. **UI Component Expansion:** Add dynamic visual feedback elements (tuner meter, sharp/flat indicators, countdown progress bars, device selectors).
3. **Event Loop & Thread Synchronization:** Wire background audio events and async timer ticks into thread-safe Flet UI updates.
4. **Lifecycle & Audio Settings Management:** Manage microphone initialization, input selection, sensitivity calibration, and clean shutdown on app exit.

---

## Phase 1: State & Architecture Setup

Before connecting real-time events, centralize application state management. The app must track game modes (Manual, Timed, Tuner, Hybrid), active target notes, timer state, and incoming tuner metrics without tying logic directly to UI controls.

### 🤖 Prompt 1: Refactoring Flet State & Game Controller

```text
Act as a Senior Python Application Architect specializing in Flet and clean state management patterns (MVC/MVVM).

I am refactoring an existing Flet fretboard training application. Currently, the app shows a random note/string combination and advances when the user clicks a "Next" button. I need to convert this into a centralized, event-driven state controller (`AppController` and `AppState`) that can be controlled manually, via async timers, or via background audio pitch detection.

### Requirements:

1. **State Dataclasses (`AppState`):**
   - Active mode: `MANUAL`, `TIMED`, `TUNER`, `HYBRID` (Timer + Tuner)
   - Current target: `target_note` (e.g., "A"), `target_octave` (e.g., 2), `target_string` (e.g., 5), `target_fret` (e.g., 0)
   - Tuner feedback state: `detected_frequency`, `cents_off`, `is_in_tune`, `is_silent`, `current_volume_db`
   - Timer state: `time_remaining`, `timer_progress` (0.0 to 1.0), `is_timer_running`
   - Score/Stats: `correct_count`, `missed_count`, `streak`

2. **Controller Logic (`AppController`):**
   - Method `next_note()`: Selects a new target note based on user-selected instrument tuning (Standard E, Drop D, etc.) and allowed string ranges, then resets timer and audio lockouts.
   - Method `on_audio_hit()`: Called when the audio engine confirms a correct note. Increments score, triggers success state, and auto-calls `next_note()`.
   - Method `on_timer_expire()`: Called when time runs out. Registers a missed attempt and auto-calls `next_note()`.
   - Thread-safe state update dispatching so UI subscribers receive state change notifications.

3. **Output:**
   - Provide a clean Python module (`app_controller.py`) that encapsulates this logic and imports cleanly into a Flet application context.

```

---

## Phase 2: UI Component Expansion

Extend the existing Flet interface to render live audio information (tuning gauges, volume levels) and countdown animations without lagging the UI.

```
+-------------------------------------------------------------+
|                      [ Target: A2 ]                         |
|                    String 5 - Fret 0                        |
+-------------------------------------------------------------+
|  Timer Progress: [========================........] 3.2s   |
+-------------------------------------------------------------+
|  Tuner Visualizer:                                          |
|        FLAT <------------ [|||O|||] ------------> SHARP     |
|        Note: A2 | Freq: 110.2 Hz | -3 Cents | In-Tune       |
+-------------------------------------------------------------+
|  [ Settings / Mic Selector ]   [ Pause ]   [ Mode Selector] |
+-------------------------------------------------------------+

```

### 🤖 Prompt 2: Building Live Tuner & Timer Flet UI Controls

```text
Act as a UI/UX Engineer specializing in Python Flet frontend development.

I need to add real-time tuner and timer controls to an existing Flet application interface. These components must update smoothly up to 20 times per second without causing UI flicker or blocking user interaction.

### UI Components Required:

1. **Timer Progress Bar (`TimerDisplay`):**
   - A `ft.ProgressBar` or visual meter displaying fractional remaining time (0.0 to 1.0).
   - Dynamic color transition (e.g., Green > Yellow when < 50% > Red when < 20%).
   - A numerical label showing seconds remaining (`3.2s`).

2. **Real-time Pitch / Tuner Gauge (`TunerWidget`):**
   - A visual needle/bar indicator showing pitch error in cents (-50 cents to +50 cents).
   - Sharp/Flat indicator lights or text (`<<< FLAT` | `IN TUNE` | `SHARP >>>`).
   - Text display showing live `Detected Note`, `Frequency (Hz)`, and `Volume (dB)`.
   - Visual state change when note matches (e.g., target turns bright green, gauge pulses).

3. **Control Bar & Settings Overlay:**
   - Mode selector dropdown (`Manual`, `Timed Only`, `Mic Only`, `Mic + Timer`).
   - Start / Pause / Reset button row.
   - Microphone selector dropdown button.

4. **Code Structure:**
   - Write reusable Flet custom controls (`ft.UserControl` or helper view classes in Python 3.10+).
   - Ensure controls provide dedicated update methods (e.g., `update_tuner_data(freq, cents, in_tune)`) that can be called efficiently.

```

---

## Phase 3: Event Loop & Thread Synchronization

Connecting continuous audio threads (`audio_worker.py`) and async tasks (`timer_manager.py`) to Flet requires bridging background events onto Flet's UI thread using `page.run_task` or thread-safe UI update schedules.

### 🤖 Prompt 3: Wiring Background Threads & Async Loops into Flet

```text
Act as a Senior Concurrent Systems Developer specializing in Python `asyncio`, multithreading, and Flet page lifecycle management.

I need the integration code that connects `pitch_detector.py`, `audio_worker.py`, `timer_manager.py`, and `app_controller.py` into the main Flet application entry point (`main(page: ft.Page)`).

### Integration Requirements:

1. **Lifecycle Management inside `main(page)`:**
   - Instantiate `AudioWorker` on app startup in a background daemon thread.
   - Instantiate `TrainerTimer` within Flet's `asyncio` event loop.
   - Register cleanly with `page.on_disconnect` or `page.window.on_event` to ensure audio streams stop and threads close when the user closes the window.

2. **Event Routing:**
   - **Tuner Updates (`on_pitch_update`):** Route high-frequency incoming audio stream data to update `TunerWidget` real-time values safely using `page.run_task` or thread-safe UI updates.
   - **Match Detected (`on_note_matched`):** Trigger success audio chime/flash in UI, reset `TrainerTimer`, and call `AppController.next_note()`.
   - **Timeout Expired (`on_timeout`):** Trigger missed note visual cue, increment missed counter, and call `AppController.next_note()`.

3. **Performance Optimization:**
   - Implement rate-limiting / throttling for raw pitch UI updates (e.g., max 20 UI refreshes/sec) to avoid overwhelming the Flet WebSocket / UI renderer.
   - Prevent race conditions where a late audio hit triggers *after* a timer timeout has already advanced the note.

4. **Output:**
   - Provide a complete, fully wired `main.py` entry point script demonstrating the initialization, callback wiring, and UI binding.

```

---

## Phase 4: Lifecycle & Audio Settings Management

The final phase adds device selection and noise floor calibration to handle different room environments and instrument signal levels.

### 🤖 Prompt 4: Audio Device Selection & Calibration Dialog

```text
Act as a Python Desktop Developer experienced with `sounddevice` and Flet dialog interfaces.

I need a settings modal dialog (`AudioSettingsDialog`) for my Flet app that allows users to select input microphones, adjust input gain/noise gates, and calibrate instrument tuning thresholds.

### Requirements:

1. **Device Enumeration:**
   - Query available audio input devices using `sounddevice.query_devices()`.
   - Filter and display valid audio input channels in a `ft.Dropdown`.

2. **Live Noise Floor Calibration:**
   - Include a live volume meter inside the settings dialog showing real-time background room noise in dB/RMS.
   - A threshold slider (`ft.Slider`) allowing users to adjust the noise gate cutoff (e.g., -50 dB to -10 dB) so room noise does not trigger the pitch detector.
   - A cents tolerance slider (e.g., $\pm 10$ cents for strict practice up to $\pm 35$ cents for loose practice).

3. **Hot-Swapping Audio Streams:**
   - When the user selects a new input device or changes thresholds in the dialog, restart or update the `AudioWorker` stream without restarting the entire Flet application.

4. **Output:**
   - Provide a self-contained Flet view component `AudioSettingsDialog` with code handling input device selection and live parameter tuning.

```

---
