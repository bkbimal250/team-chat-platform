"""Local Windows orchestration; never calls AWS or Terraform. Credentials stay in .local/."""

import argparse
import json
import os
import secrets
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".local"
SERVICES = [
    "organization",
    "identity",
    "user",
    "conversation",
    "messaging",
    "media",
    "notification",
    "realtime",
    "gateway",
]
DATABASES = dict(
    zip(
        SERVICES[:7],
        [
            "teamchat_organization_db",
            "identity_db",
            "teamchat_user_db",
            "conversation_db",
            "teamchat_message_db",
            "teamchat_media_db",
            "teamchat_notification_db",
        ],
    )
)
WORKERS = {
    "organization": [("outbox", ["manage.py", "publish_outbox"])],
    "identity": [
        ("outbox", ["-m", "app.events.run_worker"]),
        ("consumer", ["-m", "app.consumer_runner"]),
    ],
    "user": [
        ("outbox", ["-m", "app.outbox_runner"]),
        ("consumer", ["-m", "app.consumer_runner"]),
    ],
    "conversation": [
        ("outbox", ["-m", "app.outbox_runner"]),
        ("consumer", ["-m", "app.consumer_runner"]),
    ],
    "messaging": [
        ("outbox", ["-m", "app.outbox_runner"]),
        ("consumer", ["-m", "app.consumer_runner"]),
    ],
    "media": [
        ("outbox", ["-m", "app.outbox_runner"]),
        ("consumer", ["-m", "app.consumer_runner"]),
    ],
    "notification": [
        ("outbox", ["-m", "app.outbox_runner"]),
        ("consumer", ["-m", "app.consumer_runner"]),
        ("delivery", ["-m", "app.delivery_worker"]),
    ],
    "realtime": [("consumer", ["-m", "app.consumer_runner"])],
}


def folder(service):
    return ROOT / "services" / f"{service}-service"


def interpreter(service):
    return str(folder(service) / ".venv" / "Scripts" / "python.exe")


def config():
    return json.loads((LOCAL / "config.json").read_text())


def prepare():
    LOCAL.mkdir(exist_ok=True)
    if not (LOCAL / "config.json").exists():
        c = {
            k: secrets.token_urlsafe(36)
            for k in [
                "db_password",
                "rabbit_password",
                "storage_password",
                "internal_token",
                "django_secret",
            ]
        }
        (LOCAL / "config.json").write_text(json.dumps(c))
        source = (
            "from cryptography.hazmat.primitives.asymmetric import rsa;from cryptography.hazmat.primitives import serialization;from pathlib import Path;k=rsa.generate_private_key(public_exponent=65537,key_size=2048);p=Path(r'"
            + str(LOCAL)
            + "');p.joinpath('jwt-private.pem').write_bytes(k.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()));p.joinpath('jwt-public.pem').write_bytes(k.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo))"
        )
        subprocess.run([interpreter("identity"), "-c", source], check=True)
    c = config()
    (LOCAL / "compose.env").write_text(
        "\n".join(
            f"{k}={v}"
            for k, v in {
                "LOCAL_DB_PASSWORD": c["db_password"],
                "LOCAL_RABBIT_PASSWORD": c["rabbit_password"],
                "LOCAL_STORAGE_PASSWORD": c["storage_password"],
            }.items()
        )
        + "\n"
    )
    print("Local credentials/keys ready (values not displayed).")


