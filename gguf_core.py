#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Core services for GGUF Launcher."""

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
import urllib.parse
import urllib.request
import zipfile
from collections import deque

VERSION = "1.4"

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "launcher_config.json")
REPORT_PATH = os.path.join(APP_DIR, "reports.txt")

MAX_SCAN_DEPTH = 8
REPORT_MAX_BYTES = 2 * 1024 * 1024
MAX_GGUF_KV = 20000
MAX_GGUF_ARRAY_ITEMS = 1_000_000

SKIP_DIRS = {
    "$recycle.bin",
    "windows",
    "program files",
    "program files (x86)",
    "programdata",
    "appdata",
    "system volume information",
    "node_modules",
    ".git",
    "site-packages",
    "perflogs",
    "recovery",
    "$winreagent",
    "anaconda3",
    "miniconda3",
    "conda",
    "__pycache__",
    ".venv",
    "venv",
}


# ============================================================
# Error reporting
# ============================================================

def log_report(context, exc=None, extra=""):
    """Append diagnostic information without raising another exception."""
    try:
        if (
            os.path.exists(REPORT_PATH)
            and os.path.getsize(REPORT_PATH) > REPORT_MAX_BYTES
        ):
            backup = REPORT_PATH + ".1"
            try:
                if os.path.exists(backup):
                    os.remove(backup)
                os.replace(REPORT_PATH, backup)
            except OSError:
                pass

        with open(REPORT_PATH, "a", encoding="utf-8") as stream:
            stream.write("=" * 70 + "\n")
            stream.write(
                time.strftime("[%Y-%m-%d %H:%M:%S] ") + str(context) + "\n"
            )

            if extra:
                stream.write(str(extra) + "\n")

            if exc is not None:
                stream.write(
                    "".join(
                        traceback.format_exception(
                            type(exc), exc, exc.__traceback__
                        )
                    )
                )

            stream.write("\n")
    except Exception:
        pass


def install_exception_hooks():
    """Install process and thread exception handlers."""
    previous_hook = sys.excepthook

    def hook(exc_type, exc, tb):
        log_report("UNHANDLED EXCEPTION", exc)
        try:
            previous_hook(exc_type, exc, tb)
        except Exception:
            pass

    sys.excepthook = hook

    try:
        def thread_hook(args):
            log_report(
                "THREAD EXCEPTION: %s"
                % getattr(args.thread, "name", "?"),
                args.exc_value,
            )

        threading.excepthook = thread_hook
    except Exception:
        pass


# ============================================================
# Help
# ============================================================

HELP_TEXT = """\
GGUF Launcher v{ver}
====================

PURPOSE
-------
Local offline launcher for GGUF models through llama-server.
The application uses only the Python standard library and does not require
pip packages or external runtime services. Models and chat data stay on
your computer.

FEATURES
--------
1. Checks Python, RAM, NVIDIA GPU and available VRAM.
2. Installs a compatible llama.cpp Windows build automatically.
3. Searches folders or disks for .gguf model files.
4. Reads GGUF metadata without loading model weights.
5. Recommends context size and GPU layer count.
6. Starts llama-server and opens its web interface.
7. Stores diagnostics in reports.txt and rotates the file after 2 MB.
8. Stops active scans and llama-server safely.

USAGE
-----
Windows:
    Put bootstrap.bat, launcher.py, gguf_core.py and gguf_ui.py
    in the same folder, then run bootstrap.bat.

Linux / macOS:
    python3 launcher.py

Command-line options:
    --help, -h     show this help and exit
    --version      show the application version and exit
    --no-browser   do not open the browser automatically

WORKFLOW
--------
1. Check the environment and llama.cpp installation.
2. Select a folder or disk for scanning.
3. Select a GGUF model.
4. Adjust context and GPU layers, then start the server.

TROUBLESHOOTING
---------------
If the model does not fit into VRAM, reduce the context or -ngl value.
Use -ngl 0 for CPU-only inference.

If llama-server is not found, install llama.cpp from step 1 or configure
the folder that contains llama-server.exe.

For errors, open reports.txt beside launcher.py.
""".format(ver=VERSION)


