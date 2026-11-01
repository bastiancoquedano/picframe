import json

from raceframe.cli.main import main


def test_cli_json_and_errors(photo_factory, tmp_path, fake_detector, capsys):
    path = photo_factory("input/a.jpg")
    weights = tmp_path / "local.pt"
    weights.write_bytes(b"fake")
    args = ["process", str(path.parent), "--output", str(tmp_path / "out"), "--model", str(weights)]
    code = main(args, detector_factory=lambda *a: fake_detector)
    captured = capsys.readouterr()
    assert code == 0
    assert json.loads(captured.out)["summary"]["exported"] == 1
    assert "1/1" in captured.err
    code = main(["process", str(path.parent), "--model", str(tmp_path / "missing.pt")])
    assert code == 2
    assert "error" in json.loads(capsys.readouterr().out)