def env(service):
    c = config()
    e = os.environ.copy()
    e["PYTHONPATH"] = str(folder(service))
    # Never inherit real cloud/SMS credentials into development processes.
    for k in list(e):
        if k.startswith(("AWS_", "VONAGE_", "SMS_", "FIREBASE_")):
            e.pop(k, None)
    public = (LOCAL / "jwt-public.pem").read_text()
    private = (LOCAL / "jwt-private.pem").read_text()
    e.update(
        {
            "APP_ENV": "development",
            "ENVIRONMENT": "local",
            "DJANGO_SETTINGS_MODULE": "config.settings.local",
            "SECRET_KEY": c["django_secret"],
            "DEBUG": "false",
            "DEV_CONTEXT_ENABLED": "false",
            "ALLOWED_HOSTS": "localhost,127.0.0.1,testserver",
            "INTERNAL_SERVICE_TOKEN": c["internal_token"],
            "SERVICE_AUTH_TOKEN": c["internal_token"],
            "JWT_PUBLIC_KEY": public,
            "IDENTITY_JWT_PUBLIC_KEY": public,
            "ACCESS_TOKEN_PUBLIC_KEY": public,
            "ACCESS_TOKEN_PRIVATE_KEY": private,
            "OTP_PROVIDER": "development",
            "REGISTRATION_POLICY": "invite_only",
            "REDIS_URL": "redis://127.0.0.1:6380/0",
            "RABBITMQ_URL": f"amqp://globalchat_local:{quote(c['rabbit_password'], safe='')}@127.0.0.1:5672/%2F",
            "CORS_ALLOWED_ORIGINS": "http://localhost:3000",
            "IDENTITY_SERVICE_URL": "http://127.0.0.1:8001",
            "ORGANIZATION_SERVICE_URL": "http://127.0.0.1:8000",
            "USER_SERVICE_URL": "http://127.0.0.1:8002",
            "CONVERSATION_API_URL": "http://127.0.0.1:8003",
            "CONVERSATION_SERVICE_URL": "http://127.0.0.1:8003",
            "INSTANCE_ID": "local-realtime-api",
            "PUSH_PROVIDER": "fake",
            "MEDIA_STORAGE_BACKEND": "local",
            "LOCAL_STORAGE_ROOT": str(LOCAL / "media"),
            "LOCAL_STORAGE_SECRET": c["storage_password"],
            "LOCAL_STORAGE_BASE_URL": "http://127.0.0.1:8005",
            "AWS_REGION": "us-east-1",
            "MEDIA_S3_BUCKET": "globalchat-local-media",
            "MEDIA_S3_ENDPOINT_URL": "http://127.0.0.1:9000",
            "AWS_ACCESS_KEY_ID": "globalchat_local",
            "AWS_SECRET_ACCESS_KEY": c["storage_password"],
            "AWS_EC2_METADATA_DISABLED": "true",
            "NEXT_PUBLIC_API_URL": "http://localhost:8008",
            "NEXT_PUBLIC_WS_URL": "ws://localhost:8007",
        }
    )
    for i, s in enumerate(SERVICES[:7]):
        e[s.upper() + "_URL"] = f"http://127.0.0.1:{8000 + i}"
    if service in DATABASES:
        e["DATABASE_URL"] = (
            f"postgresql+asyncpg://postgres:{quote(c['db_password'], safe='')}@127.0.0.1:5434/{DATABASES[service]}"
        )
        if service == "organization":
            e["DATABASE_URL"] = e["DATABASE_URL"].replace(
                "postgresql+asyncpg", "postgresql"
            )
            e["TEST_DATABASE_URL"] = e["DATABASE_URL"].replace(
                "/teamchat_organization_db", "/test_teamchat_organization_db"
            )
    return e


def compose(*args):
    return subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            str(LOCAL / "compose.env"),
            "-f",
            str(ROOT / "docker-compose.local.yml"),
            *args,
        ],
        check=True,
    )


def run(service, args, logname=None):
    handle = (LOCAL / (logname or f"{service}-command.log")).open("w")
    execution_env = env(service)
    if "pytest" in args and service in DATABASES and service != "organization":
        name = "test_" + DATABASES[service]
        execution_env["DATABASE_URL"] = execution_env["DATABASE_URL"].replace(
            "/" + DATABASES[service], "/" + name
        )
        prefix = [
            "docker",
            "compose",
            "--env-file",
            str(LOCAL / "compose.env"),
            "-f",
            str(ROOT / "docker-compose.local.yml"),
            "exec",
            "-T",
            "postgres",
        ]
        exists = subprocess.check_output(
            prefix
            + [
                "psql",
                "-U",
                "postgres",
                "-tAc",
                f"SELECT 1 FROM pg_database WHERE datname='{name}'",
            ],
            text=True,
        ).strip()
        if exists != "1":
            subprocess.run(prefix + ["createdb", "-U", "postgres", name], check=True)
        with (LOCAL / (service + "-test-migration.log")).open("w") as migration_log:
            subprocess.run(
                [interpreter(service), "-m", "alembic", "upgrade", "head"],
                cwd=folder(service),
                env=execution_env,
                stdout=migration_log,
                stderr=subprocess.STDOUT,
                check=True,
            )
    if "-m" in args and "pytest" in args and service == "organization":
        execution_env["ENVIRONMENT"] = "test"
    if "pytest" in args and service == "media":
        for key in list(execution_env):
            if (
                key.startswith(("MEDIA_", "LOCAL_STORAGE_", "AWS_"))
                or key == "JWT_PUBLIC_KEY"
            ):
                execution_env.pop(key, None)
    if "pytest" in args and service == "notification":
        execution_env.pop("JWT_PUBLIC_KEY", None)
    if "pytest" in args and service == "gateway":
        execution_env.pop("CORS_ALLOWED_ORIGINS", None)
    result = subprocess.run(
        [interpreter(service), *args],
        cwd=folder(service),
        env=execution_env,
        stdout=handle,
        stderr=subprocess.STDOUT,
        check=False,
    )
    handle.close()
    if result.returncode:
        print(
            "FAILED:",
            service,
            args[0],
            "See .local/" + (logname or f"{service}-command.log"),
        )
        raise SystemExit(result.returncode)
    return result


