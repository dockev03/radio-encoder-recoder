import threading
from pathlib import Path

import pytest

from services import recording


@pytest.fixture(autouse=True)
def reset_recording():
    yield

    recording._cleanup_temp_files()
    recording._reset_state()


def _slow_finalize(monkeypatch, tmp_path):
    entered = threading.Event()
    release = threading.Event()

    def finalize():
        entered.set()
        release.wait(5)

    monkeypatch.setattr(recording, "_finalize_recording", finalize)
    monkeypatch.setattr(recording, "_status", "paused")
    monkeypatch.setattr(recording, "_current_file", str(tmp_path / "test.wav"))

    return entered, release


def test_status_disponible_pendant_la_finalisation(monkeypatch, tmp_path):
    entered, release = _slow_finalize(monkeypatch, tmp_path)

    worker = threading.Thread(target=recording.stop_recording)
    worker.start()
    assert entered.wait(5)

    status = {}
    probe = threading.Thread(
        target=lambda: status.update(recording.get_recording_status())
    )
    probe.start()
    probe.join(1)

    release.set()
    worker.join(5)

    assert status.get("status") == "finalizing"


def test_stop_refuse_pendant_la_finalisation(monkeypatch, tmp_path):
    entered, release = _slow_finalize(monkeypatch, tmp_path)

    worker = threading.Thread(target=recording.stop_recording)
    worker.start()
    assert entered.wait(5)

    result = recording.stop_recording()

    release.set()
    worker.join(5)

    assert result["error"] == "already_finalizing"


def test_segments_sur_le_disque_de_destination(monkeypatch, tmp_path):
    monkeypatch.setattr(recording, "is_allowed_path", lambda path: True)
    monkeypatch.setattr(recording, "_start_segment", lambda: None)

    result = recording.start_recording(
        directory=str(tmp_path),
        filename="chronique"
    )

    assert result["success"]
    assert Path(recording._temp_directory).parent == tmp_path
    assert Path(recording._temp_directory).name.startswith(".")


def test_wav_rf64_au_dela_de_4_go(tmp_path):
    capture = recording._build_capture_command(tmp_path / "segment.wav")
    final = recording._build_final_command(
        tmp_path / "segments.txt",
        tmp_path / "final.wav",
        "wav"
    )

    for command in (capture, final):
        assert command[command.index("-rf64") + 1] == "auto"


def test_capture_en_16_bits(tmp_path):
    capture = recording._build_capture_command(tmp_path / "segment.wav")

    assert capture[capture.index("-c:a") + 1] == "pcm_s16le"


class FakeProcess:

    def __init__(self, returncode=None):
        self.returncode = returncode

    def poll(self):
        return self.returncode


def test_concat_ignore_les_segments_illisibles(monkeypatch, tmp_path):
    good = tmp_path / "segment_0001.wav"
    good.write_bytes(b"\0" * recording.MIN_SEGMENT_SIZE)

    empty = tmp_path / "segment_0002.wav"
    empty.write_bytes(b"")

    missing = tmp_path / "segment_0003.wav"

    monkeypatch.setattr(recording, "_temp_directory", str(tmp_path))
    monkeypatch.setattr(
        recording,
        "_segments",
        [str(good), str(empty), str(missing)]
    )

    concat = recording._create_concat_file().read_text(encoding="utf-8")

    assert concat == f"file '{good}'\n"


def test_coupure_source_detectee(monkeypatch):
    monkeypatch.setattr(recording, "_status", "recording")
    monkeypatch.setattr(recording, "_process", FakeProcess(returncode=1))

    status = recording.get_recording_status()

    assert status["status"] == "recording"
    assert status["reconnecting"] is True
    assert status["dropouts"] == 1


def test_surveillance_relance_la_capture(monkeypatch):
    def start_segment():
        recording._process = FakeProcess()

    monkeypatch.setattr(recording, "MONITOR_INTERVAL", 0.01)
    monkeypatch.setattr(recording, "_start_segment", start_segment)
    monkeypatch.setattr(recording, "_status", "recording")
    monkeypatch.setattr(recording, "_process", FakeProcess(returncode=1))
    monkeypatch.setattr(recording, "_session", 1)

    monitor = threading.Thread(target=recording._monitor_capture, args=(1,))
    monitor.start()

    for _ in range(200):
        if recording._process is not None and recording._process.poll() is None:
            break

        threading.Event().wait(0.01)

    with recording._lock:
        restarted = recording._process.poll() is None
        reconnecting = recording._reconnecting
        dropouts = recording._dropouts

        recording._status = "stopped"

    monitor.join(5)

    assert restarted
    assert reconnecting is False
    assert dropouts == 1
    assert not monitor.is_alive()
