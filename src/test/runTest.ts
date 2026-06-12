// Entry point for `npm test`: downloads VS Code, installs the
// ms-python.python dependency into the test instance, and runs the
// mocha suite from ./suite against a workspace that contains a .py
// file (so the onLanguage/workspaceContains activation events fire).
import * as cp from 'child_process';
import * as path from 'path';
import {
    downloadAndUnzipVSCode,
    resolveCliArgsFromVSCodeExecutablePath,
    runTests,
} from '@vscode/test-electron';

async function main(): Promise<void> {
    try {
        const extensionDevelopmentPath = path.resolve(__dirname, '../../');
        const extensionTestsPath = path.resolve(__dirname, './suite/index');
        const testWorkspace = path.resolve(
            extensionDevelopmentPath,
            'src',
            'test',
            'python_tests',
            'test_data',
            'sample1',
        );

        const vscodeExecutablePath = await downloadAndUnzipVSCode();
        const [cliPath, ...cliArgs] = resolveCliArgsFromVSCodeExecutablePath(vscodeExecutablePath);

        // The extension declares ms-python.python in extensionDependencies;
        // without it the test instance cannot even resolve the extension.
        cp.spawnSync(cliPath, [...cliArgs, '--install-extension', 'ms-python.python'], {
            encoding: 'utf-8',
            stdio: 'inherit',
        });

        await runTests({
            vscodeExecutablePath,
            extensionDevelopmentPath,
            extensionTestsPath,
            launchArgs: [testWorkspace],
        });
    } catch (err) {
        console.error('Failed to run tests', err);
        process.exit(1);
    }
}

main();
