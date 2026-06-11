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
        # diagnostic `code`; `severity` routes errors vs warnings; ranges
        # span the function body reported by `--format json`.
        expected = {
            "uri": TEST_FILE_URI,
            "diagnostics": [
                {
                    "range": {
                        "start": {"line": 18, "character": 0},
                        "end": {"line": 19, "character": 0},
                    },
                    "message": (
                        "Column 'amount' not found. "
                        "Available columns: ['id', 'value']"
                    ),
                    "severity": 1,
                    "code": "PLY001",
                    "codeDescription": {"href": ERROR_CODES_HREF},
                    "source": "polypolarism",
                },
                {
                    "range": {
                        "start": {"line": 22, "character": 0},
                        "end": {"line": 23, "character": 0},
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
