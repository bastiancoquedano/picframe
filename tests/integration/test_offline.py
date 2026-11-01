import json
import os
import shutil
import subprocess
import sys

import pytest


@pytest.mark.real_model
def test_real_process_offline(tmp_path, photo_factory):
    model = os.environ.get("RACEFRAME_TEST_MODEL")
    if not model:
        pytest.skip("Prueba offline real no ejecutada: falta RACEFRAME_TEST_MODEL")
    path = photo_factory("input/photo.jpg")
    (path.parent / "broken.jpg").write_bytes(b"invalid JPEG")
    script = tmp_path / "offline_worker.py"
    script.write_text("""
import socket,sys
attempts=[]
def denied(*args,**kwargs):
    attempts.append('network')
    raise RuntimeError('network forbidden')
socket.socket.connect=denied
socket.socket.connect_ex=denied
socket.create_connection=denied
socket.getaddrinfo=denied
from raceframe.cli.main import main
code=main(sys.argv[1:])
assert not attempts, attempts
raise SystemExit(code)
""")
    command = [
        sys.executable,
        str(script),
        "process",
        str(path.parent),
        "--output",
        str(tmp_path / "out"),
        "--model",
        model,
        "--device",
        "cpu",
    ]
    sandbox = shutil.which("sandbox-exec")
    if sandbox:
        command = [sandbox, "-p", "(version 1) (allow default) (deny network*)", *command]
    env = {**os.environ, "RACEFRAME_RUNTIME_DIR": str(tmp_path / "runtime")}
    result = subprocess.run(command, env=env, text=True, capture_output=True, timeout=180)
    assert result.returncode == 1, result.stderr + result.stdout
    report = json.loads(result.stdout)
    assert report["summary"]["exported"] == 1
    assert report["summary"]["errors"] == 1
    assert report["summary"]["review_required"] == 1
