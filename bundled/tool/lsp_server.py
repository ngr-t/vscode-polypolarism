# Copyright (c) Microsoft Corporation. All rights reserved.
# Copyright (c) 2025 Tetsuya NEGORO. All rights reserved.
# Licensed under the MIT License.
"""Implementation of polypolarism support over LSP."""
from __future__ import annotations

import copy
import json
import os
import pathlib
import re
import sys
import traceback
from typing import Any, Optional, Sequence


# **********************************************************
# Update sys.path before importing any bundled libraries.
# **********************************************************
def update_sys_path(path_to_add: str, strategy: str) -> None:
    """Add given path to `sys.path`."""
    if path_to_add not in sys.path and os.path.isdir(path_to_add):
        if strategy == "useBundled":
            sys.path.insert(0, path_to_add)
        elif strategy == "fromEnvironment":
            sys.path.append(path_to_add)


# Ensure that we can import LSP libraries, and other bundled libraries.
update_sys_path(
    os.fspath(pathlib.Path(__file__).parent.parent / "libs"),
    os.getenv("LS_IMPORT_STRATEGY", "useBundled"),
)

# **********************************************************
# Imports needed for the language server goes below this.
# **********************************************************
# pylint: disable=wrong-import-position,import-error
import lsp_jsonrpc as jsonrpc
import lsp_utils as utils
import lsprotocol.types as lsp
from pygls import uris
from pygls.lsp.server import LanguageServer
from pygls.workspace import TextDocument

WORKSPACE_SETTINGS = {}
GLOBAL_SETTINGS = {}
RUNNER = pathlib.Path(__file__).parent / "lsp_runner.py"

MAX_WORKERS = 5
LSP_SERVER = LanguageServer(
    name="Polypolarism", version="0.1.0", max_workers=MAX_WORKERS
)


# **********************************************************
# Tool specific configuration
# **********************************************************
TOOL_MODULE = "polypolarism"
TOOL_DISPLAY = "Polypolarism"
# Use JSON output format for easy parsing
TOOL_ARGS = ["--format", "json"]

# polypolarism tags each diagnostic message with a stable `[PLY###]` (error)
# or `[PLW###]` (warning) prefix. Extract it into the LSP `code` field.
DIAGNOSTIC_CODE_RE = re.compile(r"^\[(PL[YW]\d{3})\]\s*")

# README anchors for the diagnostic-code tables (PLY### / PLW###).
ERROR_CODES_HREF = "https://github.com/ngr-t/polypolarism#diagnostic-codes"
WARNING_CODES_HREF = (
    "https://github.com/ngr-t/polypolarism#apply-style-helpers-and-warning-codes"
)


# **********************************************************
# Linting features
# **********************************************************

@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
def did_open(params: lsp.DidOpenTextDocumentParams) -> None:
    """LSP handler for textDocument/didOpen request."""
    document = LSP_SERVER.workspace.text_documents.get(params.text_document.uri)
    diagnostics: list[lsp.Diagnostic] = _linting_helper(document)
    # pygls 2.0: takes PublishDiagnosticsParams object
    LSP_SERVER.text_document_publish_diagnostics(
        lsp.PublishDiagnosticsParams(uri=document.uri, diagnostics=diagnostics)
    )


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_DID_SAVE)
def did_save(params: lsp.DidSaveTextDocumentParams) -> None:
    """LSP handler for textDocument/didSave request."""
    document = LSP_SERVER.workspace.text_documents.get(params.text_document.uri)
    diagnostics: list[lsp.Diagnostic] = _linting_helper(document)
    # pygls 2.0: takes PublishDiagnosticsParams object
    LSP_SERVER.text_document_publish_diagnostics(
        lsp.PublishDiagnosticsParams(uri=document.uri, diagnostics=diagnostics)
    )


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_DID_CLOSE)
def did_close(params: lsp.DidCloseTextDocumentParams) -> None:
    """LSP handler for textDocument/didClose request."""
    document = LSP_SERVER.workspace.text_documents.get(params.text_document.uri)
    # Publishing empty diagnostics to clear the entries for this file.
    # pygls 2.0: takes PublishDiagnosticsParams object
    LSP_SERVER.text_document_publish_diagnostics(
        lsp.PublishDiagnosticsParams(uri=document.uri, diagnostics=[])
    )