def print_help():
    print(HELP_TEXT)


# ============================================================
# Configuration
# ============================================================

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as stream:
            data = json.load(stream)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def save_config(config):
    try:
        temp_path = CONFIG_PATH + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as stream:
            json.dump(config, stream, ensure_ascii=False, indent=2)
        os.replace(temp_path, CONFIG_PATH)
        return True
    except Exception as exc:
        log_report("Could not save launcher_config.json", exc)
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass
        return False


# ============================================================
# Environment
# ============================================================

def python_short():
    return ".".join(str(value) for value in sys.version_info[:3])


def gpu_info():
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.free",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=6,
            check=False,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return None

        line = result.stdout.strip().splitlines()[0]
        parts = [part.strip() for part in line.split(",")]

        if len(parts) < 3:
            return None

        return {
            "name": parts[0],
            "vram_total_mb": int(float(parts[1])),
            "vram_free_mb": int(float(parts[2])),
        }
    except Exception:
        return None


def ram_available_gb():
    try:
        if os.name == "nt":
            import ctypes

            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MemoryStatus()
            status.dwLength = ctypes.sizeof(MemoryStatus)

            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(
                ctypes.byref(status)
            ):
                return None

            return status.ullAvailPhys / 2**30

        with open("/proc/meminfo", "r", encoding="utf-8") as stream:
            for line in stream:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) / 2**20
    except Exception:
        return None

    return None


def _valid_llama_executable(path):
    return (
        bool(path)
        and os.path.isfile(path)
        and os.access(path, os.X_OK)
        and os.path.basename(path).lower()
        in {"llama-server", "llama-server.exe"}
    )


def llama_info():
    config = load_config()
    configured_dir = config.get("llama_dir")

    candidates = []

    if configured_dir:
        candidates.append(configured_dir)

    try:
        for name in os.listdir(APP_DIR):
            path = os.path.join(APP_DIR, name)
            if os.path.isdir(path):
                candidates.append(path)
    except OSError as exc:
        log_report("Error searching llama-server", exc)

    checked = set()

    for directory in candidates:
        directory = os.path.abspath(os.path.expanduser(str(directory)))

        if directory.lower() in checked:
            continue

        checked.add(directory)

        for executable_name in ("llama-server.exe", "llama-server"):
            executable = os.path.join(directory, executable_name)

            if _valid_llama_executable(executable):
                if config.get("llama_dir") != directory:
                    save_config({**config, "llama_dir": directory})

                return {
                    "found": True,
                    "dir": directory,
                    "exe": executable,
                }

    return {"found": False, "dir": None, "exe": None}


# ============================================================
# GGUF parser
# ============================================================

GGUF_MAGIC = b"GGUF"

SCALAR_TYPES = {
    0: ("B", 1),
    1: ("b", 1),
    2: ("H", 2),
    3: ("h", 2),
    4: ("I", 4),
    5: ("i", 4),
    6: ("f", 4),
    10: ("Q", 8),
    11: ("q", 8),
    12: ("d", 8),
}


def _read_exact(stream, size):
    data = stream.read(size)
    if len(data) != size:
        raise ValueError("unexpected end of GGUF file")
    return data


def _read_str(stream):
    length = struct.unpack("<Q", _read_exact(stream, 8))[0]

    if length > 4_000_000:
        raise ValueError("GGUF string is too long")

    return _read_exact(stream, length).decode("utf-8", "replace")


