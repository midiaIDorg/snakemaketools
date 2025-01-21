import shutil
import subprocess
from pathlib import Path


def copy_path(source: str | Path, destination: str | Path) -> None:
    source = Path(source)
    destination = Path(destination)
    if source.is_file():
        shutil.copy(source, destination)
    elif source.is_dir():
        shutil.copytree(source, destination)
    else:
        raise ValueError(f"Source {source} is neither a file nor a directory.")


def restore_backup(node, backup_extension: str = "_bkp") -> None:
    node_location = node.location
    backup_location = node_location.with_suffix(node_location.suffix + backup_extension)
    assert backup_location.exists(), f"Missing file to replace with:\n{backup_location}"
    copy_path(backup_location, node_location)


def replace_filesystem_entry(
    node, replacement: str | Path, backup_extension: str = "_bkp"
) -> None:
    node_location = Path(node.location)
    replacement = Path(replacement)
    assert (
        node_location.exists()
    ), f"Missing file to replace:\n{node.location}\nRerun pipeline."
    assert replacement.exists(), f"Missing file to replace with:\n{replacement}"

    backup_location = node_location.with_suffix(node_location.suffix + backup_extension)

    if backup_extension != "":
        copy_path(node_location, backup_location)
    copy_path(replacement, node_location)
