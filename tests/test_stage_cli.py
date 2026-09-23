import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jev_computer_use.stage_cli import main, write_private


class StageCliTests(unittest.TestCase):
    def test_reading_retained_evidence_needs_neither_ui_nor_api_key(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_private(
                root / "evidence.json",
                {
                    "s1": {
                        "source_id": "s1",
                        "url": "https://example.test",
                        "title": "Observed",
                        "text": "Original observed value",
                    }
                },
            )
            self.assertEqual((root / "evidence.json").stat().st_mode & 0o777, 0o600)
            output = io.StringIO()
            with (
                patch(
                    "jev_computer_use.stage_cli.NativeCUA",
                    side_effect=AssertionError("Must not start CUA"),
                ),
                contextlib.redirect_stdout(output),
            ):
                main(
                    [
                        "--state-dir",
                        directory,
                        "--evidence",
                        "s1",
                        "--query",
                        "observed",
                    ]
                )
            result = json.loads(output.getvalue())[0]
            self.assertEqual(result["text"], "Original observed value")
            self.assertTrue(result["query_found"])
            self.assertFalse(result["truncated"])


if __name__ == "__main__":
    unittest.main()
