# Architecture Overview

This document outlines the technical architecture of the **ARK Reroll Automator**.

## 1. System Flow Diagram

```text
+-----------------------+       +-------------------------+
|   User Interface      |       |    Config Manager       |
|      (PyQt6)          | <---> |   (last_config.json)    |
+-----------------------+       +-------------------------+
           |
           | Start Reroll (QThread)
           v
+-----------------------+       +-------------------------+
|    Reroll Engine      | ----> |     Overlay Window      |
|  (Mouse Automation)   |       | (Transparent UI / HUD)  |
+-----------------------+       +-------------------------+
           |
           | 1. Click Item
           | 2. Capture Region
           v
+-----------------------+       +-------------------------+
|      OCR Engine       | ----> |     Windows OCR API     |
|     (mss + winsdk)    |       |   (Native UWP Engine)   |
+-----------------------+       +-------------------------+
           |
           | Returns raw text block
           v
+-----------------------+       +-------------------------+
|      Analyzer         | <---- |     Stats Config        |
|  (Regex + difflib)    |       |  (Target definitions)   |
+-----------------------+       +-------------------------+
           |
           | Returns True/False (Approved)
           v
+-----------------------+
|    Reroll Engine      |
|  (Decides Next Step)  |
+-----------------------+
           |
           +--> If Approved: Stop, Show Success on Overlay
           +--> If Rejected: Click Reroll, Repeat Loop
```

## 2. Module Responsibilities

### `main.py` & `main_window.py`
- **Responsibility:** Orchestrates the application. Handles user inputs, UI state, global hotkeys binding, and initialization of the QThread for the reroll engine.
- **Key Methods:** `setup_ui()`, `start_reroll()`, `on_reroll_progress()`.

### `reroll_engine.py`
- **Responsibility:** Executes the automation loop in a background thread to keep the UI responsive. Simulates mouse clicks, manages delays, and bridges the OCR and Analyzer modules.
- **Key Methods:** `run()` (The main loop). Emits `progress` signals to the UI.

### `ocr_engine.py`
- **Responsibility:** Captures specific screen regions and extracts text.
- **Key Methods:** `capture_and_recognize(x, y, w, h)`.
- **Inputs:** Coordinates and dimensions.
- **Outputs:** Extracted raw text.

### `analyzer.py`
- **Responsibility:** Cleans up the raw OCR text, identifies target stats using fuzzy matching, and extracts numeric values.
- **Key Methods:** `analyze_text()`, `is_fuzzy_match()`.

### `overlay.py`
- **Responsibility:** Provides a frameless, transparent, click-through overlay that stays always on top. It renders status updates visually to the user.
- **Key Methods:** `update_status()`, `center_window()`.

### `config_manager.py`
- **Responsibility:** Serializes and deserializes the application's state (coordinates, target stats, delays) to disk.

## 3. Technical Reroll Flow

1. **Initialization:** The user hits Start. `MainWindow` reads all UI states, saves them via `ConfigManager`, and creates a `RerollEngine` instance inside a `QThread`.
2. **Loop Start:** `RerollEngine` moves the mouse to the Item coordinate and clicks it.
3. **Delay:** Waits for a predefined time (e.g., 1.0s) for the game server to respond and render the tooltip.
4. **Capture:** Calls `ocr_engine.py`. `mss` takes a fast screenshot of the bounding box. The image buffer is passed to the Windows UWP OCR engine via asynchronous bindings (`winsdk`).
5. **Analysis:** The raw text is passed to `analyzer.py`. The text is split into lines. Each line is checked against the target stat using strict substring matching, followed by sliding-window fuzzy matching to account for OCR errors. If a match is found, regex extracts the numeric value at the end of the line.
6. **Decision:** 
   - If the stat is found and `>=` the minimum value, `RerollEngine` stops the loop, emits a success signal, and the UI centers the Overlay with a Success message.
   - If the stat is missing or too low, `RerollEngine` clicks the Reroll button, waits for the `click_delay`, and the loop restarts.

## 4. Technical Decisions & Justifications

- **`mss` over `Pillow/PyAutoGUI` for Screenshots:** `mss` interfaces directly with the OS display APIs using ctypes, making it significantly faster (often <10ms per frame) compared to ImageGrab, which is crucial for a fast reroll loop.
- **Windows Native OCR over Tesseract:** Tesseract is heavy, requires a separate installation binary, and uses massive traineddata files. Windows 10/11 has a highly optimized, built-in OCR engine accessible via `winsdk`. It is fast, lightweight, and requires no external downloads for the user.
- **Fuzzy Matching (`difflib`):** OCR is imperfect, especially with stylized game fonts. Characters like `k` are often read as `h` ("Taken" -> "Tahen"). Using `difflib.SequenceMatcher` allows us to tolerate a 15% error rate in character recognition, drastically reducing false negatives.
- **Prefix Rejection Logic:** Stats in ARK Omega often share base names (e.g., "Damage Taken" vs "Nature Damage Taken"). The analyzer specifically checks the characters immediately preceding a match to ensure we do not falsely accept an elemental variant of a base stat.
