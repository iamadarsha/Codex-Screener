"""`RunStatus` is a plain enum with no transition-validation logic (see
`app/research/run_state.py`'s own docstring) — this test stays minimal and
honest about that rather than inventing a transition matrix to test."""

from __future__ import annotations

from app.research.run_state import RunStatus


def test_run_status_has_exactly_the_six_expected_members():
    assert {s.value for s in RunStatus} == {
        "created",
        "validating",
        "running",
        "succeeded",
        "failed",
        "cancelled",
    }


def test_run_status_is_a_str_enum_usable_as_plain_string():
    assert RunStatus.CREATED == "created"
    assert RunStatus.SUCCEEDED.value == "succeeded"
