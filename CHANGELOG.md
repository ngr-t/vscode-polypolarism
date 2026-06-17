# Change Log

## Unreleased

Catch-up sync with polypolarism main:

- Diagnostics now expose the stable polypolarism code (`PLY###` /
  `PLW###`) in the LSP `code` field; the code links to the matching
  table in the polypolarism README from the Problems panel.
- Diagnostic ranges span the reported `end_line` / `end_column` instead
  of collapsing to a zero-width position.
- Function-level diagnostics no longer underline the whole function body:
  when a diagnostic starts on a `def` line, its range is narrowed onto the
  function-name token, so the squiggle marks the definition rather than
  every line. Diagnostics that do not start on a `def` line keep their
  reported range, so any finer span polypolarism emits later renders as-is.
- Multi-file JSON output: the per-diagnostic `file` field is respected,
  so diagnostics are never attributed to the wrong document.
- Parse/read failures (now emitted by the CLI as failing CheckResults,
  e.g. `SyntaxError`) surface as uncoded error diagnostics.
- README rewritten for the Pandera `DataFrameModel` schema declaration
  (the legacy `DF["{...}"]` DSL was removed from polypolarism) and the
  supported-version window (Polars 1.37+, Pandera 0.19+).
- Python LSP tests replaced the generator-template examples with a real
  polypolarism end-to-end check (one `PLY042` error, one `PLW007`
  warning).
- **Schema hover** (D-11): hovering inside a checked function shows
  polypolarism's view of it — per-parameter frames, declared vs
  inferred return frames, and an open-frame note — sourced from the
  `functions` array that `polypolarism --format json` now emits.
- **Bundled install fixed**: `nox -s setup` vendors polypolarism into
  `bundled/libs` from GitHub main (hash-pinned `requirements.txt`
  cannot carry a VCS dependency, so the tool never landed in the
  bundle before). To be replaced with a PyPI pin once published.
- `npm test` works: the `@vscode/test-electron` harness referenced by
  `package.json` now exists (downloads VS Code, installs the
  `ms-python.python` dependency, runs a smoke suite).
- Toolchains refreshed in one coherent pass, superseding the stale
  dependabot PRs: typescript-eslint 8, vsce 3.7, eslint 8.57, glob 13,
  ts-loader 9.5, webpack 5.107, pygls 2.1.1, lsprotocol 2025.0.0,
  pytest 9.
- Bundled polypolarism snapshot caught up with upstream `main`
  (`022c621`). The `--format json` contract the extension consumes
  (`diagnostics` / `functions`, frame `columns`/`open`/`strict`/`lazy`)
  is unchanged, so no server-side wiring changed; the refreshed snapshot
  just carries the upstream analyzer fixes (issues #95–#108), `# type:
  ignore[PLY###]` diagnostic suppression, and the new `PLW013`
  (`typing.cast` schema-assertion note) code. README diagnostic-code
  ranges bumped to `PLY001`–`PLY042` / `PLW001`–`PLW013` to match.

## 0.1.0

- Initial preview release.
