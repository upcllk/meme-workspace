import importlib.util
import json
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export.py"
spec = importlib.util.spec_from_file_location("share_export", SCRIPT)
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class ExportTests(unittest.TestCase):
    def test_validate_urls(self):
        self.assertEqual(exporter.parse_url("https://chatgpt.com/s/cx_abc"), ("codex", "cx_abc"))
        for url in ("https://evil.example/s/cx_abc", "https://chatgpt.com/c/abc",
                    "https://chatgpt.com/s/cx_abc?x=1"):
            with self.subTest(url=url), self.assertRaises(exporter.ExportError):
                exporter.parse_url(url)

    def test_redirect_allowlist(self):
        request = urllib.request.Request("https://chatgpt.com/file")
        handler = exporter.SameHostRedirect(allow_assets=True)
        allowed = handler.redirect_request(request, None, 302, "Found", {},
                                           "https://foo.oaiusercontent.com/file")
        self.assertEqual(allowed.full_url, "https://foo.oaiusercontent.com/file")
        with self.assertRaises(exporter.ExportError):
            handler.redirect_request(request, None, 302, "Found", {}, "https://evil.example/file")
        with self.assertRaises(exporter.ExportError):
            exporter.SameHostRedirect().redirect_request(
                request, None, 302, "Found", {}, "https://foo.oaiusercontent.com/file")

    def test_chat_filters_tool_messages_and_marks_attachments(self):
        def node(role, text, recipient="all", metadata=None):
            return {"message": {"author": {"role": role}, "recipient": recipient,
                                "metadata": metadata or {}, "content": {"parts": [text]}}}
        data = {"title": "test", "linear_conversation": [
            node("user", "question"), node("assistant", "tool request", "web.run"),
            node("assistant", "thinking", metadata={"is_thinking_preamble_message": True}),
            node("assistant", "answer")]}
        text = exporter.chat_markdown(data)
        self.assertIn("question", text)
        self.assertIn("answer", text)
        self.assertNotIn("tool request", text)
        self.assertNotIn("thinking", text)
        found = exporter.collect_chat_attachments({"parts": [{"asset_pointer": "file-x"}]})
        self.assertEqual(found[0]["status"], "unresolved")

    def test_share_table_and_unsupported_references(self):
        table = [{"_1": 2}, "name", "value"]
        self.assertEqual(exporter.decode_table(table, 0), {"name": "value"})
        self.assertIsNone(exporter.decode_table(table, -5))
        with self.assertRaises(exporter.ExportError):
            exporter.decode_table(table, -2)

    def test_codex_download_and_missing_attachment(self):
        url = "https://chatgpt.com/s/cx_test"
        data = {"title": "example", "assets": {"asset-1": {}, "asset-2": {}},
                "turns": [{"items": [
                    {"type": "userMessage", "content": [
                        {"type": "text", "text": "hello"},
                        {"type": "image", "url": "codex:shared-asset/asset-1"}]},
                    {"type": "imageView", "url": "codex:shared-asset/asset-1"},
                    {"type": "imageGeneration", "status": "completed",
                     "result": "codex:shared-asset/asset-1"},
                    {"type": "fileChange", "changes": [{"path": "file.txt"}], "content": "full diff"}]}]}

        def fake_fetch(target, allow_assets=False):
            if target.endswith("asset-1"):
                return b"image bytes", "image/jpeg"
            if target.endswith("asset-2"):
                raise exporter.ExportError("denied")
            return json.dumps(data).encode(), "application/json"

        with tempfile.TemporaryDirectory() as temp, patch.object(exporter, "fetch", side_effect=fake_fetch):
            dest = Path(temp) / "output"
            result = exporter.export(url, dest)
            self.assertEqual([x["status"] for x in result["attachments"]], ["downloaded", "failed"])
            self.assertEqual(json.loads((dest / "source.json").read_text()), data)
            self.assertEqual((dest / "attachments/asset-1.jpg").read_bytes(), b"image bytes")
            markdown = (dest / "conversation.md").read_text()
            self.assertEqual(markdown.count("![附件](attachments/asset-1.jpg)"), 3)
            self.assertIn('"result": "codex:shared-asset/asset-1"', markdown)
            self.assertIn("file.txt", markdown)
            self.assertIn('"content": "full diff"', markdown)
            self.assertTrue(result["warnings"])
            with self.assertRaises(exporter.ExportError):
                exporter.export(url, dest)

    def test_unlisted_image_is_reported(self):
        data = {"assets": {}, "turns": [{"items": [
            {"type": "userMessage", "content": [{"type": "image", "url": "unknown"}]},
            {"type": "imageView", "url": "codex:shared-asset/missing"},
            {"type": "imageGeneration", "result": "codex:shared-image-unavailable/1"},
            {"type": "imageGeneration", "status": "pending", "result": None}]}]}
        with tempfile.TemporaryDirectory() as temp, patch.object(
                exporter, "fetch", return_value=(json.dumps(data).encode(), "application/json")):
            result = exporter.export("https://chatgpt.com/s/cx_test", Path(temp) / "output")
            self.assertEqual([x["status"] for x in result["attachments"]], ["unresolved"] * 3)
            self.assertEqual(result["attachments"][2]["reason"], "分享源标记图片不可用")
            self.assertTrue(result["warnings"])


if __name__ == "__main__":
    unittest.main()
