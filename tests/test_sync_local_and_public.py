from __future__ import annotations

import subprocess
import unittest
from unittest import mock

import sync_local_and_public as sync


class PublishBranchTests(unittest.TestCase):
    def test_publish_uses_tracked_remote_branch(self):
        upstream = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="origin/main\n",
            stderr="",
        )

        with mock.patch.object(sync, "run_command", return_value=upstream):
            self.assertEqual(sync.get_default_branch(), "main")

    def test_publish_falls_back_to_current_branch_without_upstream(self):
        current = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="codex/local-work\n",
            stderr="",
        )

        with mock.patch.object(
            sync,
            "run_command",
            side_effect=[RuntimeError("no upstream"), current],
        ):
            self.assertEqual(sync.get_default_branch(), "codex/local-work")


if __name__ == "__main__":
    unittest.main()