def databases():
    # Only create explicitly missing names in the isolated Docker Postgres. Never drop.
    for name in DATABASES.values():
        q = subprocess.check_output(
            [
                "docker",
                "compose",
                "--env-file",
                str(LOCAL / "compose.env"),
                "-f",
                str(ROOT / "docker-compose.local.yml"),
                "exec",
                "-T",
                "postgres",
                "psql",
                "-U",
                "postgres",
                "-tAc",
                f"SELECT 1 FROM pg_database WHERE datname='{name}'",
            ],
            text=True,
        ).strip()
        if q != "1":
            subprocess.run(
                [
                    "docker",
                    "compose",
                    "--env-file",
                    str(LOCAL / "compose.env"),
                    "-f",
                    str(ROOT / "docker-compose.local.yml"),
                    "exec",
                    "-T",
                    "postgres",
                    "createdb",
                    "-U",
                    "postgres",
                    name,
                ],
                check=True,
            )
    print("Seven separate databases ready; local postgres ownership retained.")


def migrate():
    databases()
    for service in DATABASES:
        args = (
            ["manage.py", "migrate", "--noinput"]
            if service == "organization"
            else ["-m", "alembic", "upgrade", "head"]
        )
        run(service, args, f"{service}-migration.log")
        run(
            service,
            ["manage.py", "showmigrations", "--plan"]
            if service == "organization"
            else ["-m", "alembic", "current"],
            f"{service}-migration-current.log",
        )
        print(service, "migration PASS")


def launch(service, label, args):
    pidfile = LOCAL / "processes.json"
    pids = json.loads(pidfile.read_text()) if pidfile.exists() else {}
    name = service + "-" + label
    if name in pids:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pids[name]}", "/FO", "CSV", "/NH"],
            capture_output=True,
            check=False,
            text=True,
        )
        if str(pids[name]) in result.stdout:
            print(name, "already running")
            return
    h = (LOCAL / (name + ".log")).open("a")
    p = subprocess.Popen(
        [interpreter(service), *args],
        cwd=folder(service),
        env=env(service),
        stdout=h,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    h.close()
    pids[name] = p.pid
    pidfile.write_text(json.dumps(pids, indent=2))
    print(name, "started")


def start():
    run("identity", [str(ROOT / "scripts/local/broker_setup.py")], "broker-setup.log")
    for i, s in enumerate(SERVICES):
        args = (
            ["manage.py", "runserver", "127.0.0.1:8000", "--noreload"]
            if s == "organization"
            else [
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(8000 + i),
                "--no-access-log",
            ]
        )
        launch(s, "api", args)
    for s, workers in WORKERS.items():
        for label, args in workers:
            launch(s, label, args)
    deadline = time.monotonic() + 60
    remaining = set(range(len(SERVICES)))
    while remaining and time.monotonic() < deadline:
        for index in list(remaining):
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{8000 + index}/health/ready", timeout=2
                ) as response:
                    if response.status == 200:
                        remaining.remove(index)
            except (OSError, TimeoutError):
                pass
        if remaining:
            time.sleep(0.5)
    if remaining:
        raise RuntimeError(
            "Local APIs not ready: " + ", ".join(SERVICES[i] for i in sorted(remaining))
        )
    print("All nine local APIs ready")


def tests():
    for s in SERVICES:
        run(
            s,
            ["-m", "pytest", "-q", f"--junitxml={LOCAL / s}-tests.xml"],
            s + "-tests.log",
        )
        print(s, "tests PASS")


def stop():
    pidfile = LOCAL / "processes.json"
    for name, pid in json.loads(pidfile.read_text()).items():
        command = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f'(Get-CimInstance Win32_Process -Filter "ProcessId={int(pid)}").CommandLine',
            ],
            text=True,
        )
        if not command.strip():
            continue
        expected = str(folder(name.split("-")[0])).replace("\\", "/").lower()
        if expected not in command.replace("\\", "/").lower():
            raise RuntimeError(f"Refusing to stop an unverified process: {name}")
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=True
        )
    pidfile.write_text("{}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "action",
        choices=[
            "prepare",
            "infra",
            "migrate",
            "start",
            "tests",
            "stop",
            "health",
            "seed",
            "restart",
        ],
    )
    a = p.parse_args().action
    if a == "prepare":
        prepare()
    elif a == "infra":
        compose("up", "-d", "--wait", "--wait-timeout", "180")
    elif a == "migrate":
        migrate()
    elif a == "start":
        start()
    elif a == "tests":
        tests()
    elif a == "seed":
        for s in ["identity", "organization"]:
            run(s, [str(ROOT / "scripts/local" / f"seed_{s}.py")], f"{s}-seed.log")
        print("Explicit local seed ready; invite-only policy unchanged")
    elif a == "restart":
        stop()
        start()
    elif a == "stop":
        stop()
    elif a == "health":
        for i, s in enumerate(SERVICES):
            for kind in ["live", "ready"]:
                try:
                    r = urllib.request.urlopen(
                        f"http://127.0.0.1:{8000 + i}/health/{kind}", timeout=5
                    )
                    print(s, kind, r.status)
                except (OSError, TimeoutError) as x:
                    print(s, kind, type(x).__name__)


if __name__ == "__main__":
    main()
