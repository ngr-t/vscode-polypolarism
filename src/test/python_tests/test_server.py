# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Test for linting over LSP.
"""

from threading import Event

from hamcrest import assert_that, is_

from .lsp_test_client import constants, defaults, session, utils

TEST_FILE_PATH = constants.TEST_DATA / "sample1" / "sample.py"
TEST_FILE_URI = utils.as_uri(str(TEST_FILE_PATH))
TEST_FILE2_PATH = constants.TEST_DATA / "sample2" / "sample.py"
TEST_FILE2_URI = utils.as_uri(str(TEST_FILE2_PATH))
TEST_FILE3_PATH = constants.TEST_DATA / "sample3" / "sample.py"
TEST_FILE3_URI = utils.as_uri(str(TEST_FILE3_PATH))
TEST_FILE4_PATH = constants.TEST_DATA / "sample4" / "sample.py"
TEST_FILE4_URI = utils.as_uri(str(TEST_FILE4_PATH))
TEST_FILE5_PATH = constants.TEST_DATA / "sample5" / "sample.py"
TEST_FILE5_URI = utils.as_uri(str(TEST_FILE5_PATH))
TIMEOUT = 30  # seconds


def _code_actions(ls_session, uri, contents, request_range):
    """Open `contents` and return the code actions over `request_range`."""
    done = Event()
    ls_session.set_notification_callback(
        session.PUBLISH_DIAGNOSTICS, lambda _params: done.set()
    )
    ls_session.notify_did_open(
        {
            "textDocument": {
                "uri": uri,
                "languageId": "python",
                "version": 1,
                "text": contents,
            }
        }
    )
    done.wait(TIMEOUT)
    return ls_session.text_document_code_action(
        {
            "textDocument": {"uri": uri},
            "range": request_range,
            "context": {"diagnostics": [], "only": ["quickfix"]},
        }
    )

ERROR_CODES_HREF = "https://github.com/ngr-t/polypolarism#diagnostic-codes"
WARNING_CODES_HREF = (
    "https://github.com/ngr-t/polypolarism#apply-style-helpers-and-warning-codes"
)


def test_linting_example():
    """Linting on file open: one PLY error and one PLW warning."""
    contents = TEST_FILE_PATH.read_text()

    actual = []
    with session.LspSession() as ls_session:
        ls_session.initialize(defaults.VSCODE_DEFAULT_INITIALIZE)

        done = Event()

        def _handler(params):
            nonlocal actual
            actual = params
            done.set()

        ls_session.set_notification_callback(session.PUBLISH_DIAGNOSTICS, _handler)

        ls_session.notify_did_open(
            {
                "textDocument": {
                    "uri": TEST_FILE_URI,
                    "languageId": "python",
                    "version": 1,
                    "text": contents,
                }
            }
        )

        # wait for some time to receive all notifications
        done.wait(TIMEOUT)

        # `[PLY###]` / `[PLW###]` message prefixes are extracted into the
        # diagnostic `code`; `severity` routes errors vs warnings; the
        # function-spanning range `--format json` reports is narrowed onto
        # the `def` name token so the squiggle marks the definition, not the
        # whole body (here `process` / `smooth` on their `def` lines).
        expected = {
            "uri": TEST_FILE_URI,
            "diagnostics": [
                {
                    "range": {
                        "start": {"line": 18, "character": 4},
                        "end": {"line": 18, "character": 11},
                    },
                    "message": (
                        "column 'amount' is not declared in schema "
                        "'InputSchema' — the (non-strict) schema admits "
                        "extra columns at runtime, but this function's "
                        "declaration does not promise it. Declare the column "
                        "on the schema, or take a bare pl.DataFrame parameter "
                        "for row-polymorphic helpers"
                    ),
                    "severity": 1,
                    "code": "PLY042",
                    "codeDescription": {"href": ERROR_CODES_HREF},
                    "source": "polypolarism",
                    "data": {"column_name": "amount", "schema": "InputSchema"},
                },
                {
                    "range": {
                        "start": {"line": 22, "character": 4},
                        "end": {"line": 22, "character": 10},
                    },
                    "message": (
                        "`.interpolate()` is not modeled by polypolarism — "
                        "the frame's schema is no longer tracked and downstream "
                        "checks go silent. Validate the result against a schema "
                        "(`Schema.validate(...)`) to keep checking precise."
                    ),
                    "severity": 2,
                    "code": "PLW007",
                    "codeDescription": {"href": WARNING_CODES_HREF},
                    "source": "polypolarism",
                },
            ],
        }

    assert_that(actual, is_(expected))


def test_schema_hover():
    """Hover inside a checked function shows polypolarism's schema view
    (D-11): parameter frames plus declared/inferred returns, sourced from
    the lint run's `functions` JSON summaries."""
    contents = TEST_FILE_PATH.read_text()

    with session.LspSession() as ls_session:
        ls_session.initialize(defaults.VSCODE_DEFAULT_INITIALIZE)

        done = Event()
        ls_session.set_notification_callback(
            session.PUBLISH_DIAGNOSTICS, lambda _params: done.set()
        )
        ls_session.notify_did_open(
            {
                "textDocument": {
                    "uri": TEST_FILE_URI,
                    "languageId": "python",
                    "version": 1,
                    "text": contents,
                }
            }
        )
        done.wait(TIMEOUT)

        # Line inside ``process`` (0-indexed): the return statement.
        lines = contents.splitlines()
        process_line = next(
            i for i, line in enumerate(lines) if line.startswith("def process")
        )
        hover = ls_session.text_document_hover(
            {
                "textDocument": {"uri": TEST_FILE_URI},
                "position": {"line": process_line + 1, "character": 4},
            }
        )

        assert_that(hover is not None, is_(True))
        value = hover["contents"]["value"]
        assert_that("process" in value, is_(True))
        assert_that("id: Int64" in value, is_(True))
        assert_that("declared return" in value, is_(True))
        assert_that("inferred return" in value, is_(True))

        # Hovering outside any function yields no hover.
        outside = ls_session.text_document_hover(
            {
                "textDocument": {"uri": TEST_FILE_URI},
                "position": {"line": 0, "character": 0},
            }
        )
        assert_that(outside is None, is_(True))


