// Runs INSIDE the VS Code extension host (loaded by @vscode/test-electron as
// extensionTestsPath). Drives the demo workspace through the feature scenes
// and grabs one full-screen screenshot per scene via `screencapture`.
// Config (interpreter, Pylance off, etc.) is seeded into the workspace's
// .vscode/settings.json by run.js BEFORE activation, so the server starts once.
const vscode = require('vscode');
const path = require('path');
const cp = require('child_process');

const FRAMES = process.env.PLY_FRAMES;
const WORKSPACE = process.env.PLY_WORKSPACE;
const PIPELINE = vscode.Uri.file(path.join(WORKSPACE, 'pipeline.py'));
const SCHEMA = vscode.Uri.file(path.join(WORKSPACE, 'schema.py'));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function waitFor(fn, timeoutMs, label) {
    const start = Date.now();
    for (;;) {
        try {
            if (await fn()) return;
        } catch (_) {
            /* keep polling */
        }
        if (Date.now() - start > timeoutMs) throw new Error(`timeout: ${label} (${timeoutMs}ms)`);
        await sleep(300);
    }
}

function windowId() {
    try {
        const out = cp
            .execFileSync(process.env.PLY_PYTHON || 'python3', [path.join(__dirname, 'windowid.py')], {
                encoding: 'utf8',
            })
            .trim();
        return out ? parseInt(out, 10) : null;
    } catch (_) {
        return null;
    }
}

async function snap(name) {
    // Dismiss any transient notification toasts so they don't sit in the frame.
    try {
        await vscode.commands.executeCommand('notifications.clearAll');
    } catch (_) {
        /* command may be unavailable */
    }
    await sleep(150);
    const out = path.join(FRAMES, name);
    const wid = windowId();
    // -l <id> grabs exactly the VS Code window (no desktop, Space-independent);
    // fall back to full screen if the window can't be located.
    if (wid) {
        cp.execFileSync('screencapture', ['-x', '-o', '-l', String(wid), out]);
    } else {
        cp.execFileSync('screencapture', ['-x', '-o', out]);
    }
    console.log('snap ->', name, wid ? `(window ${wid})` : '(full screen)');
}

async function open(uri) {
    const doc = await vscode.workspace.openTextDocument(uri);
    const editor = await vscode.window.showTextDocument(doc, { preview: false });
    return { doc, editor };
}

async function closeReset(uri) {
    await vscode.commands.executeCommand('workbench.action.closeAllEditors');
    await vscode.commands.executeCommand('workbench.action.closePanel');
    await sleep(400);
    const ctx = await open(uri);
    await vscode.commands.executeCommand('workbench.action.focusActiveEditorGroup');
    await sleep(500);
    return ctx;
}

function posOf(doc, needle, inner) {
    const text = doc.getText();
    const base = text.indexOf(needle);
    if (base < 0) throw new Error(`not found: ${needle}`);
    return doc.positionAt(base + (inner ? needle.indexOf(inner) : 0));
}

async function run() {
    try {
        // Chat/agent lives in the secondary side bar — close it for a clean shot.
        await vscode.commands.executeCommand('workbench.action.closeAuxiliaryBar');

        const ext = vscode.extensions.getExtension('t-negoro.polypolarism');
        await ext.activate();

        await open(PIPELINE);
        await waitFor(
            () => vscode.languages.getDiagnostics(PIPELINE).length > 0,
            90_000,
            'diagnostics',
        );
        console.log(
            'diagnostics:',
            vscode.languages.getDiagnostics(PIPELINE).map((d) => d.code && d.code.value),
        );

        // ---------- Scene 1: diagnostics + Problems panel ----------
        {
            await closeReset(PIPELINE);
            await vscode.commands.executeCommand('workbench.actions.view.problems');
            await sleep(1200);
            await snap('01-diagnostics.png');
        }

        // ---------- Scene 2: schema hover ----------
        {
            const { doc, editor } = await closeReset(PIPELINE);
            const pos = posOf(doc, 'def with_tax', 'with_tax');
            editor.selection = new vscode.Selection(pos, pos);
            editor.revealRange(new vscode.Range(pos, pos));
            await sleep(300);
            await vscode.commands.executeCommand('editor.action.showHover');
            await sleep(1200);
            await snap('02-hover.png');
        }

        // ---------- Scene 3: cross-file column rename (amount -> revenue) ----------
        // Compute the rename edit from the Sales.amount declaration and apply it
        // to the in-memory buffers of BOTH files shown side by side, so the shot
        // proves the cross-file effect. Buffers are unsaved; the throwaway
        // workspace is discarded after the run, so disk is never touched.
        {
            await closeReset(SCHEMA);
            const sdoc = await vscode.workspace.openTextDocument(SCHEMA);
            const pdoc = await vscode.workspace.openTextDocument(PIPELINE);
            const pos = posOf(sdoc, 'amount: pl.Float64', 'amount');
            const edit = await vscode.commands.executeCommand(
                'vscode.executeDocumentRenameProvider',
                SCHEMA,
                pos,
                'revenue',
            );
            console.log('rename edit files:', edit && edit.size);

            // Apply while no editors are open (avoids a visible-editor render
            // race), then show both files so the cross-file effect is on screen.
            await vscode.commands.executeCommand('workbench.action.closeAllEditors');
            await vscode.commands.executeCommand('workbench.action.closePanel');
            if (edit) await vscode.workspace.applyEdit(edit);
            await sleep(400);
            await vscode.window.showTextDocument(pdoc, {
                viewColumn: vscode.ViewColumn.One,
                preview: false,
            });
            await vscode.window.showTextDocument(sdoc, {
                viewColumn: vscode.ViewColumn.Two,
                preview: false,
            });
            await sleep(1000);
            await snap('03-rename.png');
        }

        // ---------- Scene 4: QuickFix lightbulb (last: menu is sticky) ----------
        {
            const { editor } = await closeReset(PIPELINE);
            const diag = vscode.languages.getDiagnostics(PIPELINE)[0];
            editor.selection = new vscode.Selection(diag.range.start, diag.range.start);
            editor.revealRange(diag.range);
            await sleep(300);
            await vscode.commands.executeCommand('editor.action.quickFix');
            await sleep(1400);
            await snap('04-quickfix.png');
        }

        await sleep(400);
        console.log('capture complete');
    } catch (err) {
        console.error('CAPTURE ERROR:', err && err.stack ? err.stack : err);
        try {
            snap('99-error-state.png');
        } catch (_) {}
        throw err;
    }
}

module.exports = { run };