def _read_val(stream, value_type):
    if value_type == 8:
        return _read_str(stream)

    if value_type == 7:
        return bool(struct.unpack("<B", _read_exact(stream, 1))[0])

    if value_type in SCALAR_TYPES:
        fmt, size = SCALAR_TYPES[value_type]
        return struct.unpack("<" + fmt, _read_exact(stream, size))[0]

    if value_type == 9:
        element_type = struct.unpack("<I", _read_exact(stream, 4))[0]
        count = struct.unpack("<Q", _read_exact(stream, 8))[0]

        if count > MAX_GGUF_ARRAY_ITEMS:
            raise ValueError("GGUF array is too large")

        if element_type == 8:
            for _ in range(count):
                length = struct.unpack("<Q", _read_exact(stream, 8))[0]
                if length > 4_000_000:
                    raise ValueError("GGUF array string is too long")
                stream.seek(length, 1)
            return "<string[%d]>" % count

        if element_type == 7:
            stream.seek(count, 1)
            return "<bool[%d]>" % count

        if element_type in SCALAR_TYPES:
            stream.seek(count * SCALAR_TYPES[element_type][1], 1)
            return "<arr[%d]>" % count

        raise ValueError("nested GGUF array is not supported")

    raise ValueError("unknown GGUF value type %d" % value_type)


def parse_gguf_meta(path):
    metadata = {}

    with open(path, "rb") as stream:
        if _read_exact(stream, 4) != GGUF_MAGIC:
            raise ValueError("not a GGUF file")

        version = struct.unpack("<I", _read_exact(stream, 4))[0]

        if version not in (2, 3):
            raise ValueError("unsupported GGUF version: %d" % version)

        _read_exact(stream, 8)
        kv_count = struct.unpack("<Q", _read_exact(stream, 8))[0]

        if kv_count > MAX_GGUF_KV:
            raise ValueError("too many GGUF metadata entries")

        for _ in range(kv_count):
            key = _read_str(stream)
            value_type = struct.unpack("<I", _read_exact(stream, 4))[0]
            metadata[key] = _read_val(stream, value_type)

    return metadata


FTYPE_NAMES = {
    0: "F32",
    1: "F16",
    2: "Q4_0",
    3: "Q4_1",
    7: "Q8_0",
    8: "Q5_0",
    9: "Q5_1",
    10: "Q2_K",
    11: "Q3_K_S",
    12: "Q3_K_M",
    13: "Q3_K_L",
    14: "Q4_K_S",
    15: "Q4_K_M",
    16: "Q5_K_S",
    17: "Q5_K_M",
    18: "Q6_K",
    19: "IQ2_XXS",
    20: "IQ2_XS",
    21: "Q2_K_S",
    22: "IQ3_XS",
    23: "IQ3_XXS",
    24: "IQ1_S",
    25: "IQ4_NL",
    26: "IQ3_S",
    27: "IQ2_S",
    28: "IQ4_XS",
    29: "IQ1_M",
    30: "BF16",
}


def quant_from_name(path):
    match = re.search(
        r"(I?Q\d+[_A-Za-z0-9]*)\.gguf",
        os.path.basename(path),
        re.IGNORECASE,
    )
    return match.group(1).upper() if match else None


def analyze_model(path):
    try:
        size = os.path.getsize(path)
        metadata = parse_gguf_meta(path)
    except Exception as exc:
        log_report("GGUF read error: %s" % path, exc)
        return {"error": str(exc), "path": path}

    architecture = metadata.get("general.architecture")
    context_length = None

    for key, value in metadata.items():
        if key.endswith(".context_length") and isinstance(value, int):
            context_length = value
            break

    file_type = metadata.get("general.file_type")
    quantization = (
        FTYPE_NAMES.get(file_type)
        if isinstance(file_type, int)
        else None
    )
    quantization = quantization or quant_from_name(path) or "unknown"

    gpu = gpu_info()

    return {
        "path": path,
        "size_bytes": size,
        "size_gb": round(size / 2**30, 2),
        "arch": architecture or "unknown",
        "quant": quantization,
        "model_ctx": context_length,
        "gpu": gpu,
        "rec": recommend(size, context_length, gpu),
    }