def _linting_helper(document: TextDocument) -> list[lsp.Diagnostic]:
    """Run polypolarism and parse JSON output."""
    result = _run_tool_on_document(document)
    if result and result.stdout:
        return _parse_json_output(result.stdout, document.path)
    return []


def _split_code(message: str) -> tuple[Optional[str], str]:
    """Split the `[PLY###]` / `[PLW###]` prefix off a diagnostic message.

    Returns ``(code, message)``; ``code`` is ``None`` for untagged
    diagnostics (e.g. parse / read failures reported as SyntaxError).
    """
    match = DIAGNOSTIC_CODE_RE.match(message)
    if match is None:
        return None, message
    return match.group(1), message[match.end() :]


def _code_description(code: Optional[str]) -> Optional[lsp.CodeDescription]:
    """Link a diagnostic code to its table in the polypolarism README."""
    if code is None:
        return None
    if code.startswith("PLW"):
        return lsp.CodeDescription(href=WARNING_CODES_HREF)
    return lsp.CodeDescription(href=ERROR_CODES_HREF)


def _to_range(diag_data: dict) -> lsp.Range:
    """Build the LSP range from a polypolarism JSON diagnostic."""
    # polypolarism uses 1-indexed lines, LSP uses 0-indexed
    line = max(diag_data.get("line", 1) - 1, 0)
    column = diag_data.get("column", 0)
    # Use end_line if available, otherwise use same line
    end_line = diag_data.get("end_line")
    if end_line is not None:
        end_line = max(end_line - 1, 0)
    else:
        end_line = line
    end_column = diag_data.get("end_column", 0)
    return lsp.Range(
        start=lsp.Position(line=line, character=column),
        end=lsp.Position(line=end_line, character=end_column),
    )


def _parse_json_output(content: str, document_path: str) -> list[lsp.Diagnostic]:
    """Parse polypolarism JSON output into LSP diagnostics."""
    diagnostics: list[lsp.Diagnostic] = []

    try:
        data = json.loads(content)
        for diag_data in data.get("diagnostics", []):
            # Each diagnostic carries its own `file` field (multi-file JSON
            # output). We lint one document at a time; never attribute a
            # diagnostic from another file to this document.
            diag_file = diag_data.get("file")
            if diag_file is not None and not utils.is_same_path(
                diag_file, document_path
            ):
                log_to_output(
                    f"Skipping diagnostic for other file {diag_file!r} "
                    f"while linting {document_path!r}."
                )
                continue

            code, message = _split_code(diag_data.get("message", "Unknown error"))

            diagnostic = lsp.Diagnostic(
                range=_to_range(diag_data),
                message=message,
                severity=_get_severity(diag_data.get("severity", "error")),
                code=code,
                code_description=_code_description(code),
                source=TOOL_MODULE,
            )
            diagnostics.append(diagnostic)
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse polypolarism output: {e}")
    except Exception as e:
        log_error(f"Error processing diagnostics: {e}")

    return diagnostics


def _get_severity(severity_str: str) -> lsp.DiagnosticSeverity:
    """Convert severity string to LSP DiagnosticSeverity."""
    severity_map = {
        "error": lsp.DiagnosticSeverity.Error,
        "warning": lsp.DiagnosticSeverity.Warning,
        "info": lsp.DiagnosticSeverity.Information,
        "hint": lsp.DiagnosticSeverity.Hint,
    }
    return severity_map.get(severity_str.lower(), lsp.DiagnosticSeverity.Error)


