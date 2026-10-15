"""Create or ensure one local platform-only Super Admin through Identity's operator CLI."""

import argparse
import importlib.util
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEV_SCRIPT = ROOT / "scripts" / "local" / "dev.py"


def local_dev():
    spec = importlib.util.spec_from_file_location("globalchat_local_dev", DEV_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Local development runner is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--password-env", required=True)
    args = parser.parse_args()
    if not os.getenv(args.password_env):
        raise SystemExit(
            f"{args.password_env} must be set for an initial local bootstrap"
        )

    dev = local_dev()
    environment = dev.env("identity")
    environment[args.password_env] = os.environ[args.password_env]
    subprocess.run(
        [
            dev.interpreter("identity"),
            "-m",
            "app.platform_operator",
            "bootstrap",
            "--email",
            args.email,
            "--name",
            args.name,
            "--password-env",
            args.password_env,
        ],
        cwd=dev.folder("identity"),
        env=environment,
        check=True,
    )


if __name__ == "__main__":
    main()