def recommend(size_bytes, model_ctx, gpu):
    size_gb = size_bytes / 2**30

    if gpu and gpu.get("vram_free_mb"):
        free_gb = gpu["vram_free_mb"] / 1024.0

        if free_gb >= size_gb * 1.15:
            ngl = 99
            full_gpu = True
        else:
            ratio = (free_gb * 0.85) / size_gb if size_gb else 0
            ngl = int(99 * min(1.0, ratio))
            ngl = max(0, min(99, ngl))
            full_gpu = False
    else:
        ngl = 0
        full_gpu = False

    context_limit = 16384 if full_gpu else 8192

    if not full_gpu:
        ram = ram_available_gb()
        if ram is not None and ram < size_gb * 2.5:
            context_limit = 4096

    context = max(2048, min(model_ctx or 4096, context_limit))

    return {
        "ngl": ngl,
        "ctx": context,
        "full_gpu": full_gpu,
    }


# ============================================================
# Model scanning
# ============================================================

SCAN = {
    "running": False,
    "done": False,
    "current": "",
    "found": [],
    "stop": False,
    "error": None,
}

SCAN_LOCK = threading.RLock()


def _scan_snapshot():
    with SCAN_LOCK:
        return {
            "running": SCAN["running"],
            "done": SCAN["done"],
            "current": SCAN["current"],
            "found": list(SCAN["found"]),
            "stop": SCAN["stop"],
            "error": SCAN["error"],
        }


def scan_worker(root):
    try:
        stack = [(root, 0)]
        seen = set()

        while stack:
            with SCAN_LOCK:
                if SCAN["stop"]:
                    break

            directory, depth = stack.pop()
            real_path = os.path.realpath(directory).lower()

            if real_path in seen:
                continue

            seen.add(real_path)

            with SCAN_LOCK:
                SCAN["current"] = directory

            try:
                entries = list(os.scandir(directory))
            except (PermissionError, OSError):
                continue

            for entry in entries:
                with SCAN_LOCK:
                    if SCAN["stop"]:
                        break

                try:
                    if entry.is_file(follow_symlinks=False):
                        if entry.name.lower().endswith(".gguf"):
                            item = {
                                "path": entry.path,
                                "size": entry.stat().st_size,
                            }
                            with SCAN_LOCK:
                                SCAN["found"].append(item)

                    elif (
                        entry.is_dir(follow_symlinks=False)
                        and depth < MAX_SCAN_DEPTH
                        and entry.name.lower() not in SKIP_DIRS
                        and not entry.name.startswith("$")
                    ):
                        stack.append((entry.path, depth + 1))
                except OSError:
                    pass

    except Exception as exc:
        log_report("Scan error: %s" % root, exc)
        with SCAN_LOCK:
            SCAN["error"] = str(exc)

    finally:
        with SCAN_LOCK:
            SCAN["done"] = True
            SCAN["running"] = False
            SCAN["stop"] = False


def start_scan(path):
    path = os.path.abspath(os.path.expanduser(str(path or "")))

    if not os.path.isdir(path):
        return {"error": "folder not found: " + path}

    with SCAN_LOCK:
        if SCAN["running"]:
            return {"error": "scan is already running"}

        SCAN.update(
            running=True,
            done=False,
            current=path,
            found=[],
            stop=False,
            error=None,
        )

    threading.Thread(
        target=scan_worker,
        args=(path,),
        name="gguf-scan",
        daemon=True,
    ).start()

    return {"started": True}


def stop_scan():
    with SCAN_LOCK:
        if not SCAN["running"]:
            return {"ok": True, "running": False}
        SCAN["stop"] = True

    return {"ok": True, "stopping": True}


def scan_status():
    snapshot = _scan_snapshot()

    return {
        "running": snapshot["running"],
        "done": snapshot["done"],
        "current": snapshot["current"],
        "count": len(snapshot["found"]),
        "error": snapshot["error"],
    }


def scan_results():
    with SCAN_LOCK:
        return list(SCAN["found"])


