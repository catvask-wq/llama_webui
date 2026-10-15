#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GGUF Launcher: HTTP-сервер, API и точка входа.

Запуск:  python launcher.py [--help|--version|--no-browser]
"""

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

# ============================================================ HTTP handler

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    # ---------- отправка ----------

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else \
            json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(data)
        except Exception:
            pass

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return {}

    # ---------- GET ----------

    def do_GET(self):
        try:
            self._route_get()
        except Exception as e:
            core.log_report("Ошибка обработки GET %s" % self.path, e)
            try:
                self._send(500, {"error": "internal server error: " + str(e)})
            except Exception:
                pass

    def _route_get(self):
        path = urllib.parse.urlparse(self.path).path

        if path == "/":
            self._send(200, gguf_ui.HTML.encode("utf-8"),
                       "text/html; charset=utf-8")
            return

        if path == "/api/status":
            ram = core.ram_available_gb()
            self._send(200, {
                "python_ok": True,
                "python_short": core.python_short(),
                "version": VERSION,
                "gpu": core.gpu_info(),
                "ram_gb": round(ram, 1) if ram is not None else None,
                "llama": core.llama_info(),
                "install": {k: core.INSTALL[k] for k in
                            ("active", "stage", "pct", "message", "error")},
                "server": {"running": core.SERVER_MGR.running(),
                           "url": core.SERVER_MGR.url},
                "platform": sys.platform,
                "report_path": core.REPORT_PATH,
            })
            return

        if path == "/api/disks":
            self._send(200, {"disks": core.list_disks(),
                             "known": core.known_model_dirs()})
            return

        if path == "/api/scan":
            self._send(200, {"running": core.SCAN["running"],
                             "done": core.SCAN["done"],
                             "current": core.SCAN["current"],
                             "count": len(core.SCAN["found"])})
            return

        if path == "/api/scan_results":
            self._send(200, {"models": list(core.SCAN["found"])})
            return

        if path == "/api/install":
            self._send(200, {k: core.INSTALL[k] for k in
                             ("active", "stage", "pct", "message", "error")})
            return

        if path == "/api/log":
            self._send(200, {"running": core.SERVER_MGR.running(),
                             "lines": list(core.SERVER_MGR.log)[-120:]})
            return

        if path == "/api/help":
            self._send(200, {"help": core.HELP_TEXT, "version": VERSION})
            return

        if path == "/api/reports/tail":
            self._send(200, {"path": core.REPORT_PATH,
                             "lines": core.tail_reports(200)})
            return

        self._send(404, {"error": "not found"})

    # ---------- POST ----------

    def do_POST(self):
        try:
            self._route_post()
        except Exception as e:
            core.log_report("Ошибка обработки POST %s" % self.path, e)
            try:
                self._send(500, {"error": "internal server error: " + str(e)})
            except Exception:
                pass

    def _route_post(self):
        path = urllib.parse.urlparse(self.path).path
        p = self._body()

        if path == "/api/scan":
            self._send(200, core.start_scan(p.get("path", "")))
            return

        if path == "/api/scan/stop":
            core.SCAN["stop"] = True
            self._send(200, {"ok": True})
            return

        if path == "/api/analyze":
            mp = p.get("path", "")
            if not os.path.isfile(mp):
                self._send(200, {"error": "файл не найден: " + mp})
            else:
                self._send(200, core.analyze_model(mp))
            return

        if path == "/api/run":
            self._send(200, self._api_run(p))
            return

        if path == "/api/stop":
            core.SERVER_MGR.stop()
            self._send(200, {"ok": True})
            return

        if path == "/api/config":
            cfg = core.load_config()
            if p.get("llama_dir"):
                cfg["llama_dir"] = p["llama_dir"]
                core.save_config(cfg)
            self._send(200, {"ok": True, "llama": core.llama_info()})
            return

        if path == "/api/install":
            if core.INSTALL["active"]:
                self._send(200, {"error": "установка уже идёт"})
            else:
                threading.Thread(target=core.install_llama, daemon=True).start()
                self._send(200, {"started": True})
            return

        self._send(404, {"error": "not found"})

    # ---------- бизнес-логика запуска ----------

    def _api_run(self, p):
        mp = p.get("path", "")
        if not mp or not os.path.isfile(mp):
            return {"error": "выберите модель"}
        info = core.llama_info()
        if not info["found"]:
            return {"error": "llama.cpp не найден — установите его на шаге 1"}
        try:
            ctx = int(p.get("ctx") or 8192)
            ngl = int(p.get("ngl") or 0)
        except (ValueError, TypeError):
            return {"error": "некорректные числа в параметрах"}
        host = p.get("host") or "127.0.0.1"
        port = core.free_port(8080)
        args = ["-m", mp, "-c", str(ctx), "-ngl", str(ngl),
                "--host", host, "--port", str(port)]
        result = core.SERVER_MGR.start(info["exe"], args)
        if result.get("error"):
            core.log_report("Не удалось запустить сервер: " + result["error"],
                            extra="model=" + mp)
        return result

# ============================================================ точка входа

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
    core.log_report("Запуск лаунчера",
                    extra="version=%s python=%s platform=%s cwd=%s report=%s"
                          % (VERSION, core.python_short(), sys.platform,
                             os.getcwd(), core.REPORT_PATH))

    port = core.free_port(8765)
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as e:
        core.log_report("Не удалось открыть HTTP-порт %s" % port, e)
        print("Не удалось запустить HTTP-сервер на порту %d: %s" % (port, e))
        print("Подробности в reports.txt")
        return 1

    url = "http://127.0.0.1:%d" % port
    print("=" * 52)
    print("  GGUF Launcher v%s запущен: %s" % (VERSION, url))
    print("  Справка:          python launcher.py --help")
    print("  Журнал ошибок:    reports.txt")
    print("  Не закрывайте это окно.")
    print("=" * 52)

    if not no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        core.log_report("Сбой HTTP-сервера", e)
        return 1
    finally:
        try:
            core.SERVER_MGR.stop()
        except Exception as e:
            core.log_report("Ошибка при остановке llama-server", e)
        core.log_report("Остановка лаунчера")
    return 0


if __name__ == "__main__":
    sys.exit(main())