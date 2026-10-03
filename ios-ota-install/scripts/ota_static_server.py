#!/usr/bin/env python3
"""Static file server for OTA install pages, bound to localhost only. Tailscale Serve fronts it with HTTPS."""
import argparse
import functools
import http.server

TYPES = {".plist": "text/xml", ".ipa": "application/octet-stream", ".html": "text/html; charset=utf-8"}


class Handler(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path):
        for suffix, mime in TYPES.items():
            if str(path).endswith(suffix):
                return mime
        return super().guess_type(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    handler = functools.partial(Handler, directory=args.root)
    http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
