# Polypolarism VSCode Extension

Static type checker for Polars DataFrames based on row polymorphism.

## Features

- Real-time type checking for Polars DataFrame operations
- Shows errors in the Problems panel and inline in the editor
- Checks on file save

## Requirements

- VS Code 1.78.0 or greater
- Python 3.11 or higher
- `polypolarism` package installed in your Python environment

## Installation

### From VSIX (Manual Installation)

1. Download or build the `.vsix` file (see [Development](#development) section)
2. Install via command line:
   ```bash
   code --install-extension polypolarism.vsix
   ```
   Or on macOS if `code` command is not available:
   ```bash
   "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" --install-extension polypolarism.vsix
   ```

3. Install polypolarism in your Python environment:
   ```bash
   # From GitHub (polypolarism is not yet on PyPI)
   pip install git+https://github.com/ngr-t/polypolarism.git
   ```

4. Reload VSCode window

## Usage

Add type annotations to your DataFrame functions using the `DF` type:

```python
from polypolarism import DF

def process_users(
    users: DF["{id: Int64, name: Utf8}"],
) -> DF["{id: Int64, name: Utf8, active: Boolean}"]:
    return users.with_columns(pl.lit(True).alias("active"))
```

The extension will automatically check your code on save and report any type mismatches.

## Configuration

- `polypolarism.args`: Additional arguments to pass to polypolarism
- `polypolarism.path`: Custom path to polypolarism executable
- `polypolarism.interpreter`: Python interpreter to use
- `polypolarism.importStrategy`: Where to import polypolarism from (`useBundled` or `fromEnvironment`)
- `polypolarism.showNotifications`: When to show notifications (`off`, `onError`, `onWarning`, `always`)

## Commands

- `Polypolarism: Restart Server` - Restart the language server

## Development

### Prerequisites

- Node.js >= 18.17.0
- npm >= 8.19.0
- Python 3.11+
- nox (`pip install nox`)

### Setup

```bash
# 1. Install Node.js dependencies
npm install

# 2. Install nox (use virtual environment or uv to avoid system Python restrictions)
uv venv .venv
source .venv/bin/activate  # or: .venv/Scripts/activate on Windows
uv pip install nox

# 3. Setup Python dependencies (pygls, etc.)
nox --session setup

# 4. Install polypolarism to bundled/libs
#    Note: polypolarism is not on PyPI, so we install from local path or GitHub
python3 -m pip install -t ./bundled/libs --no-cache-dir --no-deps /path/to/polypolarism
# Or from GitHub:
python3 -m pip install -t ./bundled/libs --no-cache-dir --no-deps git+https://github.com/ngr-t/polypolarism.git
```

### Build

```bash
npm run compile
```

### Debug

Use the `Debug Extension and Python` launch configuration in VS Code (F5).

### Package

```bash
npm run vsce-package
```

This creates `polypolarism.vsix` which can be installed manually.

### Install Locally

```bash
code --install-extension polypolarism.vsix
# Or on macOS:
"/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" --install-extension polypolarism.vsix
```

## Troubleshooting

### "No matching distribution found for polypolarism"

polypolarism is not yet published to PyPI. Install it from GitHub:
```bash
pip install git+https://github.com/ngr-t/polypolarism.git
```

### Extension not detecting polypolarism

1. Make sure polypolarism is installed in the Python environment VSCode is using
2. Check `polypolarism.importStrategy` setting:
   - `useBundled`: Uses polypolarism bundled with the extension
   - `fromEnvironment`: Uses polypolarism from your Python environment (recommended for development)

### "externally-managed-environment" error when installing nox

Use a virtual environment:
```bash
uv venv .venv && source .venv/bin/activate && uv pip install nox
```

## License

MIT
