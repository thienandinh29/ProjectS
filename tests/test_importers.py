import codecs
from email.message import Message
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
import urllib.error
from docx import Document
from telex_app.importers import read_file, decode_text, docs_export_url, read_google_doc, ImportFailure, GoogleRedirects, MAX_BYTES

class Response(io.BytesIO):
    def __init__(self, data, kind="text/plain"):
        super().__init__(data)
        self.headers = Message()
        self.headers["Content-Type"] = kind

class ImportTests(unittest.TestCase):
    def test_unicode_encodings(self):
        text = "Đoàng\r\nTiếng Việt"
        for data in (text.encode("utf-8"), text.encode("utf-8-sig"), text.encode("utf-16"), codecs.BOM_UTF16_BE + text.encode("utf-16-be")):
            self.assertEqual(decode_text(data), "Đoàng\nTiếng Việt")

    def test_bad_encoding_and_binary(self):
        for data in (b"\xff\x81", b"a\x00b"):
            with self.assertRaises(ImportFailure):
                decode_text(data)

    def test_docx_in_document_order(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.docx"
            doc = Document()
            doc.add_paragraph("Đoàng")
            table = doc.add_table(rows=2, cols=2)
            table.cell(0, 0).text = "Tiếng"
            table.cell(0, 1).text = "Việt"
            table.cell(1, 0).merge(table.cell(1, 1)).text = "Hợp nhất"
            doc.add_paragraph("Kết thúc")
            doc.save(path)
            self.assertEqual(read_file(path), "Đoàng\nTiếng | Việt\nHợp nhất\nKết thúc")

    def test_file_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ("bad.docx", "old.doc", "typo.docs"):
                path = Path(directory) / name
                path.write_bytes(b"not a docx")
                with self.assertRaises(ImportFailure):
                    read_file(path)
            with self.assertRaises(ImportFailure):
                read_file(Path(directory) / "missing.txt")

    def test_link_parsing(self):
        self.assertEqual(docs_export_url("https://docs.google.com/document/d/ABC_123/edit?tab=t.0#heading=h.1"), "https://docs.google.com/document/d/ABC_123/export?format=txt")
        self.assertIn("/ABC/export", docs_export_url("https://docs.google.com/document/u/0/d/ABC/edit"))
        for url in ("http://docs.google.com/document/d/A", "https://docs.google.com.evil.com/document/d/A", "file:///etc/passwd", "https://docs.google.com/document/d/e/ABC/pub", "https://docs.google.com@evil.com/document/d/ABC"):
            with self.assertRaises(ImportFailure):
                docs_export_url(url)

    def test_public_import_success(self):
        opener = Mock()
        opener.open.return_value = Response("Tiếng Việt".encode())
        self.assertEqual(read_google_doc("https://docs.google.com/document/d/ABC/edit", opener), "Tiếng Việt")
        request = opener.open.call_args.args[0]
        self.assertNotIn("Cookie", request.headers)
        self.assertNotIn("Authorization", request.headers)

    def test_private_html_and_network_failures(self):
        opener = Mock()
        opener.open.return_value = Response(b"<html>Sign in</html>", "text/html")
        with self.assertRaises(ImportFailure):
            read_google_doc("https://docs.google.com/document/d/ABC/edit", opener)
        for error in (urllib.error.URLError("offline"), TimeoutError(), urllib.error.HTTPError("url", 403, "denied", {}, None)):
            opener.open.side_effect = error
            with self.assertRaises(ImportFailure):
                read_google_doc("https://docs.google.com/document/d/ABC/edit", opener)

    def test_response_size_limit(self):
        opener = Mock()
        opener.open.return_value = Response(b"a" * (MAX_BYTES + 1))
        with self.assertRaises(ImportFailure):
            read_google_doc("https://docs.google.com/document/d/ABC/edit", opener)

    def test_no_redirect_to_login_or_arbitrary_hosts(self):
        handler = GoogleRedirects()
        for url in ("https://accounts.google.com/login", "https://evil.com/", "http://docs.google.com/document"):
            with self.assertRaises(ImportFailure):
                handler.redirect_request(None, None, 302, "", {}, url)

if __name__ == "__main__":
    unittest.main()
