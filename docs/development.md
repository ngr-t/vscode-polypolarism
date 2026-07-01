# Development

How to build, debug, and package the Polypolarism VS Code extension from
source. If you just want to *use* the extension, see the
[README](../README.md).

## Prerequisites

- Node.js >= 18.17.0
- npm >= 8.19.0
- Python 3.11+
- nox (`pip install nox`)

## Setup

```bash
# 1. Install Node.js dependencies
npm install

# 2. Install nox (use a virtual environment or uv to avoid system Python restrictions)
uv venv .venv
source .venv/bin/activate  # or: .venv/Scripts/activate on Windows
uv pip install nox

# 3. Set up Python dependencies (pygls, etc.)
nox --session setup

# 4. Install polypolarism into bundled/libs
#    polypolarism is not on PyPI, so install from a local path or GitHub.
python3 -m pip install -t ./bundled/libs --no-cache-dir --no-deps /path/to/polypolarism
# Or from GitHub:
python3 -m pip install -t ./bundled/libs --no-cache-dir --no-deps git+https://github.com/ngr-t/polypolarism.git
```

`bundled/libs` is gitignored, so a fresh polypolarism snapshot only ships once
you repackage the `.vsix`.

## Build

```bash
npm run compile
```

## Debug

Use the **Debug Extension and Python** launch configuration in VS Code (F5) to
open an Extension Development Host running the local build.

## Package

```bash
npm run vsce-package
```

This creates `polypolarism.vsix`, which can be installed manually:

```bash
code --install-extension polypolarism.vsix
# Or on macOS if `code` is not on PATH:
"/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" --install-extension polypolarism.vsix
```

## Demo GIF

The README demo (`docs/demo.gif`) is reproducible with `npm run demo` — see
[`capture/README.md`](../capture/README.md).

## Troubleshooting

### "externally-managed-environment" error when installing nox

Use a virtual environment:

```bash
uv venv .venv && source .venv/bin/activate && uv pip install nox
```
