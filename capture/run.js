// Automated demo-GIF capture runner (macOS).
// Copies docs/demo-workspace into a temp dir seeded with a clean
// .vscode/settings.json (interpreter pinned BEFORE activation so exactly one
// server starts; Pylance/git-popup/chat/minimap off), launches a real VS Code
// with the extension loaded, drives it through the feature scenes, and grabs
// one full-screen screenshot per scene via `screencapture`. Frames land in
// $PLY_FRAMES (default /tmp/ply-frames); assemble with capture/make-gif.sh.
const path = require('path');
const cp = require('child_process');
const fs = require('fs');
const {
    runTests,
    downloadAndUnzipVSCode,
    resolveCliArgsFromVSCodeExecutablePath,
} = require('@vscode/test-electron');

async function main() {
    const repoRoot = path.resolve(__dirname, '..');
    const extensionDevelopmentPath = repoRoot;
    const extensionTestsPath = path.resolve(__dirname, 'suite.js');
    const srcWorkspace = path.resolve(repoRoot, 'docs', 'demo-workspace');

    const framesDir = process.env.PLY_FRAMES || '/tmp/ply-frames';
    fs.rmSync(framesDir, { recursive: true, force: true });
    fs.mkdirSync(framesDir, { recursive: true });

    const venvPython = path.resolve(repoRoot, '.venv', 'bin', 'python');

    // Build a throwaway copy of the workspace with seeded settings so nothing
    // machine-specific ever touches the committed docs/demo-workspace.
    const workspaceRaw = process.env.PLY_WORKSPACE || '/tmp/ply-workspace';
    fs.rmSync(workspaceRaw, { recursive: true, force: true });
    fs.cpSync(srcWorkspace, workspaceRaw, { recursive: true });
    // Launch on the REAL path (/tmp -> /private/tmp on macOS) so the URIs VS
    // Code uses match polypolarism's realpath'd rename-target output; otherwise
    // cross-file edits land on a phantom second document.
    const workspace = fs.realpathSync(workspaceRaw);
    fs.rmSync(path.join(workspace, 'README.md'), { force: true }); // storyboard, not demo content
    fs.mkdirSync(path.join(workspace, '.vscode'), { recursive: true });
    fs.writeFileSync(
        path.join(workspace, '.vscode', 'settings.json'),
        JSON.stringify(
            {
                'polypolarism.interpreter': [venvPython],
                'polypolarism.importStrategy': 'useBundled',
                'python.languageServer': 'None', // silence Pylance import noise
                'git.openRepositoryInParentFolders': 'never',
                'window.zoomLevel': 1,
                'workbench.colorTheme': 'Default Dark Modern',
                'editor.minimap.enabled': false,
                'chat.commandCenter.enabled': false,
                'workbench.startupEditor': 'none',
                'telemetry.telemetryLevel': 'off',
            },
            null,
            2,
        ),
    );

    const vscodeExecutablePath = await downloadAndUnzipVSCode();
    const [cli, ...args] = resolveCliArgsFromVSCodeExecutablePath(vscodeExecutablePath);
    // The extension declares ms-python.python in extensionDependencies.
    cp.spawnSync(cli, [...args, '--install-extension', 'ms-python.python'], {
        encoding: 'utf-8',
        stdio: 'inherit',
    });

    await runTests({
        vscodeExecutablePath,
        extensionDevelopmentPath,
        extensionTestsPath,
        // --locale=en forces the VS Code UI to English regardless of the host
        // system locale, so the demo panes/menus aren't localized.
        launchArgs: [workspace, '--disable-workspace-trust', '--locale=en'],
        extensionTestsEnv: {
            PLY_FRAMES: framesDir,
            PLY_WORKSPACE: workspace,
            PLY_PYTHON: venvPython,
        },
    });

    console.log(`\nFrames written to ${framesDir}`);
    for (const f of fs.readdirSync(framesDir).sort()) {
        console.log('  ' + f);
    }
}

main().catch((err) => {
    console.error('capture run failed:', err);
    process.exit(1);
});
