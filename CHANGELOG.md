# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-05-18

### Added
- Transparent, frameless real-time Overlay for visual feedback during the reroll process.
- Overlay dynamically centers and highlights in green upon finding the target stats.
- Global hotkey `F6` to start the reroll without opening the interface.
- Automatic configuration saving (`last_config.json`) upon any UI interaction to prevent data loss.
- Integrated `build.py` script for automated Nuitka compilation and source backup.
- In-app Advanced User Guide dialog with visual image support.

### Fixed
- Fuzzy matching algorithm (`difflib`) implemented to aggressively correct common OCR typos (e.g., "Tahen" instead of "Taken").
- Percentage Logic Strictness: Accurately distinguishes between flat stats and percentage stats (e.g., "Damage Taken" vs "Damage Taken %").
- Prefix Filtering: The analyzer now actively rejects false-positive substring matches (prevents "Nature Damage Taken" from satisfying a "Damage Taken" requirement).
- Number Extraction Logic: The engine now always searches for the *last* valid number in a string to avoid capturing UI artifacts like item weight ("Peso: 20.0").
- Reroll Loop condition bugs preventing the bot from stopping correctly when multiple target stats were required.
- Refactored UI layout into two organized columns to fit all configurations on a single primary tab.

## [1.0.0] - Initial Release

### Added
- Basic PyQt6 Interface with Tabbed navigation.
- Hotkey-based screen coordinate calibration (F8, F10, F11, F12).
- Multithreaded Reroll Engine (`QThread`) to keep the UI responsive.
- Basic Windows OCR wrapper (`winsdk`) integration.
- Save and Load functionality for JSON configuration profiles.
