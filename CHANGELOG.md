# Project update notes

## Launcher scrolling fix

- Made the control panel vertically scrollable with a visible scrollbar and mouse-wheel support on Windows/macOS and Linux.
- Reduced the minimum window size so the launcher remains usable on smaller laptop displays.
- Kept all existing controls and settings in the same panel; the lower controls are now reachable without resizing the window.

## Controller improvement pass

- Added index-pointing detection for aim while right-hand thumbs-up mouse mode is active.
- Preserved the existing whole-hand relative mouse movement math, mouse sensitivity, dead zone, and maximum per-frame step.
- Preserved middle-finger pinch aim when thumbs-up mouse mode is inactive.
- Added immediate release when leaving the pointing-aim mode and retained the existing safe shutdown path.
- Added validated settings for output keys for movement and existing actions.
- Updated the launcher styling and added a custom key-binding section, live aim status, and clearer status feedback.
- Added a Windows PyInstaller build script and a user/build guide.
- Added regression tests for settings normalization.

## Verification performed in this environment

- All Python files passed `py_compile`.
- Five settings-normalization unit tests passed.
- Synthetic positive/negative tests for the index-pointing detector passed.
- The launcher module imported successfully.

The Windows-specific camera loop, real webcam tracking, actual input injection, and final packaged executables were not run in this environment and still require Windows hardware testing.


## Control Profiles update

- Added named control profiles to the neon launcher.
- Added Save As, Load Profile, and Delete actions.
- Added validation and protection for the built-in Default profile.
- Profiles persist separately from current settings and include mouse tuning and supported key bindings.
- Loading profiles is blocked while the controller is running to avoid live keyboard-mapping mismatches.
- Added unit tests for profile persistence, normalization, deletion, and invalid data handling.

## 2026-10-17 — Added C, Q, Left Ctrl, and Left Alt gestures
- C: left thumb + ring fingertip pinch, held while pinched.
- Q: left pinky extended with other fingers curled and thumb not extended; sends one tap per gesture entry.
- Left Ctrl: left-hand Shaka pose (thumb + pinky extended, index/middle/ring curled), held while the pose is detected.
- Left Alt: right thumb + index fingertip pinch, held while pinched; suppressed during thumbs-up mouse mode so the existing mouse activation and movement logic remain unchanged.
- Added configurable key bindings for C, Q, Left Ctrl, and Left Alt to the neon control panel and profile settings.
- Added scan-code support for C, Left Ctrl, and Left Alt.
- Existing mouse activation/movement calculations and prior gesture mappings were left in place.

## Camera UI status update (2026-10-17)
- Added live camera-overlay status for the new C, Q, Left Ctrl, and Left Alt controls.
- C, Left Ctrl, and Left Alt show HELD/OFF states.
- Q shows TRIGGERED briefly after its tap action, then returns to OFF.
- Existing thumbs-up mouse activation and mouse movement logic were left unchanged.


## 2026-10-22 — Custom key bindings, hand-label display swap, and themes

- Reworked the binding list to show the gesture/action description on the left and a selectable output-key box on the right. Existing default output keys are preserved.
- Expanded supported scan-code bindings with additional letters, digits, common navigation keys, and modifier keys. Extended-key flags are used for right-side modifiers and arrow keys.
- Swapped only the displayed Left/Right hand names in the launcher, camera landmark labels, and relevant hand-gesture status text. Internal hand tracking and control logic were not swapped. LMB/RMB labels remain unchanged.
- Added persistent visual theme selection. Cyberpunk is the default; additional palettes are Ghost of Tsushima, The Last of Us, God of War, GTA VI, Matrix, Synthwave, and Arctic. These are color themes inspired by the named games, not official artwork or licensed assets.
- Verification: Python compilation passed, all 10 existing unit tests passed, extra theme/key normalization checks passed, and a Tk smoke test launched the panel and switched between themes. Live webcam/gameplay and Windows executable packaging still require testing on Windows hardware.


## Premium theme redesign
- Replaced palette-only theme changes with original cinematic banner artwork for all eight themes.
- Added theme-specific display typography, edition labels, taglines, card framing, and accent rails.
- Bundled `theme_art` with the GUI executable in `build_exe.bat`.
- Controller and gesture-processing logic were not changed as part of this visual pass.

