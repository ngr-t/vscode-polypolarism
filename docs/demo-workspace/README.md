# Demo workspace — recording storyboard

This folder is the workspace recorded for the README demo GIF
([`docs/demo.gif`](../demo.gif)). It is intentionally tiny — two files, one
checked function — so a single ~25-second take exercises all four headline
features without scrolling.

Open this folder in the **Extension Development Host** (VS Code → `F5` →
*Debug Extension and Python*) so the local build of the extension is active.
See [`../RECORDING.md`](../RECORDING.md) for capture + GIF-conversion steps.

## The files

- **`schema.py`** — `Sales(amount: pl.Float64, region: str)`. The `amount`
  field (line 6) is the column we rename in Scene 4.
- **`pipeline.py`** — imports `Sales`, declares `Taxed` (same file, so the
  retype QuickFix can edit it), and defines `with_tax`. The return expression
  on **line 15** aliases a `Float64` value to `tax`, but `Taxed.tax` is
  declared `pl.Int64` (line 11) → a typed return-column mismatch.

Leave both files in their committed (error) state before recording — the take
starts from the red squiggle. Discard any edits afterward (`git restore
docs/demo-workspace`) so the fixtures stay pristine.

## Storyboard (~25s, one take)

All line/column anchors below are verified against the bundled polypolarism
(`pple-*` slug codes).

### Scene 1 — Diagnostics (~6s)
1. Open `pipeline.py`. A red squiggle sits on the return expression
   (**line 15**); the **Problems** panel shows
   `[pple-return-type] Column 'tax' has type Float64, but declared type is Int64`.
2. Hover the squiggle → the message plus the **`declared here`** related link
   (points at `Taxed.tax`, line 11). Click it to show it jumps to the
   declaration.

### Scene 2 — Schema hover (~6s)
3. Hover the `with_tax` name (**line 14**). The hover shows polypolarism's view:
   the `df` parameter frame and the **declared vs inferred** return frames —
   declared `tax: Int64`, inferred `tax: Float64` (an `...` marks open frames).

### Scene 3 — QuickFix (~6s)
4. Put the cursor on the line-15 squiggle, open the lightbulb (`Cmd .`).
5. Choose **`[pple-return-type] declared type -> pl.Float64 (match inferred)`**.
   The annotation on line 11 flips `pl.Int64 → pl.Float64` and the squiggle
   clears.

### Scene 4 — Cross-file column rename (~7s)
6. In `schema.py`, put the cursor on **`amount`** (**line 6**) and press `F2`.
   Type the new name, e.g. `revenue`.
7. The refactor preview opens. It rewrites the field declaration in `schema.py`
   **and** the `pl.col("amount")` reference in `pipeline.py` (line 15). The
   edit in `pipeline.py` — the file you did *not* trigger from — is grouped
   under a confirmation heading, so the multi-file effect is explicit.
8. Apply. Both files update; `amount` becomes `revenue` everywhere
   polypolarism can prove the same `(Sales, amount)` origin (the unrelated
   `Taxed.amount` is left untouched).

## Tips for a clean frame
- High-contrast theme (Default Dark Modern / Light+), editor font ~15px.
- Hide the minimap and any noisy panels; keep the **Problems** panel visible
  for Scene 1.
- Move the mouse deliberately and pause ~1s on each tooltip so the GIF reads.
