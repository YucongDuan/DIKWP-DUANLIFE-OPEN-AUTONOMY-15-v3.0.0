from pathlib import Path
import re


def test_project_text_is_english_only():
    root = Path(__file__).resolve().parents[1]
    pattern = re.compile(r"[\u3400-\u9fff]")
    allowed = {".py", ".md", ".json", ".csv", ".html", ".toml", ".cff", ".txt", ".yml", ".yaml", ".tla"}
    offenders = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in allowed and ".git" not in path.parts:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if pattern.search(text):
                offenders.append(str(path.relative_to(root)))
    assert offenders == []
