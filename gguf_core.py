#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ядро GGUF Launcher: окружение, парсер GGUF, сканер, установка llama.cpp,
менеджер llama-server, журнал ошибок и справка."""

import json
import os
import re
import shutil
import socket
import string
import struct
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
import zipfile
from collections import deque

VERSION = "1.2"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "launcher_config.json")
REPORT_PATH = os.path.join(APP_DIR, "reports.txt")
MAX_SCAN_DEPTH = 8
REPORT_MAX_BYTES = 2 * 1024 * 1024  # после этого reports.txt ротируется в .1

SKIP_DIRS = {
    "$recycle.bin", "windows", "program files", "program files (x86)",
    "programdata", "appdata", "system volume information", "node_modules",
    ".git", "site-packages", "perflogs", "recovery", "$winreagent",
    "anaconda3", "miniconda3", "conda", "__pycache__", ".venv", "venv",
}

# ============================================================ журнал ошибок

def log_report(context, exc=None, extra=""):
    """Дописывает запись в reports.txt. Никогда не бросает исключений."""
    try:
        if os.path.exists(REPORT_PATH) and os.path.getsize(REPORT_PATH) > REPORT_MAX_BYTES:
            bak = REPORT_PATH + ".1"
            try:
                if os.path.exists(bak):
                    os.remove(bak)
                os.replace(REPORT_PATH, bak)
            except Exception:
                pass
        with open(REPORT_PATH, "a", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ") + str(context) + "\n")
            if extra:
                f.write(str(extra) + "\n")
            if exc is not None:
                f.write("".join(traceback.format_exception(
                    type(exc), exc, exc.__traceback__)))
            f.write("\n")
    except Exception:
        pass


def install_exception_hooks():
    """Глобальные перехватчики необработанных исключений."""
    prev = sys.excepthook

    def hook(exc_type, exc, tb):
        log_report("НЕОБРАБОТАННОЕ ИСКЛЮЧЕНИЕ", exc)
        try:
            prev(exc_type, exc, tb)
        except Exception:
            pass
    sys.excepthook = hook

    try:
        def thook(args):
            log_report("ИСКЛЮЧЕНИЕ В ПОТОКЕ '%s'" %
                       getattr(args.thread, "name", "?"), args.exc_value)
        threading.excepthook = thook
    except Exception:
        pass

# ============================================================ справка

HELP_TEXT = """\
GGUF Launcher v{ver}
====================

НАЗНАЧЕНИЕ
----------
Локальный офлайн-инструмент для запуска GGUF-моделей (больших языковых
моделей) через llama-server с удобным веб-интерфейсом. Только стандартная
библиотека Python — никаких pip-зависимостей и внешних сервисов. Модели
и данные остаются на вашем компьютере.

ЧТО УМЕЕТ
---------
1) Проверяет окружение: версия Python, NVIDIA GPU (nvidia-smi), VRAM, RAM.
2) Устанавливает llama.cpp: скачивает с github.com/ggml-org/llama.cpp
   подходящую сборку — CUDA при наличии GPU, иначе AVX2/CPU.
3) Ищет GGUF-модели: сканирует папку или диск, пропуская системные каталоги.
4) Анализирует модель: читает метаданные GGUF (архитектура, длина контекста,
   тип квантования) без загрузки весов в память.
5) Подбирает параметры: рекомендует контекст и число слоёв -ngl под VRAM.
6) Запускает llama-server и открывает встроенный чат в браузере.
7) Пишет диагностику: журнал llama-server и все ошибки — в reports.txt
   рядом с лаунчером (при разрастании > 2 МБ — ротация в reports.txt.1).

КАК ПОЛЬЗОВАТЬСЯ
----------------
Windows:
    1. Положите bootstrap.bat, launcher.py, gguf_core.py, gguf_ui.py
       в одну папку.
    2. Запустите bootstrap.bat — он при необходимости поставит Python
       и запустит лаунчер.
Linux / macOS:
    python3 launcher.py

