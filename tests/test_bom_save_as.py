import ast
import base64
import hashlib
import html
import json
import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MATCHER_PATH = ROOT / "component_matcher.py"
WORKER_PATH = ROOT / "cloudflare-pages-proxy" / "dist" / "_worker.js"


class BomSaveAsSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matcher = MATCHER_PATH.read_text(encoding="utf-8")
        cls.worker = WORKER_PATH.read_text(encoding="utf-8")

    def test_bom_result_uses_the_save_as_component(self):
        start = self.matcher.index('download_key_source = f"{workbook_signature}')
        end = self.matcher.index("clickable_bom_html = render_clickable_result_table", start)
        download_block = self.matcher[start:end]
        self.assertIn("components.html(", download_block)
        self.assertIn("build_bom_download_footer_html(", download_block)
        self.assertIn("bridge_channel=get_query_param_text(MEMBER_AUTH_BRIDGE_CHANNEL_PARAM)", download_block)
        self.assertNotIn("st.download_button(", download_block)

    def test_save_as_component_has_picker_and_download_fallback(self):
        start = self.matcher.index("def build_bom_download_footer_html(")
        end = self.matcher.index("\ndef get_query_param_text", start)
        helper = self.matcher[start:end]
        self.assertIn("showSaveFilePicker", helper)
        self.assertIn('source: "fruition-file-save"', helper)
        self.assertIn("browserDownload(blob)", helper)
        self.assertIn('error.name === "AbortError"', helper)
        self.assertIn('status === "canceled"', helper)

    def test_generated_component_replaces_markers_and_escapes_script_text(self):
        tree = ast.parse(self.matcher)
        function = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "build_bom_download_footer_html"
        )
        namespace = {
            "base64": base64,
            "hashlib": hashlib,
            "html": html,
            "json": json,
            "clean_text": lambda value: str(value or "").strip(),
            "MEMBER_AUTH_OUTER_SHELL_ORIGIN": "https://fruition-component.pages.dev",
        }
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(MATCHER_PATH), "exec"), namespace)
        generated = namespace["build_bom_download_footer_html"](
            b"xlsx",
            'report</script><script>alert("x")</script>.xlsx',
            bridge_channel="channel-123",
        )
        self.assertNotIn("__DATA_BASE64_JSON__", generated)
        self.assertNotIn("</script><script>", generated)
        self.assertIn("\\u003c/script\\u003e", generated)
        self.assertIn(base64.b64encode(b"xlsx").decode("ascii"), generated)

    def test_formal_shell_validates_channel_before_saving(self):
        listener = re.search(
            r'window\.addEventListener\("message".*?\n\s*}\);',
            self.worker,
            re.DOTALL,
        )
        self.assertIsNotNone(listener)
        listener_text = listener.group(0)
        source_check = listener_text.index('payload.source === "fruition-file-save"')
        channel_check = listener_text.index("payload.channel !== authBridgeChannel", source_check)
        handler_call = listener_text.index("handleFileSaveRequest", channel_check)
        self.assertLess(source_check, channel_check)
        self.assertLess(channel_check, handler_call)

    def test_formal_shell_uses_picker_with_safe_fallback(self):
        self.assertIn('typeof window.showSaveFilePicker === "function"', self.worker)
        self.assertIn("await window.showSaveFilePicker(", self.worker)
        self.assertIn('error.name === "AbortError"', self.worker)
        self.assertIn("startBrowserDownload(blob, filename)", self.worker)
        self.assertIn('respondToFileSaveRequest(event, "saved")', self.worker)


if __name__ == "__main__":
    unittest.main(verbosity=2)
