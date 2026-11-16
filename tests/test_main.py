"""Tests for the entry point, python -m bracketeer."""

import subprocess
import sys

import bracketeer.__main__ as entry


def test_python_m_bracketeer_starts_and_quits():
    done = subprocess.run(
        [sys.executable, "-m", "bracketeer"],
        input="0\n",
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert done.returncode == 0
    assert "Goodbye." in done.stdout


def test_nfr_us_2_an_unexpected_error_is_a_message_not_a_traceback(monkeypatch, capsys):
    def broken():
        raise RuntimeError("disk on fire")

    monkeypatch.setattr(entry, "run", broken)
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    assert entry.main() == 1
    shown = capsys.readouterr().out
    assert "unexpected problem and has to close: disk on fire" in shown
    assert "Traceback" not in shown
