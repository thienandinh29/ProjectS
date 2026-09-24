"""Local file and anonymous Google Docs text imports. No account/session access."""
from pathlib import Path
import codecs
import re
import urllib.request
import urllib.error
from urllib.parse import urlparse
import zipfile
from .telex import normalize

MAX_BYTES = 10 * 1024 * 1024
MAX_CHARS = 100_000

class ImportFailure(ValueError):
    pass

def checked_text(text):
    text = normalize(text)
    if len(text) > MAX_CHARS:
        raise ImportFailure("Nội dung vượt quá 100.000 ký tự. Hãy chia thành các phần nhỏ.")
    if "\x00" in text:
        raise ImportFailure("Tệp chứa dữ liệu nhị phân, không phải văn bản Unicode.")
    return text

def decode_text(data):
    try:
        if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
            text = data.decode("utf-16")
        else:
            text = data.decode("utf-8-sig")
    except UnicodeError as error:
        raise ImportFailure("Không đọc được mã chữ. Hãy lưu lại tệp bằng UTF-8 hoặc UTF-16 có BOM; không dùng VNI/TCVN3.") from error
    return checked_text(text)

def read_file(path):
    path = Path(path)
    try:
        if path.stat().st_size > MAX_BYTES:
            raise ImportFailure("Tệp lớn hơn 10 MB. Hãy chia nhỏ trước khi nhập.")
        suffix = path.suffix.lower()
        if suffix == ".txt":
            return decode_text(path.read_bytes())
        if suffix != ".docx":
            raise ImportFailure("Chỉ hỗ trợ .txt và .docx. Hãy lưu tệp .doc/.docs thành .docx.")
        from docx import Document
        from docx.table import Table
        from docx.text.paragraph import Paragraph
        with zipfile.ZipFile(path) as archive:
            if sum(i.file_size for i in archive.infolist()) > 50 * 1024 * 1024:
                raise ImportFailure("Tệp Word giải nén quá lớn.")
        doc = Document(path)
        blocks = []
        for block in doc.iter_inner_content():
            if isinstance(block, Paragraph):
                blocks.append(block.text)
            elif isinstance(block, Table):
                for row in block.rows:
                    cells, seen = [], set()
                    for cell in row.cells:
                        if cell._tc not in seen:
                            seen.add(cell._tc)
                            cells.append(cell.text)
                    blocks.append(" | ".join(cells))
        return checked_text("\n".join(blocks))
    except ImportFailure:
        raise
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        raise ImportFailure("Không mở được tệp. Kiểm tra tệp có hợp lệ và không được mã hóa/mật khẩu.") from error
    except Exception as error:
        raise ImportFailure("Không đọc được cấu trúc tệp Word. Hãy xuất thành .txt rồi nhập lại.") from error

def docs_export_url(url):
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or parsed.hostname != "docs.google.com" or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ImportFailure("Dán liên kết HTTPS của tài liệu tại docs.google.com.")
    match = re.fullmatch(r"/document/(?:u/\d+/)?d/([A-Za-z0-9_-]+)(?:/[^?#]*)?", parsed.path)
    if not match or match.group(1) == "e":
        raise ImportFailure("Cần liên kết tài liệu dạng docs.google.com/document/d/…; liên kết xuất bản chưa hỗ trợ.")
    return f"https://docs.google.com/document/d/{match.group(1)}/export?format=txt"

class GoogleRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlparse(newurl)
        host = parsed.hostname or ""
        if parsed.scheme != "https" or not (host == "docs.google.com" or host.endswith(".googleusercontent.com")):
            raise ImportFailure("Liên kết yêu cầu đăng nhập. Hãy tải tài liệu thành .docx hoặc .txt và mở tệp đó.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def read_google_doc(url, opener=None):
    export = docs_export_url(url)
    opener = opener or urllib.request.build_opener(GoogleRedirects())
    request = urllib.request.Request(export, headers={"User-Agent": "GoViet/1.0", "Accept": "text/plain"})
    try:
        with opener.open(request, timeout=20) as response:
            kind = response.headers.get_content_type()
            if kind != "text/plain":
                raise ImportFailure("Google không trả về văn bản. Với tài liệu riêng tư/hạn chế tải xuống, hãy tự tải .docx hoặc .txt rồi nhập.")
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ImportFailure("Tài liệu lớn hơn 10 MB.")
            return decode_text(data)
    except ImportFailure:
        raise
    except urllib.error.HTTPError as error:
        raise ImportFailure("Không tải được tài liệu. Liên kết phải đọc và tải được khi chưa đăng nhập. Có thể nhập .docx/.txt thay thế.") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ImportFailure("Không kết nối được Google Docs. Kiểm tra mạng hoặc nhập tệp .docx/.txt.") from error