def test_typed_mismatch_related_information():
    """A typed return-column mismatch (PLY040) is reported with a precise
    inferred-side span and a `declared here` related location, sourced from
    polypolarism's per-column spans and `related` JSON (issue #110)."""
    contents = TEST_FILE2_PATH.read_text()

    actual = []
    with session.LspSession() as ls_session:
        ls_session.initialize(defaults.VSCODE_DEFAULT_INITIALIZE)

        done = Event()

        def _handler(params):
            nonlocal actual
            actual = params
            done.set()

        ls_session.set_notification_callback(session.PUBLISH_DIAGNOSTICS, _handler)
        ls_session.notify_did_open(
            {
                "textDocument": {
                    "uri": TEST_FILE2_URI,
                    "languageId": "python",
                    "version": 1,
                    "text": contents,
                }
            }
        )
        done.wait(TIMEOUT)

    diagnostics = actual["diagnostics"]
    assert_that(len(diagnostics), is_(1))
    diagnostic = diagnostics[0]
    assert_that(diagnostic["code"], is_("PLY040"))
    assert_that(diagnostic["severity"], is_(1))  # Error

    # Precise inferred-side span: the `pl.col("value").sum()` expression on the
    # return line (line 20, 1-indexed -> 19), not the whole function body.
    assert_that(
        diagnostic["range"],
        is_(
            {
                "start": {"line": 19, "character": 27},
                "end": {"line": 19, "character": 48},
            }
        ),
    )

    # `declared here` related location points at the schema field `total: int`
    # (line 16, 1-indexed -> 15) in the same document.
    related = diagnostic["relatedInformation"]
    assert_that(len(related), is_(1))
    assert_that(related[0]["message"], is_("declared here"))
    assert_that(related[0]["location"]["uri"], is_(TEST_FILE2_URI))
    assert_that(
        related[0]["location"]["range"],
        is_(
            {
                "start": {"line": 15, "character": 4},
                "end": {"line": 15, "character": 14},
            }
        ),
    )


