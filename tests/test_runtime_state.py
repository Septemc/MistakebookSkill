import json
import tempfile
import unittest
from pathlib import Path

from scripts.runtime_state import (
    RuntimeStateError,
    assert_can_archive,
    default_runtime_state,
    load_state,
    save_state,
    transition,
)


class RuntimeStateTests(unittest.TestCase):
    def test_save_and_load_round_trips_runtime_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "runtime_state.json"
            state = default_runtime_state(
                host="codex",
                project_root="/repo",
                entry_type="mistake",
                case_id="case-1",
                status="armed",
            )

            save_state(path, state)
            loaded = load_state(path)

            self.assertEqual(loaded["host"], "codex")
            self.assertEqual(loaded["project_root"], "/repo")
            self.assertEqual(loaded["entry_type"], "mistake")
            self.assertEqual(loaded["case_id"], "case-1")
            self.assertEqual(loaded["status"], "armed")
            self.assertIn("updated_at", loaded)

    def test_transition_rejects_skipping_directly_to_archived(self) -> None:
        state = default_runtime_state(status="pending_review", entry_type="mistake")

        with self.assertRaisesRegex(RuntimeStateError, "invalid runtime state transition"):
            transition(state, "archived")

    def test_assert_can_archive_requires_summarizing_state_and_user_confirmation(self) -> None:
        pending = default_runtime_state(status="pending_review", entry_type="mistake")
        payload = {
            "entryType": "mistake",
            "title": "case",
            "summary": "summary",
            "userConfirmed": True,
        }

        with self.assertRaisesRegex(RuntimeStateError, "requires status=summarizing"):
            assert_can_archive(pending, payload)

        summarizing = transition(pending, "summarizing")
        unconfirmed = dict(payload)
        unconfirmed["userConfirmed"] = False
        with self.assertRaisesRegex(RuntimeStateError, "userConfirmed=true"):
            assert_can_archive(summarizing, unconfirmed)

        assert_can_archive(summarizing, payload)

    def test_assert_can_archive_requires_matching_runtime_identity(self) -> None:
        state = default_runtime_state(
            status="summarizing",
            entry_type="mistake",
            case_id="case-1",
        )
        payload = {
            "entryType": "mistake",
            "caseId": "case-1",
            "title": "case",
            "summary": "summary",
            "userConfirmed": True,
        }

        wrong_type = dict(payload)
        wrong_type["entryType"] = "note"
        with self.assertRaisesRegex(RuntimeStateError, "entry_type mismatch"):
            assert_can_archive(state, wrong_type)

        wrong_case = dict(payload)
        wrong_case["caseId"] = "case-2"
        with self.assertRaisesRegex(RuntimeStateError, "case_id mismatch"):
            assert_can_archive(state, wrong_case)

        missing_case = dict(payload)
        missing_case.pop("caseId")
        with self.assertRaisesRegex(RuntimeStateError, "archive payload missing caseId"):
            assert_can_archive(state, missing_case)

    def test_load_state_rejects_unknown_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "runtime_state.json"
            path.write_text(json.dumps({"status": "unknown"}), encoding="utf-8")

            with self.assertRaisesRegex(RuntimeStateError, "unknown runtime status"):
                load_state(path)


if __name__ == "__main__":
    unittest.main()
