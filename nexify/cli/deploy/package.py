import os
import shutil
import subprocess
import zipfile

from nexify.cli.deploy.types import NexifyConfig
from rich import print
from rich.console import Console
from rich.progress import Progress, TaskID

console = Console()


def install_requirements(
    requirements_file_path: str, target_dir: str, config: NexifyConfig, progress: Progress, task: TaskID
):
    """
    Install requirements from a requirements file.
    """
    os.makedirs(target_dir, exist_ok=True)

    architecture = config.get("architecture", "x86_64")
    platform = "manylinux2014_aarch64" if architecture == "arm64" else "manylinux2014_x86_64"

    extra_args = config.get("package", {}).get("pipCmdExtraArgs", [])

    progress.update(task, status="\n\tSetting up Python environment...")
    process = subprocess.Popen(
        [
            "pip",
            "install",
            "-r",
            requirements_file_path,
            "-t",
            target_dir,
            "--platform",
            platform,
            "--implementation",
            "cp",
            "--python-version",
            config["provider"]["runtime"].strip("python"),
            "--only-binary=:all:",
            "--upgrade",
        ]
        + extra_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    msg = ""
    for c in iter(lambda: process.stdout.read(1), b""):  # type: ignore
        msg += c.decode("utf-8")
        if "\n" in msg:
            progress.update(task, status="\n\t" + msg)
            msg = ""

    process.wait()

    if process.stderr:
        error = process.stderr.read().decode("utf-8").strip()

        if not error:
            return

        if "ERROR" in error.upper():
            print(f"\n\n[red]Installation failed: {error}[/red]")
            raise SystemExit(1)
        if "WARNING" in error.upper():
            print(f"\n\n[yellow]Installation completed with warnings:\n\n{error}[/yellow]\n\n")
        else:
            print(f"\n\n[red]Installation failed: {error}[/red]")
            raise SystemExit(1)


def package_lambda_function(source_dir: str, requirements_dir: str, output_zip_path: str):
    """
    Package a Lambda function.
    """
    shutil.make_archive(output_zip_path.replace(".zip", ""), "zip", requirements_dir)

    with zipfile.ZipFile(output_zip_path, "a", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".nexify")]

            for file in files:
                zf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file)))
