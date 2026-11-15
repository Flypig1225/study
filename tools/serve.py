#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""支持 HTTP Range 的静态文件服务器（标准库实现）。

python -m http.server 是 HTTP/1.0 且不支持 Range，手机浏览器与 Chrome 内置
PDF 预览器因此会一直白屏/卡在加载中。这个脚本补上：
  * HTTP/1.1
  * Accept-Ranges: bytes
  * Range 请求返回 206 + Content-Range
  * 正确的 Content-Type（含 PDF / 图片 / HTML）

用法：
    python3 tools/serve.py [端口] [根目录]
"""
import email.utils
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.abspath(".")
PORT = 8080

MIME = {
    ".pdf": "application/pdf",
    ".html": "text/html; charset=utf-8",
    ".htm": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/plain; charset=utf-8",
}

RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "study-serve/1.0"

    def log_message(self, fmt, *args):  # 简洁日志
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _resolve(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        from urllib.parse import unquote
        path = unquote(path)
        if path.endswith("/"):
            path += "index.html"
        full = os.path.abspath(os.path.join(ROOT, path.lstrip("/")))
        if not full.startswith(ROOT):
            return None
        return full if os.path.isfile(full) else None

    def _headers(self, code, length, ctype, extra=None, last_modified=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-cache")
        if last_modified is not None:
            self.send_header("Last-Modified", last_modified)
        for k, v in (extra or []):
            self.send_header(k, v)
        self.end_headers()

    def do_HEAD(self):
        self._serve(body=False)

    def do_GET(self):
        self._serve(body=True)

    def _serve(self, body=True):
        full = self._resolve()
        if not full:
            msg = b"404 Not Found"
            self._headers(404, len(msg), "text/plain; charset=utf-8")
            if body:
                self.wfile.write(msg)
            return

        size = os.path.getsize(full)
        ctype = MIME.get(os.path.splitext(full)[1].lower(), "application/octet-stream")
        lm = email.utils.formatdate(os.path.getmtime(full), usegmt=True)

        rng = self.headers.get("Range")
        m = RANGE_RE.match(rng.strip()) if rng else None

        if m:
            start_s, end_s = m.group(1), m.group(2)
            if start_s == "":                      # bytes=-N 取末尾 N 字节
                length = int(end_s or 0)
                start = max(0, size - length)
                end = size - 1
            else:
                start = int(start_s)
                end = int(end_s) if end_s else size - 1
                end = min(end, size - 1)
            if start > end or start >= size:
                self._headers(416, 0, ctype,
                              [("Content-Range", "bytes */%d" % size)])
                return
            length = end - start + 1
            self._headers(206, length, ctype,
                          [("Content-Range", "bytes %d-%d/%d" % (start, end, size))], lm)
            if body:
                with open(full, "rb") as f:
                    f.seek(start)
                    self.wfile.write(f.read(length))
            return

        self._headers(200, size, ctype, last_modified=lm)
        if body:
            with open(full, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)


def main():
    global ROOT, PORT
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])
    if len(sys.argv) > 2:
        ROOT = os.path.abspath(sys.argv[2])
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("serving %s on http://0.0.0.0:%d (HTTP/1.1, Range enabled)" % (ROOT, PORT))
    srv.serve_forever()


if __name__ == "__main__":
    main()
