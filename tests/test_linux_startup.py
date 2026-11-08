import os
import subprocess
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import main


class StartupTests(unittest.TestCase):
    def test_configuration_defaults_and_secrets(self):
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test", "PORT": "4321"}, clear=True), \
             mock.patch.object(main, "load_dotenv"):
            env = main.configure()
        self.assertEqual(env["FOXPROFILE_API_PORT"], "4321")
        self.assertEqual(env["FOXPROFILE_URL"], "http://127.0.0.1:4321")
        self.assertEqual(env["FOXPROFILE_HEADLESS"], "true")
        self.assertEqual(Path(env["FOXPROFILE_UPLOAD_DIRS"]), main.ROOT / "Videos/downloads")

    def test_token_required_without_prompt(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(main, "load_dotenv"):
            with self.assertRaisesRegex(ValueError, "TELEGRAM_BOT_TOKEN"):
                main.configure()

    def test_child_exit_during_startup(self):
        proc = mock.Mock(returncode=3)
        proc.poll.return_value = 3
        with self.assertRaisesRegex(RuntimeError, "code 3"):
            main.wait_for_api(proc, "http://127.0.0.1:8090")

    def test_cancel_api_wait(self):
        proc = mock.Mock()
        self.assertFalse(main.wait_for_api(proc, "http://127.0.0.1:8090", cancelled=lambda: True))
        proc.poll.assert_not_called()

    def test_shutdown_terminates_and_reaps_children(self):
        children = [mock.Mock(), mock.Mock()]
        for child in children:
            child.poll.return_value = None
        main.stop_processes(children)
        for child in children:
            child.terminate.assert_called_once()
            child.wait.assert_called_once_with(timeout=15)

    def test_bot_no_token_exits_on_linux(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(main.ROOT / "muse_telebot", root / "muse_telebot",
                            ignore=shutil.ignore_patterns(".env", "*.log*", "*.lock", "__pycache__"))
            (root / "foxprofile").mkdir()
            shutil.copy(main.ROOT / "foxprofile/foxprofile_client.py", root / "foxprofile")
            shutil.copy(main.ROOT / ".env.example", root)
            env = os.environ.copy()
            env.pop("TELEGRAM_BOT_TOKEN", None)
            result = subprocess.run([sys.executable, "muse_telebot.py"], cwd=root / "muse_telebot",
                                    env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("TELEGRAM_BOT_TOKEN", result.stdout)
            self.assertNotIn("windll", result.stderr)


if __name__ == "__main__":
    unittest.main()
