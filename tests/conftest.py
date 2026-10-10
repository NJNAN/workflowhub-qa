import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import httpx
import pytest


@pytest.fixture(scope="session")
def service(tmp_path_factory):
    external = os.getenv("QA_BASE_URL")
    if external:
        accounts = json.loads(Path(os.environ["QA_ACCOUNTS_FILE"]).read_text(encoding="utf-8"))
        yield external, accounts
        return
    root = Path(
        os.getenv("WORKFLOWHUB_PATH", str(Path(__file__).resolve().parents[2] / "workflowhub"))
    )
    scratch = tmp_path_factory.mktemp("http-service")
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{scratch / 'service.db'}",
        "PYTHONPATH": str(root / "backend"),
    }
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    for command in [
        ["-m", "alembic", "upgrade", "head"],
        ["scripts/seed_demo.py", "--output", str(scratch / "accounts.json")],
    ]:
        result = subprocess.run(
            [sys.executable, *command],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            creationflags=flags,
        )
        assert result.returncode == 0, result.stderr
    log = (scratch / "service.log").open("w", encoding="utf-8")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "workflowhub.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=root,
        env=env,
        stdout=log,
        stderr=log,
        creationflags=flags,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        with httpx.Client(trust_env=False, timeout=1) as client:
            for _ in range(100):
                if process.poll() is not None:
                    raise AssertionError("Server stopped; inspect private temporary service.log")
                try:
                    if client.get(url + "/api/health").status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.2)
            else:
                raise AssertionError("Server did not become ready within 20 seconds")
        yield url, json.loads((scratch / "accounts.json").read_text(encoding="utf-8"))
    finally:
        process.terminate()
        process.wait(timeout=10)
        log.close()


@pytest.fixture
def client(service):
    with httpx.Client(base_url=service[0] + "/api/", trust_env=False, timeout=10) as client:
        yield client


def authenticate(client, service, username="requester"):
    response = client.post(
        "auth/login", json={"username": username, "password": service[1][username]}
    )
    assert response.status_code == 200
    client.headers["Authorization"] = "Bearer " + response.json()["access_token"]


def ticket(client, title="HTTP regression"):
    response = client.post("tickets", json={"title": title, "description": "Created via real HTTP"})
    assert response.status_code == 201
    return response.json()
