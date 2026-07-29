import json
from pathlib import Path


def test_schema_files_are_valid_json():
    root = Path(__file__).resolve().parents[2]
    paths = list((root / "schemas").glob("*.json"))
    assert len(paths) >= 5
    for path in paths:
        json.loads(path.read_text(encoding="utf-8"))

