import logging
import os
import shutil
import subprocess
import zipfile

from nexify.cli.deploy.types import NexifyConfig
from rich.console import Console

logger = logging.getLogger("nexify_cli")
console = Console()


def install_requirements(requirements_file_path: str, target_dir: str, config: NexifyConfig):
    """
    Install requirements from a requirements file.
    """
    os.makedirs(target_dir, exist_ok=True)

    architecture = config.get("architecture", "x86_64")
    platform = "manylinux2014_aarch64" if architecture == "arm64" else "manylinux2014_x86_64"

    process = subprocess.run(
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
        ],
        capture_output=True,
        text=True,
    )

    # Rich 콘솔을 사용해 출력
    # if process.stdout:
    #     console.print(process.stdout.strip(), style="cyan")
    # if process.stderr:
    #     console.print(process.stderr.strip(), style="red")


def package_lambda_function(source_dir: str, requirements_dir: str, output_zip_path: str):
    """
    Package a Lambda function.
    """
    shutil.make_archive(output_zip_path.replace(".zip", ""), "zip", requirements_dir, logger=logger)

    with zipfile.ZipFile(output_zip_path, "a", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".nexify")]

            for file in files:
                zf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file)))