def test_quickfix_bare_param():
    """QuickFix (D-11b): a PLY042 "column not declared in schema" diagnostic
    offers a code action that rewrites the offending `DataFrame[Schema]`
    parameter annotation to a bare `pl.DataFrame` (row-polymorphic helper)."""
    contents = TEST_FILE_PATH.read_text()

    with session.LspSession() as ls_session:
        ls_session.initialize(defaults.VSCODE_DEFAULT_INITIALIZE)

        done = Event()
        ls_session.set_notification_callback(
            session.PUBLISH_DIAGNOSTICS, lambda _params: done.set()
        )
        ls_session.notify_did_open(
            {
                "textDocument": {
                    "uri": TEST_FILE_URI,
                    "languageId": "python",
                    "version": 1,
                    "text": contents,
                }
            }
        )
        done.wait(TIMEOUT)

        # PLY042 is reported on the `process` def line (line 19, 1-indexed ->
        # 18). Request quick fixes over that line.
        actions = ls_session.text_document_code_action(
            {
                "textDocument": {"uri": TEST_FILE_URI},
                "range": {
                    "start": {"line": 18, "character": 4},
                    "end": {"line": 18, "character": 11},
                },
                "context": {"diagnostics": [], "only": ["quickfix"]},
            }
        )

    assert_that(actions is not None, is_(True))
    bare = [
        a
        for a in actions
        if a.get("kind") == "quickfix" and "PLY042" in a.get("title", "")
    ]
    assert_that(len(bare), is_(1))
    action = bare[0]
    assert_that(action["isPreferred"], is_(True))

    edits = action["edit"]["changes"][TEST_FILE_URI]
    assert_that(len(edits), is_(1))
    edit = edits[0]
    assert_that(edit["newText"], is_("pl.DataFrame"))

    # The replaced span must be exactly the `DataFrame[InputSchema]` annotation.
    start, end = edit["range"]["start"], edit["range"]["end"]
    assert_that(start["line"], is_(18))
    assert_that(end["line"], is_(18))
    replaced = contents.splitlines()[18][start["character"] : end["character"]]
    assert_that(replaced, is_("DataFrame[InputSchema]"))


def test_quickfix_declare_column():
    """QuickFix (D-11b): an undeclared extra return column (PLY040 "Extra
    column 'X' of type T") offers a code action that declares the column on
    the strict return schema — an insertion at the end of the schema body."""
    contents = TEST_FILE3_PATH.read_text()

    with session.LspSession() as ls_session:
        ls_session.initialize(defaults.VSCODE_DEFAULT_INITIALIZE)

        done = Event()
        ls_session.set_notification_callback(
            session.PUBLISH_DIAGNOSTICS, lambda _params: done.set()
        )
        ls_session.notify_did_open(
            {
                "textDocument": {
                    "uri": TEST_FILE3_URI,
                    "languageId": "python",
                    "version": 1,
                    "text": contents,
                }
            }
        )
        done.wait(TIMEOUT)

        # PLY040 "Extra column" points at the return expression (line 23,
        # 1-indexed -> 22). Request quick fixes over that line.
        actions = ls_session.text_document_code_action(
            {
                "textDocument": {"uri": TEST_FILE3_URI},
                "range": {
                    "start": {"line": 22, "character": 4},
                    "end": {"line": 22, "character": 50},
                },
                "context": {"diagnostics": [], "only": ["quickfix"]},
            }
        )

    assert_that(actions is not None, is_(True))
    declare = [
        a
        for a in actions
        if a.get("kind") == "quickfix" and "declare column 'extra'" in a.get("title", "")
    ]
    assert_that(len(declare), is_(1))
    action = declare[0]
    assert_that("Result" in action["title"], is_(True))

    edits = action["edit"]["changes"][TEST_FILE3_URI]
    assert_that(len(edits), is_(1))
    edit = edits[0]
    # A new field line inserted after the last field of `Result` (`value:
    # pl.Float64` on line 16, 1-indexed -> 15); a zero-width insertion.
    assert_that(edit["newText"], is_("\n    extra: pl.Float64"))
    assert_that(edit["range"]["start"], is_(edit["range"]["end"]))
    assert_that(edit["range"]["start"]["line"], is_(15))


