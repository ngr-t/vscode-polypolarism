# Polypolarism VSCode Extension

Static type checker for Polars DataFrames based on row polymorphism.

## Features

- Real-time type checking for Polars DataFrame operations
- Shows errors and warnings in the Problems panel and inline in the editor
- Diagnostics carry their stable polypolarism code (`PLY###` errors,
  `PLW###` warnings); the code links to the corresponding table in the
  [polypolarism README](https://github.com/ngr-t/polypolarism#diagnostic-codes)
- Files that fail to parse are reported as a syntax-error diagnostic
- Schema hover: hovering inside a checked function shows polypolarism's
  view of it — per-parameter frames and the declared vs inferred return
  frames (an `...` marks open frames that may carry extra columns)
- Checks on file open and save

## Requirements

- VS Code 1.78.0 or greater
- Python 3.11 or higher
- `polypolarism` package installed in your Python environment
  (recommended; see [Installation](#installation))
- polypolarism's supported window: Polars `1.37+`, Pandera `0.19+`
  (older versions are best-effort and flagged by a `PLW010` warning;
  see [Supported versions](https://github.com/ngr-t/polypolarism#supported-versions))

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

4. Set `polypolarism.importStrategy` to `fromEnvironment` (recommended:
   the bundled copy is only a fallback snapshot and may lag behind the
   version you installed)

5. Reload VSCode window

## Usage

Declare schemas as Pandera `DataFrameModel` classes and annotate your
functions with `DataFrame[Schema]` / `LazyFrame[Schema]`:

```python
import pandera.polars as pa
import polars as pl
from pandera.typing.polars import DataFrame


class Users(pa.DataFrameModel):
    id: int
    name: str


class ActiveUsers(pa.DataFrameModel):
    id: int
    name: str
    active: bool


def process_users(users: DataFrame[Users]) -> DataFrame[ActiveUsers]:
    return users.with_columns(pl.lit(True).alias("active"))
```

The extension will automatically check your code on open and save and
report any type mismatches.

## Diagnostics

| Kind | Codes | Shown as |
|---|---|---|
| Errors | `PLY001`–`PLY033` | Problems panel **Error** |
| Warnings | `PLW001`–`PLW010` | Problems panel **Warning** |

Each diagnostic's code links to its description in the polypolarism
README ([error table](https://github.com/ngr-t/polypolarism#diagnostic-codes),
[warning table](https://github.com/ngr-t/polypolarism#apply-style-helpers-and-warning-codes)).
Files that cannot be parsed produce an uncoded `SyntaxError` diagnostic
instead of being silently skipped.

## Configuration

- `polypolarism.args`: Additional arguments to pass to polypolarism
- `polypolarism.path`: Custom path to polypolarism executable
- `polypolarism.interpreter`: Python interpreter to use
- `polypolarism.importStrategy`: Where to import polypolarism from (`useBundled` or `fromEnvironment`; `fromEnvironment` is recommended while polypolarism is not on PyPI)
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
   - `useBundled`: Uses the polypolarism snapshot bundled with the extension
   - `fromEnvironment`: Uses polypolarism from your Python environment (recommended — keeps you on the version you installed from GitHub)

### "externally-managed-environment" error when installing nox

Use a virtual environment:
```bash
uv venv .venv && source .venv/bin/activate && uv pip install nox
```

## License

MIT
