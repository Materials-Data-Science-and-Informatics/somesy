from somesy.codemeta import CodeMeta
from somesy.json_wrapper import json


def test_update_codemeta(somesy_input, tmp_path):
    codemeta_file = tmp_path / "codemeta.json"

    cm = CodeMeta(codemeta_file)

    # firstly, create a codemeta file
    cm.sync(somesy_input.project)
    cm.save()

    assert codemeta_file.is_file()
    dat = open(codemeta_file, "rb").read()

    # second time, no changes but codemeta.json exists -> codemeta.json is the same
    cm.sync(somesy_input.project)
    cm.save()
    assert codemeta_file.is_file()
    dat2 = open(codemeta_file, "rb").read()
    assert dat == dat2

    # third time, change the project name -> codemeta.json is different
    somesy_input.project.name = "new_name"
    cm.sync(somesy_input.project)
    cm.save()
    assert codemeta_file.is_file()
    dat3 = open(codemeta_file, "rb").read()
    assert dat != dat3

    # fourth time, change the project name back and change version in codemeta.json
    # -> codemeta.json is the same
    somesy_input.project.name = "testproject"
    with open(codemeta_file, "w") as f:
        codemeta = json.loads(dat3)
        codemeta["version"] = "0.0.2"
        json.dump(codemeta, f)
    cm.sync(somesy_input.project)
    cm.save()
    assert codemeta_file.is_file()
    dat4 = open(codemeta_file, "rb").read()
    assert dat == dat4
    assert dat3 != dat4
