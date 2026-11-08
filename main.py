"""Run FoxProfile, the Telegram bot and AutoPost as one supervised workload."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent


def configure() -> dict[str, str]:
    load_dotenv(ROOT / ".env")  # Existing platform secrets take precedence.
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.setdefault("FOXPROFILE_API_HOST", "127.0.0.1")
    env.setdefault("FOXPROFILE_API_PORT", env.get("PORT", "8090"))
    env.setdefault("FOXPROFILE_HEADLESS", "true")
    env.setdefault("FOXPROFILE_UPLOAD_DIRS", str(ROOT / "Videos" / "downloads"))
    env.setdefault("FOXPROFILE_URL", f"http://127.0.0.1:{env['FOXPROFILE_API_PORT']}")
    env.setdefault("FOXPROFILE_ENV_FILE", str(ROOT / ".env"))
    env["NO_PROXY"] = ",".join(filter(None, (env.get("NO_PROXY", ""), "127.0.0.1", "localhost")))
    if not env.get("TELEGRAM_BOT_TOKEN", "").strip():
        raise ValueError("TELEGRAM_BOT_TOKEN is required (set it in the environment).")
    return env


def wait_for_api(proc: subprocess.Popen, url: str, timeout: float = 60, cancelled=lambda: False) -> bool:
    opener = build_opener(ProxyHandler({}))
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if cancelled():
            return False
        if proc.poll() is not None:
            raise RuntimeError(f"FoxProfile exited during startup (code {proc.returncode}).")
        try:
            with opener.open(url + "/api/v1/health", timeout=2) as response:
                if response.status == 200:
                    return True
        except (OSError, URLError):
            pass
        time.sleep(0.5)
    raise RuntimeError("Timed out waiting for FoxProfile health check.")


def stop_processes(processes: list[subprocess.Popen]) -> None:
    for proc in reversed(processes):
        if proc.poll() is None:
            proc.terminate()
    for proc in reversed(processes):
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def main() -> int:
    processes: list[subprocess.Popen] = []
    stopping = False

    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        env = configure()
        data = ROOT / "foxprofile" / "data"
        data.mkdir(parents=True, exist_ok=True)
        print("Starting FoxProfile...", flush=True)
        server = subprocess.Popen([sys.executable, str(ROOT / "foxprofile/repo/src/server.py")], cwd=data, env=env)
        processes.append(server)
        ready = wait_for_api(server, f"http://127.0.0.1:{env['FOXPROFILE_API_PORT']}",
                             cancelled=lambda: stopping)
        if not ready or stopping:
            return 0
        for name, folder, script in (("Telegram bot", "muse_telebot", "muse_telebot.py"),
                                     ("AutoPost", "social_post", "auto_post.py")):
            print(f"Starting {name}...", flush=True)
            processes.append(subprocess.Popen([sys.executable, script], cwd=ROOT / folder, env=env))
        while not stopping:
            for proc in processes:
                if proc.poll() is not None:
                    raise RuntimeError(f"Process {proc.args} exited (code {proc.returncode}).")
            time.sleep(0.5)
        return 0
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"Startup/runtime error: {exc}", file=sys.stderr, flush=True)
        return 1
    finally:
        stop_processes(processes)


if __name__ == "__main__":
    sys.exit(main())
