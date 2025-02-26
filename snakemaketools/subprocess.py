import subprocess

from pprint import pprint


def run(cmd, *args, capture_output=True, check=True, verbose=True, **kwargs):
    if verbose:
        print("running:")
        print()
        pprint(cmd)
        print()
    try:
        res = subprocess.run(
            cmd, *args, capture_output=capture_output, check=check, **kwargs
        )
        return res
    except subprocess.CalledProcessError as exc:
        print("-----------------")
        print("SUBPROCESS FAILED")
        print(f"Return Code: {exc.returncode}")
        print(f"Command: {exc.cmd}")
        print()
        print(f"STDOUT:")
        print(exc.stdout)
        print()
        print(f"STDERR:")
        print(exc.stderr)
        print("-----------------")
        raise exc
