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
        "robo": "Odoo-Ninjas/git-workflows/.github/workflows/robotests.yml@v9.21",
        "unit": "Odoo-Ninjas/git-workflows/.github/workflows/unittests.yml@v9.21",
        "prepare_db": "Odoo-Ninjas/git-workflows/.github/workflows/prepare_test_db.yml@v9.21",
        "prepare_sources": "Odoo-Ninjas/git-workflows/.github/workflows/prepare_sources.yml@v9.21",
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
    parser.add_argument("--shared-dir", type=str, default="",
                        help="Shared filesystem path for prepared database dumps (e.g. /home/githubrunner/runner.shared)")
    parser.add_argument("--extra-modules", type=str, default="",
                        help="Additional modules to install on top of MANIFEST['install'] (e.g. 'robot_utils crm sale_management')")
    parser.add_argument("--uninstall-modules", type=str, default="",
                        help="Modules to uninstall before backup (e.g. 'partner_autocomplete')")
    args = parser.parse_args()

    file = Path(args.file)
    TIMEOUT = args.timeout
    MAX_RETRIES = args.max_retries
    if not file.exists():
        print(f"Creating not existing file: {file}")
        file.write_text(template)

    parsed = yaml.safe_load(file.read_text())


    def update_files(ttype="robo", listcmd=None, combined=False, shared_dir="", needs_jobs=None):
        workflow = workflows[ttype]
        PREFIX = f"run_{ttype}_"

        # remove previously generated jobs
        for k in list(parsed["jobs"].keys()):
            if k.startswith(PREFIX):
                del parsed["jobs"][k]

        if combined:
            techname = f"{PREFIX}all"
            with_params = {
                "enabled": True,
                "projectname": f"all_{ttype}tests-${{{{ github.ref_name }}}}",
            }
            if shared_dir:
                with_params["shared_dir"] = shared_dir
            parsed["jobs"][techname] = {
                "uses": workflow,
                "with": with_params,
            }
            if needs_jobs:
                parsed["jobs"][techname]["needs"] = list(needs_jobs)
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
                if shared_dir:
                    params["shared_dir"] = shared_dir

                job = {
                    "uses": workflow,
                    "with": params,
                }
                if needs_jobs:
                    job["needs"] = list(needs_jobs)
                parsed["jobs"][techname] = job

        parsed["jobs"][f"all_{ttype}tests"] = {
            "name": f"All {ttype}tests done",
            "needs": list(technames),
            "runs-on": "self-hosted",
            "timeout-minutes": TIMEOUT,
            "steps": [
                {"name": "good", "run": f'echo "All {ttype} done"'},
            ],
        }

    # generate prepare_sources + prepare_test_db jobs if shared_dir is set
    robo_needs = []
    unit_needs = []
    if args.shared_dir:
        # prepare_sources: gimera apply + cache sources
        parsed["jobs"].pop("prepare_sources", None)
        parsed["jobs"]["prepare_sources"] = {
            "uses": workflows["prepare_sources"],
            "with": {
                "enabled": True,
                "shared_dir": args.shared_dir,
            },
        }

        # prepare_test_db: uses cached sources, prepares DB dump
        parsed["jobs"].pop("prepare_test_db", None)
        prepare_params = {
            "enabled": True,
            "projectname": f"prepare_test_db-${{{{ github.ref_name }}}}",
            "shared_dir": args.shared_dir,
        }
        if args.extra_modules:
            prepare_params["extra_modules"] = args.extra_modules
        if args.uninstall_modules:
            prepare_params["uninstall_modules"] = args.uninstall_modules
        parsed["jobs"]["prepare_test_db"] = {
            "uses": workflows["prepare_db"],
            "with": prepare_params,
            "needs": ["prepare_sources"],
        }
        robo_needs = ["prepare_test_db"]
        unit_needs = ["prepare_sources"]

    update_files("robo", ["odoo", "robot", "list"], shared_dir=args.shared_dir, needs_jobs=robo_needs)
    update_files("unit", ["odoo", "list-unit-test-files", "-m"], combined=args.combined_unittests,
                 shared_dir=args.shared_dir, needs_jobs=unit_needs)

    file.write_text(yaml.dump(parsed, sort_keys=False))

if __name__ == "__main__":
    raise SystemExit(main())