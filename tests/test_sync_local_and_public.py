from __future__ import annotations

import inspect
import subprocess
import unittest
from unittest import mock

import sync_local_and_public as sync


class PublishBranchTests(unittest.TestCase):
    def test_main_refreshes_release_stamp_independently_of_bundle_rebuild(self):
        source = inspect.getsource(sync.main)
        bundle_call = source.index("build_cloud_bundle(python_cmd, args.skip_bundle_rebuild)")
        stamp_call = source.index("refresh_public_release_stamp()")
        validation_call = source.index("validate_python_files(python_cmd)")
        self.assertLess(bundle_call, stamp_call)
        self.assertLess(stamp_call, validation_call)
        self.assertNotIn("if bundle_rebuilt:", source)

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
