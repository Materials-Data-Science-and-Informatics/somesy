import json

from somesy.codemeta import CodeMeta
from somesy.core.core import write_json
from somesy.package_json.writer import PackageJSON  # noqa: F401  (patch regression)


def test_json_dump_not_patched():
    assert json.dumps({"a": "ü"}) == '{"a": "\\u00fc"}'
    assert json.dumps({"a": 1}, indent=None) == '{"a": 1}'


def test_write_json_format(tmp_path):
    path = tmp_path / "out.json"
    write_json({"name": "Müller"}, path)
    assert path.read_bytes() == '{\n  "name": "Müller"\n}\n'.encode()


def test_codemeta_save_indented(tmp_path):
    path = tmp_path / "codemeta.json"
    cm = CodeMeta(path, merge=False)
    cm.save()
    text = path.read_text(encoding="utf-8")
    assert text.startswith('{\n  "@context"')
    assert text.endswith("}\n")
