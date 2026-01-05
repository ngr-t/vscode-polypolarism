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

1. Install the extension from VSCode Marketplace (or load from VSIX)
2. Install polypolarism in your Python environment:
   ```bash
   pip install polypolarism
   ```

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

### Setup

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies
python -m pip install nox
nox --session setup
```

### Build

```bash
npm run compile
```

### Debug

Use the `Debug Extension and Python` launch configuration in VS Code.

### Package

```bash
npm run vsce-package
```

This creates `polypolarism.vsix` which can be installed manually.

## License

MIT