# **********************************************************
# Required Language Server Initialization and Exit handlers.
# **********************************************************
@LSP_SERVER.feature(lsp.INITIALIZE)
def initialize(params: lsp.InitializeParams) -> None:
    """LSP handler for initialize request."""
    log_to_output(f"CWD Server: {os.getcwd()}")

    paths = "\r\n   ".join(sys.path)
    log_to_output(f"sys.path used to run Server:\r\n   {paths}")

    GLOBAL_SETTINGS.update(**params.initialization_options.get("globalSettings", {}))

    settings = params.initialization_options["settings"]
    _update_workspace_settings(settings)
    log_to_output(
        f"Settings used to run Server:\r\n{json.dumps(settings, indent=4, ensure_ascii=False)}\r\n"
    )
    log_to_output(
        f"Global settings:\r\n{json.dumps(GLOBAL_SETTINGS, indent=4, ensure_ascii=False)}\r\n"
    )


@LSP_SERVER.feature(lsp.EXIT)
def on_exit(_params: Optional[Any] = None) -> None:
    """Handle clean up on exit."""
    jsonrpc.shutdown_json_rpc()


@LSP_SERVER.feature(lsp.SHUTDOWN)
def on_shutdown(_params: Optional[Any] = None) -> None:
    """Handle clean up on shutdown."""
    jsonrpc.shutdown_json_rpc()


def _get_global_defaults():
    return {
        "path": GLOBAL_SETTINGS.get("path", []),
        "interpreter": GLOBAL_SETTINGS.get("interpreter", [sys.executable]),
        "args": GLOBAL_SETTINGS.get("args", []),
        "importStrategy": GLOBAL_SETTINGS.get("importStrategy", "useBundled"),
        "showNotifications": GLOBAL_SETTINGS.get("showNotifications", "off"),
    }


def _update_workspace_settings(settings):
    if not settings:
        key = os.getcwd()
        WORKSPACE_SETTINGS[key] = {
            "cwd": key,
            "workspaceFS": key,
            "workspace": uris.from_fs_path(key),
            **_get_global_defaults(),
        }
        return

    for setting in settings:
        key = uris.to_fs_path(setting["workspace"])
        WORKSPACE_SETTINGS[key] = {
            "cwd": key,
            **setting,
            "workspaceFS": key,
        }


def _get_settings_by_path(file_path: pathlib.Path):
    workspaces = {s["workspaceFS"] for s in WORKSPACE_SETTINGS.values()}

    while file_path != file_path.parent:
        str_file_path = str(file_path)
        if str_file_path in workspaces:
            return WORKSPACE_SETTINGS[str_file_path]
        file_path = file_path.parent

    setting_values = list(WORKSPACE_SETTINGS.values())
    return setting_values[0]


def _get_document_key(document: TextDocument):
    if WORKSPACE_SETTINGS:
        document_workspace = pathlib.Path(document.path)
        workspaces = {s["workspaceFS"] for s in WORKSPACE_SETTINGS.values()}

        # Find workspace settings for the given file.
        while document_workspace != document_workspace.parent:
            if str(document_workspace) in workspaces:
                return str(document_workspace)
            document_workspace = document_workspace.parent

    return None


def _get_settings_by_document(document: TextDocument | None):
    if document is None or document.path is None:
        return list(WORKSPACE_SETTINGS.values())[0]

    key = _get_document_key(document)
    if key is None:
        # This is either a non-workspace file or there is no workspace.
        key = os.fspath(pathlib.Path(document.path).parent)
        return {
            "cwd": key,
            "workspaceFS": key,
            "workspace": uris.from_fs_path(key),
            **_get_global_defaults(),
        }

    return WORKSPACE_SETTINGS[str(key)]


