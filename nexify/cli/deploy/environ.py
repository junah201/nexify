import os

from rich import print


def load_env(target_dir: str):
    """
    Load environment variables from a .env file.
    """
    env_file = os.path.join(target_dir, ".env")
    if not os.path.exists(env_file):
        return

    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            os.environ[key] = value
            print(f"[green]Setting environment variable[/green] [blue]{key}[/blue]=[gray]***[/gray]")
