# Demo GIF capture

Automated capture of the README demo (`docs/demo.gif`). Launches a real VS Code
via `@vscode/test-electron` on a throwaway copy of `docs/demo-workspace`, drives
the extension through four feature scenes, screenshots each, and stitches the
frames into a GIF.

## Commands

```bash
npm run demo          # capture frames, then build docs/demo.gif
npm run demo:capture  # just capture PNG frames -> $PLY_FRAMES (default /tmp/ply-frames)
npm run demo:gif      # just rebuild the GIF from existing frames
```

## Requirements (macOS)

- `ffmpeg` and `gifski` on PATH (`brew install ffmpeg gifski`) — only `ffmpeg`
  is used by `make-gif.sh`; `gifski` is an alternative assembler.
- **Screen Recording permission** for the terminal running the capture
  (System Settings → Privacy & Security → Screen Recording). `screencapture`
  needs it on macOS 13+.
- A `.venv` with a Python 3.8+ interpreter at `.venv/bin/python` (the bundled
  polypolarism runs against it; polars/pandera need NOT be installed).

## Notes

- The capture **takes over the screen for ~1 minute** (VS Code goes full-screen
  so the grab is just the editor). Don't use the machine while it runs.
- The UI is forced to English (`--locale=en`); Pylance, the git "open
  repository?" prompt, chat, and the minimap are disabled via seeded settings so
  the frames are clean. Nothing machine-specific touches `docs/demo-workspace`.
- Scenes: (1) diagnostics + Problems panel, (2) schema hover, (3) column rename
  on the `Sales.amount` declaration, (4) QuickFix lightbulb. Tune holds/size via
  `HOLD` and `WIDTH` env vars for `make-gif.sh`.
