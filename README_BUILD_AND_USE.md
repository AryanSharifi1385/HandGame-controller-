# Hand Game Controller — build and user guide

## What's included

- `launcher.py` — desktop control panel
- `mian.py` — controller engine (the filename is intentionally kept as `mian.py`)
- Supporting camera, hand tracking, movement, gesture, input and settings modules
- `hand_landmarker.task` — MediaPipe hand landmark model
- `build_exe.bat` — Windows packaging script

## Run from Python (Windows)

1. Install 64-bit Python 3.11 or 3.12. MediaPipe wheels and packaging compatibility vary by Python version; use a supported version rather than assuming the newest Python will work.
2. Open Command Prompt in this project folder.
3. Create and activate a virtual environment:

   ```bat
   py -3.11 -m venv .venv
   .venv\Scripts\activate
   ```

4. Install the requirements:

   ```bat
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Start the desktop panel:

   ```bat
   python launcher.py
   ```

The camera window is started from the panel. The launcher panel can be scrolled using the mouse wheel or its right-side scrollbar. Use **Stop safely** in the panel or press `]` in the camera window to exit. The left-pinky Ability gesture remains independently mapped to its configured action key (default `Q`).

## Build the Windows EXE files

1. On Windows, install Python 3.11 or 3.12 (64-bit) and make sure `python` works in Command Prompt.
2. Double-click `build_exe.bat`, or run it from Command Prompt.
3. When the build completes, distribute these two files together from `dist`:
   - `HandGameController.exe` — the desktop control panel
   - `HandGameControllerCore.exe` — the hand-tracking and input engine

The MediaPipe model is bundled inside the core executable. Keep both executables in the same folder. The first start may take longer because one-file PyInstaller apps extract bundled components to a temporary directory.

### If the EXE build fails

- Read the first missing-module or hook error in the build output; later errors may be consequences.
- Run the build on Windows, not Linux, because the input layer uses Windows `SendInput` APIs.
- Confirm the selected Python version is supported by the installed MediaPipe release.
- Antivirus software may quarantine newly built unsigned executables. Do not disable protection globally; inspect the detection and sign the release build if distributing commercially.

## User settings

The control panel supports:

- Mouse sensitivity
- Jitter dead zone
- Maximum cursor movement per frame
- A gesture-to-key binding table: gesture names on the left and selectable output keys on the right
- Ten switchable visual themes: Cyberpunk (default), Ghost of Tsushima, The Last of Us, God of War, GTA VI, Call of Duty, Stray, Matrix, Synthwave, and Arctic
- Named control profiles that can be saved, loaded, and deleted from the launcher

Mouse settings are reloaded while the controller runs. Keyboard binding changes apply after stopping and starting the controller. Settings and logs are written to `%LOCALAPPDATA%\HandGameController` in packaged builds; during Python development they are written beside the source files.

The key selector includes the currently supported alphanumeric keys and common modifiers/navigation keys. Gesture recognition itself remains fixed to the documented gesture set; users can customize the output key for each existing action, but cannot create entirely new gestures from the UI. The hand names shown in the launcher and camera overlay are intentionally swapped for display only; the actual tracking and control logic is unchanged. LMB and RMB labels are unchanged.

### Saved game profiles

- **Save As** stores the current mouse settings and key bindings as a named profile.
- **Load Profile** applies a saved profile to the current settings. Stop the controller first before loading so the key bindings are reinitialized cleanly.
- **Delete** removes a saved user profile. The built-in **Default** profile is protected.
- Profiles are stored as `profiles.json` alongside the other user data in `%LOCALAPPDATA%\HandGameController` for packaged builds. Each profile is a snapshot; changing the current controls does not silently overwrite a saved profile.

## Gesture reference

- **Left hand movement:** movement is determined by the calibrated hand position.
- **Left thumb + pinky pinch:** hold the configured Jump key.
- **Left thumb + middle-finger pinch:** hold the configured Interact key.
- **Left-hand fist:** sends the configured Fist action key once per fist gesture.
- **Right-hand thumbs-up:** activates whole-hand relative mouse movement.
- **Right index pointing while thumbs-up mouse mode is active:** hold right mouse / aim. Curl the index finger to release aim while mouse mode remains active.
- **Right thumb + middle-finger pinch outside thumbs-up mode:** normal aim / right mouse, retained from the previous behavior.
- **Right thumb + ring-finger pinch:** hold the configured Sprint key.
- **Right thumb + pinky pinch:** sends the configured R action once per gesture.

If tracking is lost, the program attempts to release held inputs. Always test the gestures in a safe desktop or training environment before using them in a game where accidental input could cause problems.

## Validation notes

Python syntax and settings normalization can be checked on any platform. The full camera loop, Windows key injection, packaged EXEs, camera-specific gesture reliability and live gameplay still require testing on a Windows machine with a webcam. This project has not been represented as fully hardware-tested by this build process.

## Additional key gestures
- **C** — Left thumb touches left ring fingertip; hold to keep the key down.
- **Q** — Left pinky extended while the index, middle, and ring fingers are curled and the thumb is not extended; sends one key tap each time the pose begins.
- **Left Ctrl** — Left thumb and pinky extended, with index, middle, and ring fingers curled; hold to keep Ctrl down.
- **Left Alt** — Right thumb touches right index fingertip; hold to keep Alt down. This gesture is ignored while right-hand thumbs-up mouse mode is active, preserving mouse activation and movement.

These bindings are configurable in the control panel and are included in saved profiles. Gesture reliability still depends on camera angle, lighting, and clear fingertip visibility; test the new poses before relying on them in a game.


## Premium visual themes
The launcher includes ten locally bundled theme artworks: Cyberpunk, Ghost of Tsushima, The Last of Us, God of War, GTA VI, Call of Duty, Stray, Matrix, Synthwave, and Arctic. Theme changes update the banner artwork, display typography, title/tagline, card framing, accent rails, and palette. The game-inspired artwork is original atmospheric scenery and does not include official game logos or character art. The GUI build command bundles the `theme_art` folder into the one-file launcher.

## Assigning custom keyboard keys

In **MAKE IT YOURS · KEY BINDINGS**, click the key button beside a gesture, then press the keyboard key you want that gesture to send. The selected key is shown in the button. Click **SAVE SETTINGS** to persist changes; stop and restart the controller for the new mappings to take effect. Saved profiles also retain their key assignments.

The current Windows scan-code input layer supports standard letter and number keys, common punctuation keys, F1–F12, modifiers, navigation/editing keys, and numeric keypad keys. Some specialized keyboard keys and unusual keyboard layouts may not be supported or may use a physical-key position corresponding to the standard US scan-code layout. If a key is rejected, use another supported key.

## University showcase preparation

Before presenting, open the launcher and select **RUN PREFLIGHT CHECK**. It checks for common missing files, bundled theme artwork, Python dependencies, and whether the current environment is Windows. This check does not open the camera or send any keyboard/mouse input. A successful preflight is not a substitute for testing the webcam and real-game controls.

Use **PRESENTATION MODE** to put the launcher into fullscreen; press **Escape** to return to normal window mode. Press `]` in the camera window to close the controller view; `Q` remains the default output for the separate Ability gesture. Before the event, rehearse the complete flow on the presentation laptop: start the controller, complete calibration, verify both hand feeds/statuses, test every gesture in a safe desktop or training scene, confirm the game's control bindings, and stop safely to verify that held inputs are released.
