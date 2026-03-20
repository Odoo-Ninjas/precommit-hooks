#!/usr/bin/env python3
# Generates output file containing unit and robo tests
# The output should look like this:

def main():

    from pathlib import Path
    import argparse
    import yaml
    import subprocess

    import inspect
    import os
    import sys
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
    jobs: {}
    """

    workflows = {
        "robo": "Odoo-Ninjas/git-workflows/.github/workflows/robotests.yml@v9.5",
        "unit": "Odoo-Ninjas/git-workflows/.github/workflows/unittests.yml@v9.5",
    }

    current_dir = Path(
        os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Path to the workflow file")
    parser.add_argument("timeout", type=int, help="Timeout in minutes")
    parser.add_argument("max_retries", type=int, nargs="?", default=10, help="Max retries")
    parser.add_argument("--combined-unittests", action="store_true",
                        help="Run all unit tests combined in a single job via 'odoo -f run-tests' instead of splitting per file")
    args = parser.parse_args()

    file = Path(args.file)
    TIMEOUT = args.timeout
    MAX_RETRIES = args.max_retries
    if not file.exists():
        print(f"Creating not existing file: {file}")
        file.write_text(template)

    parsed = yaml.safe_load(file.read_text())


    def update_files(ttype="robo", listcmd=None, combined=False):
        workflow = workflows[ttype]
        PREFIX = f"run_{ttype}_"

        # remove previously generated jobs
        for k in list(parsed["jobs"].keys()):
            if k.startswith(PREFIX):
                del parsed["jobs"][k]

        if combined:
            techname = f"{PREFIX}all"
            parsed["jobs"][techname] = {
                "uses": workflow,
                "with": {
                    "enabled": True,
                    "projectname": f"all_{ttype}tests-${{{{ github.ref_name }}}}",
                },
            }
            technames = [techname]
        else:
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

                params = {
                    "enabled": True,
                    "projectname": projectname,
                    "testfile": case,
                }

                parsed["jobs"][techname] = {
                    "uses": workflow,
                    "with": params,
                }

        parsed["jobs"][f"all_{ttype}tests"] = {
            "name": f"All {ttype}tests done",
            "needs": list(technames),
            "runs-on": "self-hosted",
            "timeout-minutes": TIMEOUT,
            "steps": [
                {"name": "good", "run": f'echo "All {ttype} done"'},
            ],
        }


    update_files("robo", ["odoo", "robot", "list"])
    update_files("unit", ["odoo", "list-unit-test-files", "-m"], combined=args.combined_unittests)

    file.write_text(yaml.dump(parsed, sort_keys=False))

if __name__ == "__main__":
    raise SystemExit(main())