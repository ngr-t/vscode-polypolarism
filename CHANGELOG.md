# Change Log

## Unreleased

Catch-up sync with polypolarism main:

- Diagnostics now expose the stable polypolarism code (`PLY###` /
  `PLW###`) in the LSP `code` field; the code links to the matching
  table in the polypolarism README from the Problems panel.
- Diagnostic ranges span the reported `end_line` / `end_column` instead
  of collapsing to a zero-width position.
- Multi-file JSON output: the per-diagnostic `file` field is respected,
  so diagnostics are never attributed to the wrong document.
- Parse/read failures (now emitted by the CLI as failing CheckResults,
  e.g. `SyntaxError`) surface as uncoded error diagnostics.
- README rewritten for the Pandera `DataFrameModel` schema declaration
  (the legacy `DF["{...}"]` DSL was removed from polypolarism) and the
  supported-version window (Polars 1.37+, Pandera 0.19+).
- Python LSP tests replaced the generator-template examples with a real
  polypolarism end-to-end check (one `PLY001` error, one `PLW007`
  warning).

## 0.1.0

- Initial preview release.
