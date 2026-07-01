# Recording the README demo GIF

Target artifact: `docs/demo.gif`, embedded at the top of the README. Follow the
4-scene storyboard in [`demo-workspace/README.md`](demo-workspace/README.md).

## 1. Set up the stage

1. Open this repo in VS Code and press `F5` (*Debug Extension and Python*) to
   launch the **Extension Development Host** with the local extension build.
2. In that window, open the folder `docs/demo-workspace`.
3. Make it look clean:
   - High-contrast theme (Default Dark Modern or Light+).
   - Editor font ~15px; `View: Zoom` until the text is comfortably large.
   - Hide the minimap (`View → Appearance → Minimap`) and the Activity/Side
     bar if not needed; keep the **Problems** panel open for Scene 1.
   - Resize the window to a tight 16:9-ish rectangle (~1280×720) so the GIF
     stays small.
4. Confirm `pipeline.py` shows the red squiggle on line 15 before you record
   (the take starts from the error state).

## 2. Capture

macOS built-in screen recording is the simplest source:

- Press `Cmd-Shift-5` → **Record Selected Portion** → drag a box around the
  editor → **Record**. Run through the storyboard, then stop from the menu bar.
- A `.mov` lands on the Desktop. Keep the take to ~25s.

## 3. Convert to GIF

> Neither **ffmpeg** nor **gifski** is currently on `PATH`. Install whichever
> recipe you use first.

### Recommended — gifski (smallest, best-dithered GIFs)

```bash
brew install gifski ffmpeg          # gifski reads the .mov via ffmpeg
gifski --fps 15 --width 1200 -o docs/demo.gif ~/Desktop/Screen\ Recording*.mov
```

### Fallback — pure ffmpeg (two-pass palette)

```bash
brew install ffmpeg
ffmpeg -i ~/Desktop/Screen\ Recording*.mov \
  -vf "fps=15,scale=1200:-1:flags=lanczos,palettegen" -y /tmp/palette.png
ffmpeg -i ~/Desktop/Screen\ Recording*.mov -i /tmp/palette.png \
  -lavfi "fps=15,scale=1200:-1:flags=lanczos,paletteuse" -y docs/demo.gif
```

Tune `--fps`/`fps` (12–15) and `--width`/`scale` (1000–1200) to keep the file
comfortably under GitHub's ~10 MB inline limit. Check the result:

```bash
ls -lh docs/demo.gif
```

## 4. Clean up

The QuickFix and rename steps modify the workspace files during recording.
Restore them so the committed fixtures stay in the pristine error state:

```bash
git restore docs/demo-workspace
```

Then commit `docs/demo.gif` alongside the README change.
