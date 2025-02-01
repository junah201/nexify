import os
import shutil
import subprocess
import sys
from functools import lru_cache
from importlib import metadata
from pathlib import Path

mkdocs_name = "mkdocs.yml"

missing_translation_snippet = """
{!../../docs/missing-translation.md!}
"""

non_translated_sections = [
    "reference/",
    "release-notes.md",
    "external-links.md",
    "newsletter.md",
    "management-tasks.md",
    "management.md",
    "contributing.md",
]

docs_path = Path("docs")
en_docs_path = Path("docs/en")
en_config_path: Path = en_docs_path / mkdocs_name
site_path = Path("site").absolute()
build_site_path = Path("site_build").absolute()


@lru_cache
def is_mkdocs_insiders() -> bool:
    version = metadata.version("mkdocs-material")
    return "insiders" in version


def get_lang_paths() -> list[Path]:
    return sorted(docs_path.iterdir())


def build_lang(lang: str):
    """
    Build the docs for a language.
    """
    insiders_env_file = os.environ.get("INSIDERS_FILE")
    print(f"Insiders file {insiders_env_file}")
    if is_mkdocs_insiders():
        print("Using insiders")
    lang_path: Path = Path("docs") / lang
    if not lang_path.is_dir():
        print(f"The language translation doesn't seem to exist yet: {lang}")
        raise Exception(f"The language translation doesn't seem to exist yet: {lang}")

    print(f"Building docs for: {lang}")
    build_site_dist_path = build_site_path / lang
    if lang == "en":
        dist_path = site_path
        # Don't remove en dist_path as it might already contain other languages.
        # When running build_all(), that function already removes site_path.
        # All this is only relevant locally, on GitHub Actions all this is done through
        # artifacts and multiple workflows, so it doesn't matter if directories are
        # removed or not.
    else:
        dist_path = site_path / lang
        shutil.rmtree(dist_path, ignore_errors=True)
    current_dir = os.getcwd()
    os.chdir(lang_path)
    shutil.rmtree(build_site_dist_path, ignore_errors=True)

    process = subprocess.Popen(
        ["mkdocs", "build", "--site-dir", str(build_site_dist_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # 실시간 로그 출력
    for line in process.stdout:
        print(line, end="")

    for line in process.stderr:
        print(line, end="")

    process.wait()

    shutil.copytree(build_site_dist_path, dist_path, dirs_exist_ok=True)
    os.chdir(current_dir)
    print(f"Built docs for: {lang}")


if __name__ == "__main__":
    lang = sys.argv[1]
    build_lang(lang)