def list_disks():
    result = []

    if os.name == "nt":
        for letter in string.ascii_uppercase:
            drive = letter + ":\\"

            if os.path.exists(drive):
                try:
                    result.append(
                        {
                            "path": drive,
                            "free_gb": round(
                                shutil.disk_usage(drive).free / 2**30,
                                1,
                            ),
                        }
                    )
                except OSError:
                    result.append({"path": drive, "free_gb": None})
    else:
        result.append({"path": "/", "free_gb": None})

    return result


def known_model_dirs():
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".lmstudio", "models"),
        os.path.join(home, "AppData", "Local", "LM Studio", "models"),
        os.path.join(home, "models"),
        os.path.join(APP_DIR, "models"),
    ]

    return [path for path in candidates if os.path.isdir(path)]


# ============================================================
# llama.cpp installation
# ============================================================

INSTALL = {
    "active": False,
    "stage": "",
    "pct": 0,
    "message": "",
    "error": None,
}

INSTALL_LOCK = threading.RLock()


def _set_install(**values):
    with INSTALL_LOCK:
        INSTALL.update(values)


def install_status():
    with INSTALL_LOCK:
        return {
            key: INSTALL[key]
            for key in ("active", "stage", "pct", "message", "error")
        }


def _pick_asset(assets, want_cuda):
    """Select a compatible Windows llama.cpp archive."""

    cuda_assets = []
    cpu_assets = []

    for asset in assets:
        name = str(asset.get("name") or "")
        lowered = name.lower()

        if not lowered.endswith(".zip"):
            continue

        if "win" not in lowered and "windows" not in lowered:
            continue

        if any(token in lowered for token in ("arm", "aarch64", "arm64")):
            continue

        if "cuda" in lowered:
            cuda_assets.append(asset)
            continue

        if any(
            token in lowered
            for token in (
                "cpu",
                "avx",
                "avx2",
                "vulkan",
                "win-vulkan",
            )
        ):
            cpu_assets.append(asset)

    def asset_score(asset):
        name = str(asset.get("name") or "").lower()
        score = 0

        if "avx2" in name:
            score += 50

        if "cpu" in name:
            score += 20

        if "win" in name or "windows" in name:
            score += 10

        if "x64" in name or "amd64" in name:
            score += 10

        return score

    if want_cuda and cuda_assets:
        return sorted(
            cuda_assets,
            key=asset_score,
            reverse=True,
        )[0]

    if cpu_assets:
        return sorted(
            cpu_assets,
            key=asset_score,
            reverse=True,
        )[0]

    return None


def _safe_extract(zip_file, destination):
    destination = os.path.abspath(destination)

    for member in zip_file.infolist():
        target = os.path.abspath(os.path.join(destination, member.filename))

        if os.path.commonpath((destination, target)) != destination:
            raise RuntimeError("unsafe path in downloaded archive")

    zip_file.extractall(destination)


def _github_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "gguf-launcher/1.4",
            "Accept": "application/vnd.github+json",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def _release_assets_description(data):
    assets = data.get("assets", [])

    if not assets:
        return "no assets"

    names = [
        str(asset.get("name") or "?")
        for asset in assets[:40]
    ]

    return ", ".join(names)


