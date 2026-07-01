# Change Log

## Unreleased

Catch-up sync with polypolarism main:

- Diagnostics now expose the stable polypolarism code (`pple-*` errors /
  `pplw-*` warnings) in the LSP `code` field; the code links to the
  matching table in polypolarism's diagnostics reference from the Problems
  panel.
- Diagnostic ranges span the reported `end_line` / `end_column` instead
  of collapsing to a zero-width position.
- Function-level diagnostics no longer underline the whole function body:
  when a diagnostic starts on a `def` line, its range is narrowed onto the
  function-name token, so the squiggle marks the definition rather than
  every line. Diagnostics that do not start on a `def` line keep their
  reported range, so any finer span polypolarism emits later renders as-is.
- Typed return-column mismatches (`pple-return-type`) now point at the precise
  inferred-side expression polypolarism reports (per-column spans, issue
  #110) instead of the whole function, and their `declared here` schema
  location is surfaced as LSP **related information** (visible in the
  Problems panel and on the diagnostic). The `related` array is read
  additively, so diagnostics without one are unaffected.
- **QuickFix code actions** (D-11b): the lightbulb now offers concrete
  edits for polypolarism diagnostics.
  - `pple-undeclared-column` ("column not declared in schema `S`"): rewrite
    the offending `DataFrame[S]` / `LazyFrame[S]` parameter annotation to a
    bare `pl.DataFrame` / `pl.LazyFrame` (a row-polymorphic helper).
  - `pple-return-type` typed return-column mismatch: rewrite the
    already-declared schema field to the inferred dtype (e.g. `total: int` →
    `total: pl.Float64`), located via the diagnostic's same-file
    `declared here` related entry.
  - `pple-return-type` undeclared extra return column ("Extra column `X` of type
    `T`"): declare the column on the strict return schema (insert
    `X: pl.T` at the end of the schema body).
  Diagnostic operands are read from the structured fields polypolarism now
  stamps on each diagnostic (`column_name` / `schema` / `declared_type` /
  `inferred_type`, carried through LSP `Diagnostic.data`), with message
  parsing only as a fallback. Edit targets (the parameter annotation, the
  schema class/field) are located by parsing the document with `ast`, so
  ranges are exact; when an edit cannot be resolved unambiguously (no
  polars import, cross-file schema, undeclared column with unknown dtype,
  complex dtype) no action is offered rather than risking a wrong edit.
  The retype fix now consumes polypolarism's `suggested_annotation` +
  `declared_annotation_range` (issue #113) so complex dtypes (e.g.
  `pl.List(pl.Int64)`) are handled, and the `pple-undeclared-column`
  "declare the column" fix is now offered whenever the column's dtype is
  statically known —
  e.g. pinned by `.cast(T)` — via `fix.suggested_dtype` (issue #114).
- **Column rename** (D-11b): `textDocument/rename` (with `prepareRename`)
  renames a Polars column across its schema-field declaration and every
  `pl.col("...")` reference that polypolarism proves refers to the same
  `(schema, column)`, via the `--rename-targets FILE:LINE:COL` query mode.
  Only proven occurrences are rewritten, and new names that are not valid
  Python identifiers are rejected (the schema field is renamed too).
  - **Cross-file**: references in other files are followed. The edit is
    returned as `documentChanges` with `changeAnnotations`; edits outside
    the active file are grouped under a confirmation-required annotation,
    so the editor's refactor preview makes the multi-file effect explicit
    and the user reviews before applying.
  - When the active buffer matches disk, the real file is queried so the
    project-wide scan can resolve cross-file references; with unsaved
    edits the query falls back to the live buffer (single-document only),
    so no edit is ever derived from stale on-disk content.
  - If another involved file is open with unsaved edits that moved the
    column (so the disk-based scan would be stale for it), the rename is
    refused with a message to save that file first, rather than applying
    a stale edit. Files that are not open take the edit on disk exactly
    as scanned.
- Multi-file JSON output: the per-diagnostic `file` field is respected,
  so diagnostics are never attributed to the wrong document.
- Parse/read failures (now emitted by the CLI as failing CheckResults,
  e.g. `SyntaxError`) surface as uncoded error diagnostics.
- README rewritten for the Pandera `DataFrameModel` schema declaration
  (the legacy `DF["{...}"]` DSL was removed from polypolarism) and the
  supported-version window (Polars 1.37+, Pandera 0.19+).
- Python LSP tests replaced the generator-template examples with a real
  polypolarism end-to-end check (one `pple-undeclared-column` error, one
  `pplw-unmodeled-method` warning).
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
  (`7faf639`). **Breaking upstream change:** diagnostic codes moved from
  numeric `PLY###` / `PLW###` to semantic slugs — errors `pple-<slug>`,
  warnings `pplw-<slug>` (e.g. `pple-return-type`, `pple-undeclared-column`,
  `pplw-unmodeled-method`, `pplw-unsupported-version`; the several
  column-not-found codes collapsed into one `pple-column-not-found`). The
  `--format json` / `--rename-targets` contract, messages, severities, and
  fix metadata are otherwise unchanged. The server's diagnostic-code
  extraction regex only matched the old numeric form, so with slugs it
  returned no code and **silently disabled every QuickFix** (they are
  guarded on the diagnostic code) and dropped the Problems-panel code
  links — now fixed (slug-aware regex, and warning/error classification by
  the `pplw` prefix). Code-reference links repoint to polypolarism's
  `docs/diagnostics.md` (upstream moved the code tables out of its README);
  that reference also documents the numeric→slug legacy mapping. The
  earlier `022c621` sync's additions (analyzer fixes for issues #95–#108,
  `# type: ignore[...]` diagnostic suppression, and the `typing.cast`
  schema-assertion warning) remain.

## 0.1.0

- Initial preview release.
