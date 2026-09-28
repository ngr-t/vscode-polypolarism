// Flat config for ESLint 10 — eslintrc files (`.eslintrc.json`) are no longer
// read as of ESLint 10, so the rules below are the former .eslintrc.json.
import tsParser from '@typescript-eslint/parser';
import tsPlugin from '@typescript-eslint/eslint-plugin';

export default [
    {
        ignores: ['out/**', 'dist/**', 'bundled/**', '.vscode-test/**', '**/*.d.ts'],
    },
    {
        files: ['**/*.ts'],
        languageOptions: {
            parser: tsParser,
            ecmaVersion: 2020,
            sourceType: 'module',
        },
        plugins: {
            '@typescript-eslint': tsPlugin,
        },
        rules: {
            '@typescript-eslint/naming-convention': 'warn',
            curly: 'warn',
            eqeqeq: 'warn',
            'no-throw-literal': 'warn',
            semi: 'warn',
        },
    },
];
