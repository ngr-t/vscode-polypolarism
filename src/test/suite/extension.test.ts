import * as assert from 'assert';
import * as vscode from 'vscode';

const EXTENSION_ID = 't-negoro.polypolarism';

suite('Extension smoke', () => {
    test('is resolvable in the test instance', () => {
        const ext = vscode.extensions.getExtension(EXTENSION_ID);
        assert.ok(ext, `${EXTENSION_ID} not found — extensionDependencies unresolved?`);
    });

    test('activates', async function () {
        this.timeout(120_000);
        const ext = vscode.extensions.getExtension(EXTENSION_ID);
        assert.ok(ext);
        await ext.activate();
        assert.strictEqual(ext.isActive, true);
    });

    test('contributes the restart command', async function () {
        this.timeout(120_000);
        const ext = vscode.extensions.getExtension(EXTENSION_ID);
        assert.ok(ext);
        await ext.activate();
        const commands = await vscode.commands.getCommands(true);
        assert.ok(
            commands.includes('polypolarism.restart'),
            'polypolarism.restart is not registered',
        );
    });
});