Откроется браузер с пошаговым мастером:
    Шаг 1 — окружение (Python, GPU, RAM, установка llama.cpp).
    Шаг 2 — поиск моделей (диск или папка).
    Шаг 3 — выбор найденной GGUF-модели.
    Шаг 4 — параметры запуска и кнопка «Запустить сервер».

КЛЮЧИ КОМАНДНОЙ СТРОКИ
----------------------
    --help, -h     показать эту справку и выйти
    --version      показать версию и выйти
    --no-browser   не открывать браузер автоматически

ЧАСТЫЕ ВОПРОСЫ
--------------
Q: Модель не влезает в VRAM.
A: Уменьшите контекст (-c) или число слоёв -ngl на шаге 4. Можно поставить
   -ngl 0 — тогда модель пойдёт на CPU.

Q: llama-server не найден.
A: Нажмите «Установить llama.cpp автоматически» на шаге 1 или укажите путь
   к папке, где лежит llama-server.

Q: Что-то упало с ошибкой.
A: Откройте reports.txt рядом с launcher.py — там трассировка и контекст.
""".format(ver=VERSION)


def print_help():
    print(HELP_TEXT)

# ============================================================ конфиг

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_report("Не удалось сохранить launcher_config.json", e)
        # ============================================================ окружение

def python_short():
    return ".".join(str(x) for x in sys.version_info[:3])


def gpu_info():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=6)
        if out.returncode != 0 or not out.stdout.strip():
            return None
        line = out.stdout.strip().splitlines()[0]
        parts = [p.strip() for p in line.split(",")]
        return {"name": parts[0],
                "vram_total_mb": int(float(parts[1])),
                "vram_free_mb": int(float(parts[2]))}
    except Exception:
        return None


def ram_available_gb():
    try:
        if os.name == "nt":
            import ctypes

            class MSTAT(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            st = MSTAT()
            st.dwLength = ctypes.sizeof(MSTAT)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
            return st.ullAvailPhys / 2 ** 30
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable"):
                    return int(line.split()[1]) / 2 ** 20
    except Exception:
        pass
    return None


def llama_info():
    cfg = load_config()
    d = cfg.get("llama_dir")
    if d:
        for name in ("llama-server.exe", "llama-server"):
            exe = os.path.join(d, name)
            if os.path.exists(exe):
                return {"found": True, "dir": d, "exe": exe}
    try:
        for name in os.listdir(APP_DIR):
            sub = os.path.join(APP_DIR, name)
            if not os.path.isdir(sub):
                continue
            for exe_name in ("llama-server.exe", "llama-server"):
                exe = os.path.join(sub, exe_name)
                if os.path.exists(exe):
                    save_config({**load_config(), "llama_dir": sub})
                    return {"found": True, "dir": sub, "exe": exe}
    except Exception as e:
        log_report("Ошибка поиска llama-server", e)
    return {"found": False, "dir": None, "exe": None}

# ============================================================ парсер GGUF

GGUF_MAGIC = b"GGUF"

# 0=UINT8 1=INT8 2=UINT16 3=INT16 4=UINT32 5=INT32 6=FLOAT32
# 7=BOOL  8=STRING 9=ARRAY 10=UINT64 11=INT64 12=FLOAT64
SCALAR_TYPES = {
    0: ("B", 1), 1: ("b", 1), 2: ("H", 2), 3: ("h", 2),
    4: ("I", 4), 5: ("i", 4), 6: ("f", 4),
    10: ("Q", 8), 11: ("q", 8), 12: ("d", 8),
}


def _read_str(f):
    (n,) = struct.unpack("<Q", f.read(8))
    if n > 4_000_000:
        raise ValueError("слишком длинная строка в GGUF")
    return f.read(n).decode("utf-8", "replace")


def _read_val(f, t):
    if t == 8:
        return _read_str(f)
    if t == 7:
        return bool(struct.unpack("<B", f.read(1))[0])
    if t in SCALAR_TYPES:
        fmt, size = SCALAR_TYPES[t]
        return struct.unpack("<" + fmt, f.read(size))[0]
    if t == 9:
        (et,) = struct.unpack("<I", f.read(4))
        (cnt,) = struct.unpack("<Q", f.read(8))
        if et == 8:
            for _ in range(cnt):
                (n,) = struct.unpack("<Q", f.read(8))
                f.seek(n, 1)
            return "<string[%d]>" % cnt
        if et == 7:
            f.seek(cnt, 1)
            return "<bool[%d]>" % cnt
        if et in SCALAR_TYPES:
            f.seek(cnt * SCALAR_TYPES[et][1], 1)
            return "<arr[%d]>" % cnt
        raise ValueError("вложенный массив не поддерживается")
    raise ValueError("неизвестный тип значения %d" % t)


def parse_gguf_meta(path):
    meta = {}
    with open(path, "rb") as f:
        if f.read(4) != GGUF_MAGIC:
            raise ValueError("это не GGUF-файл")
        (ver,) = struct.unpack("<I", f.read(4))
        if ver not in (2, 3):
            raise ValueError("неподдерживаемая версия GGUF: %d" % ver)
        struct.unpack("<Q", f.read(8))
        (kv_count,) = struct.unpack("<Q", f.read(8))
        for _ in range(min(kv_count, 20000)):
            key = _read_str(f)
            (t,) = struct.unpack("<I", f.read(4))
            try:
                meta[key] = _read_val(f, t)
            except ValueError:
                break
    return meta


FTYPE_NAMES = {
    0: "F32", 1: "F16", 2: "Q4_0", 3: "Q4_1", 7: "Q8_0", 8: "Q5_0", 9: "Q5_1",
    10: "Q2_K", 11: "Q3_K_S", 12: "Q3_K_M", 13: "Q3_K_L", 14: "Q4_K_S",
    15: "Q4_K_M", 16: "Q5_K_S", 17: "Q5_K_M", 18: "Q6_K", 19: "IQ2_XXS",
    20: "IQ2_XS", 21: "Q2_K_S", 22: "IQ3_XS", 23: "IQ3_XXS", 24: "IQ1_S",
    25: "IQ4_NL", 26: "IQ3_S", 27: "IQ2_S", 28: "IQ4_XS", 29: "IQ1_M",
    30: "BF16",
}


def quant_from_name(path):
    m = re.search(r"(I?Q\d+[_A-Za-z0-9]*)\.gguf",
                  os.path.basename(path), re.IGNORECASE)
    return m.group(1).upper() if m else None


def analyze_model(path):
    size = os.path.getsize(path)
    try:
        meta = parse_gguf_meta(path)
    except Exception as e:
        log_report("Ошибка чтения GGUF: %s" % path, e)
        return {"error": str(e), "path": path}

    arch = meta.get("general.architecture")
    ctx = None
    for k, v in meta.items():
        if k.endswith(".context_length") and isinstance(v, int):
            ctx = v
    ftype = meta.get("general.file_type")
    quant = FTYPE_NAMES.get(ftype) if isinstance(ftype, int) else None
    quant = quant or quant_from_name(path) or "неизвестно"
    gpu = gpu_info()
    return {
        "path": path,
        "size_bytes": size,
        "size_gb": round(size / 2 ** 30, 2),
        "arch": arch or "неизвестно",
        "quant": quant,
        "model_ctx": ctx,
        "gpu": gpu,
        "rec": recommend(size, ctx, gpu),
    }


def recommend(size_bytes, model_ctx, gpu):
    size_gb = size_bytes / 2 ** 30
    if gpu and gpu.get("vram_free_mb"):
        free_gb = gpu["vram_free_mb"] / 1024.0
        if free_gb >= size_gb * 1.15:
            ngl, full = 99, True
        else:
            ngl = int(99 * min(1.0, (free_gb * 0.85) / size_gb)) if size_gb else 0
            ngl, full = max(0, min(99, ngl)), False
    else:
        ngl, full = 0, False
    ctx_limit = 16384 if full else 8192
    if not full:
        ram = ram_available_gb()
        if ram is not None and ram < size_gb * 2.5:
            ctx_limit = 4096
    ctx = max(2048, min(model_ctx or 4096, ctx_limit))
    return {"ngl": ngl, "ctx": ctx, "full_gpu": full}
    # ============================================================ сканирование

SCAN = {"running": False, "done": False, "current": "", "found": [], "stop": False}
SCAN_LOCK = threading.Lock()


def scan_worker(root):
    try:
        stack = [(root, 0)]
        seen = set()
        while stack and not SCAN["stop"]:
            d, depth = stack.pop()
            real = os.path.realpath(d).lower()
            if real in seen:
                continue
            seen.add(real)
            SCAN["current"] = d
            try:
                entries = list(os.scandir(d))
            except (PermissionError, OSError):
                continue
            for e in entries:
                if SCAN["stop"]:
                    return
                try:
                    if e.is_file(follow_symlinks=False) and e.name.lower().endswith(".gguf"):
                        SCAN["found"].append({"path": e.path, "size": e.stat().st_size})
                    elif (e.is_dir(follow_symlinks=False) and depth < MAX_SCAN_DEPTH
                          and e.name.lower() not in SKIP_DIRS
                          and not e.name.startswith("$")):
                        stack.append((e.path, depth + 1))
                except OSError:
                    pass
        SCAN["done"] = True
    except Exception as e:
        log_report("Ошибка сканирования: %s" % root, e)
        SCAN["done"] = True
    finally:
        SCAN["running"] = False


def start_scan(path):
    if not os.path.isdir(path):
        return {"error": "папка не найдена: " + path}
    with SCAN_LOCK:
        if SCAN["running"]:
            return {"error": "сканирование уже идёт"}
        SCAN.update(running=True, done=False, current=path, found=[], stop=False)
    threading.Thread(target=scan_worker, args=(path,), daemon=True).start()
    return {"started": True}


def list_disks():
    res = []
    if os.name == "nt":
        for L in string.ascii_uppercase:
            d = L + ":\\"
            if os.path.exists(d):
                try:
                    res.append({"path": d,
                                "free_gb": round(shutil.disk_usage(d).free / 2 ** 30, 1)})
                except OSError:
                    res.append({"path": d, "free_gb": None})
    else:
        res.append({"path": "/", "free_gb": None})
    return res


def known_model_dirs():
    home = os.path.expanduser("~")
    cands = [
        os.path.join(home, ".lmstudio", "models"),
        os.path.join(home, "AppData", "Local", "LM Studio", "models"),
        os.path.join(home, "models"),
        os.path.join(APP_DIR, "models"),
    ]
    return [c for c in cands if os.path.isdir(c)]

# ============================================================ установка llama.cpp

INSTALL = {"active": False, "stage": "", "pct": 0, "message": "", "error": None}


def _pick_asset(assets, want_cuda):
    cuda, cpu = None, None
    for a in assets:
        n = a.get("name", "").lower()
        if not (n.endswith(".zip") and "win" in n and "-bin-" in n):
            continue
        if "arm" in n or "aarch64" in n:
            continue
        if "cuda" in n:
            cuda = cuda or a
            continue
        if "avx2" in n or "avx" in n or "cpu" in n:
            score = 2 if "avx2" in n else 1
            if cpu is None or score > cpu[0]:
                cpu = (score, a)
    if want_cuda and cuda:
        return cuda
    if cpu:
        return cpu[1]
    return None


def install_llama():
    INSTALL.update(active=True, stage="query", pct=0,
                   message="Получаю список релизов с GitHub…", error=None)
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest",
            headers={"User-Agent": "gguf-launcher"})
        data = json.loads(urllib.request.urlopen(req, timeout=30).read())
        gpu = gpu_info()
        target = _pick_asset(data.get("assets", []), want_cuda=(gpu is not None))
        if not target:
            raise RuntimeError("не найден подходящий архив в последнем релизе")
        url = target["browser_download_url"]
        name = target["name"]
        INSTALL.update(stage="download", message="Скачиваю " + name, pct=1)
        tmp = os.path.join(APP_DIR, "llama_download.zip")
        dl_req = urllib.request.Request(url, headers={"User-Agent": "gguf-launcher"})
        with urllib.request.urlopen(dl_req, timeout=60) as r, open(tmp, "wb") as out:
            total = int(r.headers.get("Content-Length") or 0)
            got = 0
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                got += len(chunk)
                if total:
                    INSTALL["pct"] = min(99, int(got * 100 / total))
                INSTALL["message"] = "Скачиваю %s: %d%%" % (name, INSTALL["pct"])
        INSTALL.update(stage="extract", pct=99, message="Распаковываю архив…")
        dest = os.path.join(APP_DIR, "llama.cpp")
        with zipfile.ZipFile(tmp) as z:
            z.extractall(dest)
        try:
            os.remove(tmp)
        except OSError:
            pass
        exe = None
        for dirpath, _dirs, files in os.walk(dest):
            if "llama-server.exe" in files or "llama-server" in files:
                exe = dirpath
                break
        if not exe:
            raise RuntimeError("в архиве не найден llama-server")
        save_config({**load_config(), "llama_dir": exe})
        INSTALL.update(stage="done", pct=100,
                       message="Готово! llama.cpp установлен в " + exe, error=None)
        log_report("llama.cpp успешно установлен", extra="dir=" + exe)
    except Exception as e:
        log_report("Ошибка установки llama.cpp", e)
        INSTALL.update(stage="error", error=str(e),
                       message="Ошибка установки: " + str(e))
    finally:
        INSTALL["active"] = False

# ============================================================ менеджер сервера

class ServerManager:
    def __init__(self):
        self.proc = None
        self.log = deque(maxlen=600)
        self.lock = threading.Lock()
        self.url = None

    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def start(self, exe, args):
        with self.lock:
            if self.running():
                return {"error": "сервер уже запущен"}
            self.log.clear()
            try:
                self.proc = subprocess.Popen(
                    [exe] + args, cwd=os.path.dirname(exe),
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", bufsize=1)
            except OSError as e:
                log_report("Не удалось запустить llama-server", e,
                           extra="exe=%s args=%r" % (exe, args))
                self.proc = None
                return {"error": "не удалось запустить: " + str(e)}
            threading.Thread(target=self._pump, daemon=True).start()
            if "--port" in args:
                pidx = args.index("--port")
                self.url = "http://127.0.0.1:" + args[pidx + 1]
            else:
                self.url = None
            return {"ok": True, "url": self.url}

    def _pump(self):
        p = self.proc
        try:
            for line in p.stdout:
                self.log.append(line.rstrip())
        except Exception as e:
            log_report("Ошибка чтения лога llama-server", e)
        try:
            code = p.poll()
            self.log.append("[процесс завершился, код %s]" % code)
            if code not in (0, None):
                log_report("llama-server завершился с кодом %s" % code,
                           extra="\n".join(list(self.log)[-60:]))
        except Exception:
            pass
        finally:
            # чистим состояние, чтобы UI не показывал "running"
            try:
                with self.lock:
                    if self.proc is p:
                        self.proc = None
                        self.url = None
            except Exception:
                pass

    def stop(self):
        with self.lock:
            if self.proc and self.running():
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=5)
                except Exception:
                    try:
                        self.proc.kill()
                    except Exception:
                        pass
            self.proc = None
            self.url = None


SERVER_MGR = ServerManager()


def free_port(start=8080):
    for p in range(start, start + 60):
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", p))
            s.close()
            return p
        except OSError:
            try:
                s.close()
            except Exception:
                pass
    return start


def tail_reports(limit=200):
    try:
        with open(REPORT_PATH, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()[-limit:]
    except FileNotFoundError:
        return []
    except Exception as e:
        log_report("Ошибка чтения reports.txt", e)
        return []