def _find_llama_release():
    """Find a GitHub release containing a Windows binary archive."""

    stable_url = (
        "https://api.github.com/repos/"
        "ggml-org/llama.cpp/releases/latest"
    )

    stable = _github_json(stable_url)

    if _pick_asset(
        stable.get("assets", []),
        want_cuda=gpu_info() is not None,
    ):
        return stable

    stable_tag = stable.get("tag_name")
    nightly_tag = None

    release_body = str(stable.get("body") or "")

    nightly_match = re.search(
        r"releases/tag/([A-Za-z0-9._-]+)",
        release_body,
    )

    if nightly_match:
        nightly_tag = nightly_match.group(1)

    if nightly_tag:
        nightly_url = (
            "https://api.github.com/repos/"
            "ggml-org/llama.cpp/releases/tags/"
            + urllib.parse.quote(nightly_tag, safe="")
        )

        try:
            nightly = _github_json(nightly_url)

            if _pick_asset(
                nightly.get("assets", []),
                want_cuda=gpu_info() is not None,
            ):
                return nightly

        except Exception as exc:
            log_report(
                "Could not query nightly llama.cpp release",
                exc,
                extra="tag=%s" % nightly_tag,
            )

    releases_url = (
        "https://api.github.com/repos/"
        "ggml-org/llama.cpp/releases?per_page=20"
    )

    releases = _github_json(releases_url)

    if isinstance(releases, list):
        for release in releases:
            if _pick_asset(
                release.get("assets", []),
                want_cuda=gpu_info() is not None,
            ):
                return release

    raise RuntimeError(
        "no compatible Windows llama.cpp archive found; "
        "stable=%s; stable_tag=%s"
        % (
            _release_assets_description(stable),
            stable_tag or "unknown",
        )
    )


