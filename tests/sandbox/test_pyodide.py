from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from prefab_ui.sandbox._pyodide import PyodideSandbox


def test_stop_terminates_and_communicates_with_process() -> None:
    process = MagicMock(spec=subprocess.Popen)
    process.stdin = MagicMock()
    process.stdout = MagicMock()
    process.stderr = MagicMock()
    process.poll.return_value = None
    sandbox = PyodideSandbox()
    sandbox._process = process

    sandbox._stop()

    assert sandbox._process is None
    process.terminate.assert_called_once_with()
    process.communicate.assert_called_once_with(timeout=5)
    process.stdin.close.assert_called_once_with()
    process.stdout.close.assert_called_once_with()
    process.stderr.close.assert_called_once_with()


def test_stop_kills_process_when_graceful_shutdown_times_out() -> None:
    process = MagicMock(spec=subprocess.Popen)
    process.stdin = MagicMock()
    process.stdout = MagicMock()
    process.stderr = MagicMock()
    process.poll.return_value = None
    process.communicate.side_effect = [subprocess.TimeoutExpired("deno", 5), (b"", b"")]
    sandbox = PyodideSandbox()
    sandbox._process = process

    sandbox._stop()

    process.kill.assert_called_once_with()
    assert process.communicate.call_count == 2
    process.stdin.close.assert_called_once_with()
    process.stdout.close.assert_called_once_with()
    process.stderr.close.assert_called_once_with()


@pytest.mark.timeout(120)
@pytest.mark.skipif(shutil.which("deno") is None, reason="Deno not installed")
async def test_cold_start_keeps_download_logs_out_of_responses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DENO_DIR", str(tmp_path / "deno-cache"))
    async with PyodideSandbox() as sandbox:
        for text in ("first", "second"):
            result = await sandbox.run(
                f"from prefab_ui.components import Text\nview = Text({text!r})"
            )
            assert result["view"]["content"] == text