## 2026-10-22 — Custom keyboard key capture

- Replaced fixed key dropdowns in the control panel with click-to-capture buttons: click a gesture's key box and press the desired keyboard key.
- Added support for standard letters, digits, punctuation keys, F1–F12, navigation/editing keys, modifiers, and numeric keypad keys in the settings validation and Windows scan-code input layer.
- Kept the existing default assignments, gesture detection, mouse movement/aim behavior, themes, and profile format unchanged.
- Duplicate assignment warnings and saved profiles continue to work; mapping changes are applied after restarting the controller.
- Key capture rejects keys not supported by the current input layer instead of silently saving an unusable assignment.

## University showcase readiness pass

- Added a launcher preflight report for core project files/model, bundled theme artwork, key Python dependencies, and Windows environment suitability.
- Added a presentation-mode fullscreen toggle with Escape to exit.
- Preflight explicitly avoids opening the camera or injecting keyboard/mouse input, so it is safe to run before the demo.
- Kept the controller engine, thumb-tip mouse movement logic, gesture recognition, default key mappings, and settings/profile formats unchanged.
- Validation in this environment: Python compilation passed and all 15 automated unit tests passed. GUI interaction, webcam access, Windows input injection, packaged EXEs, and live gameplay still require a rehearsal on the presentation laptop.

## University Showcase UI pass — 2026-10-28

- Expanded the default launcher to a presentation-friendly desktop size while keeping it responsive to smaller displays.
- Added a product masthead and showcase-build badge to strengthen visual hierarchy and first impression.
- Increased the cinematic hero area and refined title spacing for better readability on a projected screen.
- Reorganized the main dashboard into two balanced columns so live telemetry, profiles, pointer tuning, key mapping, and preflight read as a deliberate control studio rather than one long settings form.
- Refined status language and card titles for a more polished operator-facing interface.
- Fixed the preflight handler being incorrectly decorated as a static method; the button now invokes it as a normal instance method.
- Added `THEME_ART_SOURCES.md` with official game-media sources and offline-safe instructions for installing real landscape art.

Validation: Python compilation and the existing unit tests should be run in the project environment. Camera operation, real input injection, packaged EXE behavior, and the visual result on the presentation laptop still require a manual Windows rehearsal.


## Showcase polish — 2026-10-31
- Re-composed the hero artwork as a right-anchored image panel instead of stretching 16:9 artwork across the entire ultra-wide banner.
- Added a dark gradient that is strongest on the left and fades smoothly from the center toward the right, keeping the title readable while preserving the artwork.
- Increased the hero banner height and retained rounded clipping so image pixels cannot spill outside the card corners.
- Applied the same right-biased crop and stronger left fade treatment to theme gallery artwork.
- Changed the in-game emergency exit key from Q to the right bracket key (`]`).


## 2026-10-31 — Final showcase UI refinement
- Reorganized the landing screen into a cinematic hero, three compact live status panels, a ten-theme visual gallery, and a separate detailed settings area.
- Replaced rectangular sidebar navigation with rounded, selectable navigation pills and softened the native button styling to fit the rounded visual system.
- Reworked hero rendering to use a right-aligned 2:1 artwork zone with a smooth left-to-right alpha reveal; art is crop-to-fill with theme-specific focal positions rather than stretched across the banner.
- Applied the same focal-aware crop, middle-to-left fade, and rounded clipping to all ten theme tiles.
- Consolidated Start, Stop, Preflight, Presentation Mode, and Save Settings into one rounded Quick Actions panel.
- Moved showcase readiness beneath profile and pointer settings to balance the lower two-column layout.
- Updated the camera-window exit hint and user guide to show `]` as the exit key; the separate Ability gesture remains mapped to its configured action key (default `Q`).
- Preserved the controller engine, hand tracking, gesture recognition, mouse behavior, key mapping defaults, and profile/settings formats.

Validation for this revision: launcher and controller Python files compile; all 15 automated unit tests pass; the Tkinter launcher starts in a virtual display and successfully rebuilds for theme changes; all 10 gallery images load. Live webcam, Windows input injection, game behavior, and packaged EXE execution still require rehearsal on the presentation laptop.