# *****************************************************
# Internal execution APIs.
# *****************************************************
def _run_tool_on_document(
    document: TextDocument,
    use_stdin: bool = False,
    extra_args: Optional[Sequence[str]] = None,
) -> utils.RunResult | None:
    """Runs polypolarism on the given document."""
    if extra_args is None:
        extra_args = []
    if str(document.uri).startswith("vscode-notebook-cell"):
        # Skip notebook cells
        return None

    if utils.is_stdlib_file(document.path):
        # Skip standard library python files.
        return None

    # deep copy here to prevent accidentally updating global settings.
    settings = copy.deepcopy(_get_settings_by_document(document))

    code_workspace = settings["workspaceFS"]
    cwd = settings["cwd"]

    use_path = False
    use_rpc = False
    if settings["path"]:
        # 'path' setting takes priority over everything.
        use_path = True
        argv = settings["path"]
    elif settings["interpreter"] and not utils.is_current_interpreter(
        settings["interpreter"][0]
    ):
        # If there is a different interpreter set use JSON-RPC to the subprocess
        # running under that interpreter.
        argv = [TOOL_MODULE]
        use_rpc = True
    else:
        # if the interpreter is same as the interpreter running this
        # process then run as module.
        argv = [TOOL_MODULE]

    argv += TOOL_ARGS + settings["args"] + extra_args
    argv += [document.path]

    if use_path:
        # This mode is used when running executables.
        log_to_output(" ".join(argv))
        log_to_output(f"CWD Server: {cwd}")
        result = utils.run_path(
            argv=argv,
            use_stdin=use_stdin,
            cwd=cwd,
            source=document.source.replace("\r\n", "\n"),
        )
        if result.stderr:
            log_to_output(result.stderr)
    elif use_rpc:
        # This mode is used if the interpreter running this server is different from
        # the interpreter used for running this server.
        log_to_output(" ".join(settings["interpreter"] + ["-m"] + argv))
        log_to_output(f"CWD Linter: {cwd}")

        result = jsonrpc.run_over_json_rpc(
            workspace=code_workspace,
            interpreter=settings["interpreter"],
            module=TOOL_MODULE,
            argv=argv,
            use_stdin=use_stdin,
            cwd=cwd,
            source=document.source,
        )
        if result.exception:
            log_error(result.exception)
            result = utils.RunResult(result.stdout, result.stderr)
        elif result.stderr:
            log_to_output(result.stderr)
    else:
        # In this mode the tool is run as a module in the same process as the language server.
        log_to_output(" ".join([sys.executable, "-m"] + argv))
        log_to_output(f"CWD Linter: {cwd}")
        # This is needed to preserve sys.path, in cases where the tool modifies
        # sys.path and that might not work for this scenario next time around.
        with utils.substitute_attr(sys, "path", sys.path[:]):
            try:
                result = utils.run_module(
                    module=TOOL_MODULE,
                    argv=argv,
                    use_stdin=use_stdin,
                    cwd=cwd,
                    source=document.source,
                )
            except Exception:
                log_error(traceback.format_exc(chain=True))
                raise
        if result.stderr:
            log_to_output(result.stderr)

    log_to_output(f"{document.uri} :\r\n{result.stdout}")
    return result


# *****************************************************
# Logging and notification.
# *****************************************************
def log_to_output(
    message: str, msg_type: lsp.MessageType = lsp.MessageType.Log
) -> None:
    # pygls 2.0: takes LogMessageParams(type, message)
    LSP_SERVER.window_log_message(lsp.LogMessageParams(type=msg_type, message=message))


def log_error(message: str) -> None:
    LSP_SERVER.window_log_message(
        lsp.LogMessageParams(type=lsp.MessageType.Error, message=message)
    )
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["onError", "onWarning", "always"]:
        LSP_SERVER.window_show_message(
            lsp.ShowMessageParams(type=lsp.MessageType.Error, message=message)
        )


def log_warning(message: str) -> None:
    LSP_SERVER.window_log_message(
        lsp.LogMessageParams(type=lsp.MessageType.Warning, message=message)
    )
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["onWarning", "always"]:
        LSP_SERVER.window_show_message(
            lsp.ShowMessageParams(type=lsp.MessageType.Warning, message=message)
        )


def log_always(message: str) -> None:
    LSP_SERVER.window_log_message(
        lsp.LogMessageParams(type=lsp.MessageType.Info, message=message)
    )
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["always"]:
        LSP_SERVER.window_show_message(
            lsp.ShowMessageParams(type=lsp.MessageType.Info, message=message)
        )


# *****************************************************
# Start the server.
# *****************************************************
if __name__ == "__main__":
    LSP_SERVER.start_io()
