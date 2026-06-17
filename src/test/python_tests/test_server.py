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
TIMEOUT = 30  # seconds

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
