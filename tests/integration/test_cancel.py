from pathlib import Path
from threading import Event

from raceframe.core.processing import process_folder
from raceframe.export.manifest import read_report


def test_cancel_does_not_start_next_image(photo_factory, tmp_path, fake_detector):
    path = photo_factory("input/a.jpg")
    photo_factory("input/b.jpg")
    stop = Event()
    result = process_folder(
        path.parent,
        tmp_path / "out",
        detector=fake_detector,
        cancel=stop,
        progress=lambda n, total: stop.set(),
    )
    assert result["status"] == "cancelled"
    assert fake_detector.calls == 1
    assert result["summary"]["exported"] == 1
    assert result["summary"]["not_attempted"] == 1
    assert read_report(Path(result["manifest_path"]).parent)["status"] == "cancelled"


def test_real_sigint_cli_exits_130(photo_factory, tmp_path):
    import json
    import os
    import signal
    import subprocess
    import sys
    import time

    path = photo_factory("input/a.jpg")
    photo_factory("input/b.jpg")
    weights = tmp_path / "fake.pt"
    weights.write_bytes(b"mock")
    marker = tmp_path / "active"
    worker = tmp_path / "worker.py"
    worker.write_text("""
import sys,time
from pathlib import Path
from raceframe.cli.main import main
marker=Path(sys.argv[1])
class Detector:
    def detect(self,image):
        marker.touch()
        time.sleep(0.2)
        return ()
raise SystemExit(main(sys.argv[2:],detector_factory=lambda *a:Detector()))
""")
    proc = subprocess.Popen(
        [
            sys.executable,
            str(worker),
            str(marker),
            "process",
            str(path.parent),
            "--output",
            str(tmp_path / "out"),
            "--model",
            str(weights),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        assert marker.exists()
        os.kill(proc.pid, signal.SIGINT)
        stdout, stderr = proc.communicate(timeout=10)
        assert proc.returncode == 130, stderr
        report = json.loads(stdout)
        assert report["status"] == "cancelled"
        assert report["summary"]["exported"] == 1
        assert report["summary"]["not_attempted"] == 1
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