def install_llama():
    with INSTALL_LOCK:
        if INSTALL["active"]:
            return

        INSTALL.update(
            active=True,
            stage="query",
            pct=0,
            message="Getting llama.cpp release information...",
            error=None,
        )

    temporary_zip = os.path.join(
        APP_DIR,
        "llama_download.zip",
    )

    destination = os.path.join(
        APP_DIR,
        "llama.cpp",
    )

    try:
        release = _find_llama_release()

        release_tag = release.get("tag_name") or "unknown"
        assets = release.get("assets", [])

        target = _pick_asset(
            assets,
            want_cuda=gpu_info() is not None,
        )

        if not target:
            raise RuntimeError(
                "no compatible Windows archive in release %s; assets: %s"
                % (
                    release_tag,
                    _release_assets_description(release),
                )
            )

        url = target.get("browser_download_url")
        name = target.get("name") or "llama.cpp archive"

        if not url:
            raise RuntimeError(
                "selected llama.cpp asset has no download URL"
            )

        log_report(
            "Selected llama.cpp release",
            extra=(
                "release=%s\n"
                "asset=%s\n"
                "url=%s"
                % (
                    release_tag,
                    name,
                    url,
                )
            ),
        )

        _set_install(
            stage="download",
            pct=1,
            message=(
                "Downloading %s from release %s..."
                % (name, release_tag)
            ),
        )

        download_request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "gguf-launcher/1.4",
                "Accept": "application/octet-stream",
            },
        )

        with urllib.request.urlopen(
            download_request,
            timeout=180,
        ) as response:
            total = int(
                response.headers.get("Content-Length") or 0
            )
            downloaded = 0

            with open(temporary_zip, "wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)

                    if not chunk:
                        break

                    output.write(chunk)
                    downloaded += len(chunk)

                    percent = 1

                    if total:
                        percent = min(
                            99,
                            int(downloaded * 100 / total),
                        )

                    _set_install(
                        pct=percent,
                        message=(
                            "Downloading %s: %d%%"
                            % (name, percent)
                        ),
                    )

        if not os.path.isfile(temporary_zip):
            raise RuntimeError(
                "downloaded archive does not exist"
            )

        if os.path.getsize(temporary_zip) < 1024:
            raise RuntimeError(
                "downloaded archive is unexpectedly small"
            )

        _set_install(
            stage="extract",
            pct=99,
            message="Extracting llama.cpp archive...",
        )

        if os.path.isdir(destination):
            shutil.rmtree(destination)

        os.makedirs(destination, exist_ok=True)

        with zipfile.ZipFile(temporary_zip) as archive:
            _safe_extract(archive, destination)

        executable_directory = None
        executable_path = None

        for directory, _dirs, files in os.walk(destination):
            if "llama-server.exe" in files:
                executable_directory = directory
                executable_path = os.path.join(
                    directory,
                    "llama-server.exe",
                )
                break

            if "llama-server" in files:
                executable_directory = directory
                executable_path = os.path.join(
                    directory,
                    "llama-server",
                )
                break

        if not executable_directory or not executable_path:
            raise RuntimeError(
                "llama-server was not found in downloaded archive"
            )

        save_config(
            {
                **load_config(),
                "llama_dir": executable_directory,
            }
        )

        _set_install(
            stage="done",
            pct=100,
            message=(
                "llama.cpp installed in "
                + executable_directory
            ),
            error=None,
        )

        log_report(
            "llama.cpp installed successfully",
            extra=(
                "release=%s\n"
                "asset=%s\n"
                "dir=%s\n"
                "exe=%s"
                % (
                    release_tag,
                    name,
                    executable_directory,
                    executable_path,
                )
            ),
        )

    except Exception as exc:
        log_report(
            "llama.cpp installation error",
            exc,
            extra=(
                "temporary_zip=%s\n"
                "destination=%s"
                % (
                    temporary_zip,
                    destination,
                )
            ),
        )

        _set_install(
            stage="error",
            error=str(exc),
            message="Installation error: " + str(exc),
        )

    finally:
        try:
            if os.path.exists(temporary_zip):
                os.remove(temporary_zip)
        except OSError:
            pass

        _set_install(active=False)


# ============================================================
# Server manager
# ============================================================

class ServerManager:
    def __init__(self):
        self.proc = None
        self.log = deque(maxlen=600)
        self.lock = threading.RLock()
        self.url = None

    def running(self):
        with self.lock:
            return self.proc is not None and self.proc.poll() is None

    def start(self, executable, args):
        with self.lock:
            if self.running():
                return {"error": "server is already running"}

            if not _valid_llama_executable(executable):
                return {"error": "invalid llama-server executable"}

            self.log.clear()

            try:
                self.proc = subprocess.Popen(
                    [executable] + list(args),
                    cwd=os.path.dirname(executable),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                )
            except OSError as exc:
                log_report(
                    "Could not start llama-server",
                    exc,
                    extra="exe=%s args=%r" % (executable, args),
                )
                self.proc = None
                return {"error": "could not start server: " + str(exc)}

            process = self.proc

            threading.Thread(
                target=self._pump,
                args=(process,),
                name="llama-server-log",
                daemon=True,
            ).start()

            port = None
            try:
                port_index = args.index("--port")
                port = int(args[port_index + 1])
            except (ValueError, IndexError, TypeError):
                pass

            self.url = (
                "http://127.0.0.1:%d" % port
                if port is not None
                else None
            )

            return {"ok": True, "url": self.url}

    def _pump(self, process):
        try:
            if process.stdout is not None:
                for line in process.stdout:
                    self.log.append(line.rstrip())
        except Exception as exc:
            log_report("Error reading llama-server log", exc)

        try:
            code = process.wait(timeout=2)
            self.log.append("[process exited with code %s]" % code)

            if code != 0:
                log_report(
                    "llama-server exited with code %s" % code,
                    extra="\n".join(list(self.log)[-60:]),
                )
        except Exception:
            pass
        finally:
            with self.lock:
                if self.proc is process:
                    self.proc = None
                    self.url = None

    def stop(self):
        with self.lock:
            process = self.proc

            if process is None:
                self.url = None
                return

            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            except Exception:
                try:
                    if process.poll() is None:
                        process.kill()
                        process.wait(timeout=3)
                except Exception as exc:
                    log_report("Could not stop llama-server", exc)
            finally:
                if self.proc is process:
                    self.proc = None
                self.url = None


SERVER_MGR = ServerManager()


def free_port(start=8080):
    for port in range(start, start + 60):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", port))
            return port
        except OSError:
            pass
        finally:
            sock.close()

    return start


def tail_reports(limit=200):
    try:
        with open(
            REPORT_PATH,
            "r",
            encoding="utf-8",
            errors="replace",
        ) as stream:
            return stream.readlines()[-limit:]
    except FileNotFoundError:
        return []
    except Exception as exc:
        log_report("Could not read reports.txt", exc)
        return []