def test_rename_column():
    """textDocument/rename (D-11b): renaming a column rewrites its schema-field
    declaration and every provable `pl.col("...")` reference; prepareRename
    gates the cursor onto a resolvable column token."""
    contents = TEST_FILE4_PATH.read_text()

    with session.LspSession() as ls_session:
        ls_session.initialize(defaults.VSCODE_DEFAULT_INITIALIZE)

        done = Event()
        ls_session.set_notification_callback(
            session.PUBLISH_DIAGNOSTICS, lambda _params: done.set()
        )
        ls_session.notify_did_open(
            {
                "textDocument": {
                    "uri": TEST_FILE4_URI,
                    "languageId": "python",
                    "version": 1,
                    "text": contents,
                }
            }
        )
        done.wait(TIMEOUT)

        # Cursor on the `amount` field declaration (line 10, 1-indexed -> 9).
        position = {"line": 9, "character": 4}

        prepared = ls_session.text_document_prepare_rename(
            {"textDocument": {"uri": TEST_FILE4_URI}, "position": position}
        )
        assert_that(
            prepared,
            is_(
                {
                    "start": {"line": 9, "character": 4},
                    "end": {"line": 9, "character": 10},
                }
            ),
        )

        workspace_edit = ls_session.text_document_rename(
            {
                "textDocument": {"uri": TEST_FILE4_URI},
                "position": position,
                "newName": "value",
            }
        )

    edits = workspace_edit["changes"][TEST_FILE4_URI]
    assert_that(len(edits), is_(3))
    for one in edits:
        assert_that(one["newText"], is_("value"))
    # The declaration (line 10 -> 9) and both `pl.col("amount")` references
    # (line 15 -> 14), each spanning just the column-name token.
    spans = sorted(
        (
            e["range"]["start"]["line"],
            e["range"]["start"]["character"],
            e["range"]["end"]["character"],
        )
        for e in edits
    )
    assert_that(spans, is_([(9, 4, 10), (14, 29, 35), (14, 64, 70)]))


def test_quickfix_retype_declared():
    """QuickFix (D-11b): a PLY040 type mismatch offers a "retype the declared
    field" action sourced from polypolarism's `suggested_annotation` and
    `declared_annotation_range` (issue #113), editing only the annotation."""
    contents = TEST_FILE2_PATH.read_text()

    with session.LspSession() as ls_session:
        ls_session.initialize(defaults.VSCODE_DEFAULT_INITIALIZE)
        # PLY040 is reported on the return expression (line 20, 1-indexed -> 19).
        actions = _code_actions(
            ls_session,
            TEST_FILE2_URI,
            contents,
            {
                "start": {"line": 19, "character": 27},
                "end": {"line": 19, "character": 48},
            },
        )

    retype = [
        a
        for a in actions
        if a.get("kind") == "quickfix" and "declared type" in a.get("title", "")
    ]
    assert_that(len(retype), is_(1))
    edit = retype[0]["edit"]["changes"][TEST_FILE2_URI][0]
    assert_that(edit["newText"], is_("pl.Float64"))
    # Only the annotation (`int` on line 16, 1-indexed -> 15) is replaced.
    assert_that(
        edit["range"],
        is_(
            {
                "start": {"line": 15, "character": 11},
                "end": {"line": 15, "character": 14},
            }
        ),
    )
    replaced = contents.splitlines()[15][11:14]
    assert_that(replaced, is_("int"))


def test_quickfix_declare_column_ply042():
    """QuickFix (D-11b): a PLY042 whose undeclared column has a statically known
    dtype (here pinned by `.cast(pl.Boolean)`) offers a "declare the column"
    action that inserts the field, using polypolarism's `fix.suggested_dtype`
    (issue #114)."""
    contents = TEST_FILE5_PATH.read_text()

    with session.LspSession() as ls_session:
        ls_session.initialize(defaults.VSCODE_DEFAULT_INITIALIZE)
        # PLY042 is reported on the `f` def line (line 14, 1-indexed -> 13).
        actions = _code_actions(
            ls_session,
            TEST_FILE5_URI,
            contents,
            {
                "start": {"line": 13, "character": 4},
                "end": {"line": 13, "character": 5},
            },
        )

    declare = [
        a
        for a in actions
        if a.get("kind") == "quickfix"
        and "declare column 'flag'" in a.get("title", "")
    ]
    assert_that(len(declare), is_(1))
    action = declare[0]
    assert_that("pl.Boolean" in action["title"], is_(True))
    assert_that("Src" in action["title"], is_(True))

    edit = action["edit"]["changes"][TEST_FILE5_URI][0]
    # A new field inserted after `keep: pl.Int64` (line 11, 1-indexed -> 10).
    assert_that(edit["newText"], is_("\n    flag: pl.Boolean"))
    assert_that(edit["range"]["start"], is_(edit["range"]["end"]))
    assert_that(edit["range"]["start"]["line"], is_(10))
