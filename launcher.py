#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTTP server, API and entry point for GGUF Launcher."""

import json
import os
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import gguf_core as core
import gguf_ui


VERSION = core.VERSION
MAX_REQUEST_BYTES = 256 * 1024
ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def _send(self, code, body, content_type="application/json; charset=utf-8"):
        data = (
            body
            if isinstance(body, bytes)
            else json.dumps(body, ensure_ascii=False).encode("utf-8")
        )

        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        try:
            self.wfile.write(data)
        except OSError:
            pass

    def _body(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)

            if length < 0 or length > MAX_REQUEST_BYTES:
                return {}

            raw = self.rfile.read(length)
            value = json.loads(raw or b"{}")

            return value if isinstance(value, dict) else {}
        except (ValueError, TypeError, json.JSONDecodeError):
            return {}

    def do_GET(self):
        try:
            self._route_get()
        except Exception as exc:
            core.log_report("GET error: %s" % self.path, exc)
            self._send(500, {"error": "internal server error"})

    def _route_get(self):
        path = urllib.parse.urlparse(self.path).path

        if path == "/":
            self._send(
                200,
                gguf_ui.HTML.encode("utf-8"),
                "text/html; charset=utf-8",
            )
            return

        if path == "/api/status":
            ram = core.ram_available_gb()

            self._send(
                200,
                {
                    "python_ok": True,
                    "python_short": core.python_short(),
                    "version": VERSION,
                    "gpu": core.gpu_info(),
                    "ram_gb": round(ram, 1) if ram is not None else None,
                    "llama": core.llama_info(),
                    "install": core.install_status(),
                    "server": {
                        "running": core.SERVER_MGR.running(),
                        "url": core.SERVER_MGR.url,
                    },
                    "platform": sys.platform,
                    "report_path": core.REPORT_PATH,
                },
            )
            return

        if path == "/api/disks":
            self._send(
                200,
                {
                    "disks": core.list_disks(),
                    "known": core.known_model_dirs(),
                },
            )
            return

        if path == "/api/scan":
            self._send(200, core.scan_status())
            return

        if path == "/api/scan_results":
            self._send(200, {"models": core.scan_results()})
            return

        if path == "/api/install":
            self._send(200, core.install_status())
            return

        if path == "/api/log":
            self._send(
                200,
                {
                    "running": core.SERVER_MGR.running(),
                    "lines": list(core.SERVER_MGR.log)[-120:],
                },
            )
            return

        if path == "/api/help":
            self._send(
                200,
                {
                    "help": core.HELP_TEXT,
                    "version": VERSION,
                },
            )
            return

        if path == "/api/reports/tail":
            self._send(
                200,
                {
                    "path": core.REPORT_PATH,
                    "lines": core.tail_reports(200),
                },
            )
            return

        self._send(404, {"error": "not found"})

    def do_POST(self):
        try:
            self._route_post()
        except Exception as exc:
            core.log_report("POST error: %s" % self.path, exc)
            self._send(500, {"error": "internal server error"})

    def _route_post(self):
        path = urllib.parse.urlparse(self.path).path
        payload = self._body()

        if path == "/api/scan":
            self._send(200, core.start_scan(payload.get("path", "")))
            return

        if path == "/api/scan/stop":
            self._send(200, core.stop_scan())
            return

        if path == "/api/analyze":
            model_path = str(payload.get("path", ""))

            if not os.path.isfile(model_path):
                self._send(200, {"error": "file not found: " + model_path})
            else:
                self._send(200, core.analyze_model(model_path))
            return

        if path == "/api/run":
            self._send(200, self._api_run(payload))
            return

        if path == "/api/stop":
            core.SERVER_MGR.stop()
            self._send(200, {"ok": True})
            return

        if path == "/api/config":
            llama_dir = payload.get("llama_dir")

            if not isinstance(llama_dir, str) or not llama_dir.strip():
                self._send(400, {"error": "llama_dir is required"})
                return

            config = core.load_config()
            config["llama_dir"] = os.path.abspath(
                os.path.expanduser(llama_dir.strip())
            )
            core.save_config(config)

            self._send(
                200,
                {
                    "ok": True,
                    "llama": core.llama_info(),
                },
            )
            return

        if path == "/api/install":
            if core.install_status()["active"]:
                self._send(200, {"error": "installation is already running"})
            else:
                threading.Thread(
                    target=core.install_llama,
                    name="llama-install",
                    daemon=True,
                ).start()
                self._send(200, {"started": True})
            return

        self._send(404, {"error": "not found"})

    def _api_run(self, payload):
        model_path = str(payload.get("path", ""))

        if not model_path or not os.path.isfile(model_path):
            return {"error": "select a model"}

        llama = core.llama_info()

        if not llama["found"]:
            return {"error": "llama.cpp was not found"}

        try:
            context = int(payload.get("ctx") or 8192)
            gpu_layers = int(payload.get("ngl") or 0)
        except (ValueError, TypeError):
            return {"error": "invalid numeric parameters"}

        if context < 512 or context > 1_000_000:
            return {"error": "context must be between 512 and 1000000"}

        if gpu_layers < 0 or gpu_layers > 999:
            return {"error": "GPU layers must be between 0 and 999"}

        host = str(payload.get("host") or "127.0.0.1").strip()

        if host not in ALLOWED_HOSTS:
            return {
                "error": "host must be 127.0.0.1, localhost or ::1"
            }

        port = core.free_port(8080)

        args = [
            "-m",
            os.path.abspath(model_path),
            "-c",
            str(context),
            "-ngl",
            str(gpu_layers),
            "--host",
            host,
            "--port",
            str(port),
        ]

        result = core.SERVER_MGR.start(llama["exe"], args)

        if result.get("error"):
            core.log_report(
                "Could not start server: " + result["error"],
                extra="model=%s" % model_path,
            )

        return result


def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        core.print_help()
        return 0

    if "--version" in args:
        print("GGUF Launcher " + VERSION)
        return 0

    no_browser = "--no-browser" in args

    core.install_exception_hooks()
    core.log_report(
        "Launcher started",
        extra=(
            "version=%s python=%s platform=%s cwd=%s report=%s"
            % (
                VERSION,
                core.python_short(),
                sys.platform,
                os.getcwd(),
                core.REPORT_PATH,
            )
        ),
    )

    port = core.free_port(8765)

    try:
        http_server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as exc:
        core.log_report("Could not open HTTP port %s" % port, exc)
        print("Could not start HTTP server on port %d: %s" % (port, exc))
        print("See reports.txt for details.")
        return 1

    url = "http://127.0.0.1:%d" % port

    print("=" * 52)
    print("  GGUF Launcher v%s started: %s" % (VERSION, url))
    print("  Help:             python launcher.py --help")
    print("  Error log:        reports.txt")
    print("  Do not close this window.")
    print("=" * 52)

    if not no_browser:
        threading.Timer(
            0.8,
            lambda: webbrowser.open(url),
        ).start()

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        core.log_report("HTTP server failure", exc)
        return 1
    finally:
        try:
            http_server.server_close()
        except Exception:
            pass

        try:
            core.SERVER_MGR.stop()
        except Exception as exc:
            core.log_report("Error stopping llama-server", exc)

        core.log_report("Launcher stopped")

    return 0


if __name__ == "__main__":
    sys.exit(main())
