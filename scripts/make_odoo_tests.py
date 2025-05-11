#!/usr/bin/env python3
# Generates output file containing unit and robo tests
# The output should look like this:

from pathlib import Path
import yaml
import subprocess

import inspect
import os
from pathlib import Path

template = """
name: testing and deployments
'on':
  push:
    branches-ignore: null
permissions: write-all
env:
  GIMERA_NON_INTERACTIVE: 1
  GIMERA_NON_THREADED: 1
  GIMERA_NO_PRECOMMIT: 1
  GIMERA_QUIET: 1
jobs:
"""

workflows = {
    "robo": "Odoo-Ninjas/git-workflows/.github/workflows/robotests.yml@v9",
    "unit": "Odoo-Ninjas/git-workflows/.github/workflows/unittests.yml@v9",
}

current_dir = Path(
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)

file = Path(sys.argv[1])
if not file.exists():
  file.write_text(template)

parsed = yaml.safe_load(file.read_text())


def update_files(ttype="robo", listcmd=None):
    test_cases = list(
        filter(
            bool,
            subprocess.check_output(
                listcmd,
                encoding="utf-8",
            )
            .split("!!!")[1]
            .splitlines(),
        )
    )

    # remove generic created lines:
    PREFIX = f"run_{ttype}_"
    for k in list(parsed["jobs"].keys()):
        if k.startswith(PREFIX):
            del parsed["jobs"][k]

    technames = []
    for case in sorted(test_cases):
        casesafe = case
        for c in "!._ -/\\":
            casesafe = casesafe.replace(c, "_")
        techname = f"{PREFIX}{casesafe}"
        technames.append(techname)
        projectname = Path(case).stem
        for c in "!._ -/\\":
            projectname = projectname.replace(".", "_")
        projectname += "-${{ github.ref_name }}"

        workflow = workflows[ttype]

        params = {
            "enabled": True,
            "projectname": projectname,
            "testfile": case,
        }
        if ttype == "robo":
            params["timeout"] = 140

        parsed["jobs"][techname] = {
            "uses": workflow,
            "concurrency": {
                "group": f"${{{{ github.workflow }}}}-${{{{ github.ref }}}}-{case}",
                "cancel-in-progress": True,
            },
            "with": params,
        }
    parsed["jobs"][f"all_{ttype}tests"] = {
        "name": "All robotests done",
        "needs": list(technames),
        "runs-on": "self-hosted",
        "steps": [
            {"name": "good", "run": 'echo f"All {ttype} done"'},
        ],
    }


update_files("robo", ["odoo", "robot", "list"])
update_files("unit", ["odoo", "list-unit-test-files", "-m"])

file.write_text(yaml.dump(parsed, sort_keys=False))
