#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML/CSS/JavaScript web interface for GGUF Launcher v1.3."""

HTML = r'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GGUF Launcher v1.3</title>

<style>
:root{
  --bg:#0a0e1a;
  --bg2:#0d1222;
  --card:#131a2e;
  --card2:#182136;
  --border:rgba(255,255,255,.07);
  --border2:rgba(255,255,255,.12);
  --txt:#e8ecf6;
  --dim:#8b95ad;
  --dim2:#5b6683;
  --acc:#6366f1;
  --acc2:#8b5cf6;
  --accGlow:rgba(99,102,241,.35);
  --ok:#10b981;
  --warn:#f59e0b;
  --err:#ef4444;
  --r:14px;
  --r2:10px;
}

*{
  box-sizing:border-box;
}

html,
body{
  margin:0;
  padding:0;
}

body{
  font-family:
    "Segoe UI",
    "Noto Sans",
    system-ui,
    -apple-system,
    sans-serif;
  background:
    radial-gradient(
      1200px 600px at 90% -10%,
      rgba(99,102,241,.12),
      transparent 60%
    ),
    radial-gradient(
      900px 500px at -10% 20%,
      rgba(139,92,246,.10),
      transparent 55%
    ),
    var(--bg);
  color:var(--txt);
  min-height:100vh;
  -webkit-font-smoothing:antialiased;
}

a{
  color:var(--acc2);
}

.app{
  max-width:940px;
  margin:0 auto;
  padding:26px 18px 80px;
}

/* ---------- header ---------- */

.head{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:16px;
  margin-bottom:22px;
}

.brand{
  display:flex;
  align-items:center;
  gap:14px;
}

.brand-logo{
  width:46px;
  height:46px;
  border-radius:12px;
  background:linear-gradient(135deg,var(--acc),var(--acc2));
  display:flex;
  align-items:center;
  justify-content:center;
  box-shadow:0 8px 24px -6px var(--accGlow);
}

.brand-logo svg{
  width:26px;
  height:26px;
  color:#fff;
}

.brand h1{
  font-size:22px;
  margin:0;
  font-weight:700;
  letter-spacing:-.3px;
}

.brand p{
  margin:2px 0 0;
  font-size:13px;
  color:var(--dim);
}

.head-right{
  display:flex;
  gap:8px;
  align-items:center;
}

/* ---------- steps ---------- */

.steps{
  display:flex;
  gap:6px;
  margin-bottom:22px;
  flex-wrap:wrap;
}

.step{
  display:flex;
  align-items:center;
  gap:8px;
  padding:8px 14px;
  border-radius:99px;
  background:rgba(255,255,255,.03);
  border:1px solid var(--border);
  color:var(--dim);
  font-size:13px;
  font-weight:500;
  transition:all .2s;
}

.step span{
  width:22px;
  height:22px;
  border-radius:50%;
  background:rgba(255,255,255,.06);
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:11px;
  font-weight:700;
}

.step.active{
  color:var(--txt);
  border-color:var(--acc);
  background:rgba(99,102,241,.10);
  box-shadow:0 0 0 3px rgba(99,102,241,.08);
}

.step.active span{
  background:var(--acc);
  color:#fff;
}

.step.done{
  color:var(--ok);
  border-color:rgba(16,185,129,.35);
}

.step.done span{
  background:var(--ok);
  color:#fff;
}

/* ---------- cards ---------- */

.card{
  background:linear-gradient(180deg,var(--card),var(--card2));
  border:1px solid var(--border);
  border-radius:var(--r);
  padding:22px;
  margin-bottom:16px;
  box-shadow:0 4px 22px -12px rgba(0,0,0,.6);
  transition:border-color .2s;
}

.card:hover{
  border-color:var(--border2);
}

.card-head{
  display:flex;
  align-items:center;
  justify-content:space-between;
  margin-bottom:14px;
  gap:10px;
  flex-wrap:wrap;
}

.card-title{
  display:flex;
  align-items:center;
  gap:10px;
}

.kicker{
  font-size:11px;
  font-weight:700;
  letter-spacing:1.2px;
  text-transform:uppercase;
  color:var(--acc2);
}

.card h2{
  margin:2px 0 0;
  font-size:17px;
  font-weight:600;
  letter-spacing:-.2px;
}

/* ---------- chips ---------- */

.chips{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin:4px 0;
}

.chip{
  display:inline-flex;
  align-items:center;
  gap:6px;
  padding:6px 12px;
  border-radius:99px;
  background:rgba(255,255,255,.04);
  border:1px solid var(--border);
  font-size:13px;
  color:var(--txt);
  white-space:nowrap;
}

.chip.ok{
  background:rgba(16,185,129,.10);
  border-color:rgba(16,185,129,.3);
  color:#7ee2bd;
}

.chip.warn{
  background:rgba(245,158,11,.10);
  border-color:rgba(245,158,11,.3);
  color:#fcd77e;
}

.chip.err{
  background:rgba(239,68,68,.10);
  border-color:rgba(239,68,68,.3);
  color:#fca5a5;
}

.chip .dot{
  width:6px;
  height:6px;
  border-radius:50%;
  background:currentColor;
  opacity:.85;
}

.chip svg{
  width:13px;
  height:13px;
}

/* ---------- buttons ---------- */

button,
.btn{
  font:inherit;
  font-size:14px;
  font-weight:500;
  border:0;
  border-radius:var(--r2);
  padding:10px 16px;
  cursor:pointer;
  transition:all .15s;
  display:inline-flex;
  align-items:center;
  gap:8px;
  text-decoration:none;
}

button svg,
.btn svg{
  width:15px;
  height:15px;
}

button.primary,
.btn.primary{
  background:linear-gradient(135deg,var(--acc),var(--acc2));
  color:#fff;
  box-shadow:0 6px 20px -8px var(--accGlow);
}

button.primary:hover,
.btn.primary:hover{
  transform:translateY(-1px);
  box-shadow:0 10px 26px -8px var(--accGlow);
}

button.ghost,
.btn.ghost{
  background:rgba(255,255,255,.04);
  border:1px solid var(--border2);
  color:var(--txt);
}

button.ghost:hover,
.btn.ghost:hover{
  background:rgba(255,255,255,.08);
  border-color:rgba(255,255,255,.2);
}

button.ok,
.btn.ok{
  background:linear-gradient(135deg,var(--ok),#059669);
  color:#fff;
  box-shadow:0 6px 20px -8px rgba(16,185,129,.5);
}

button:disabled{
  opacity:.5;
  cursor:not-allowed;
  transform:none !important;
}

button.icon{
  padding:8px;
  background:rgba(255,255,255,.04);
  border:1px solid var(--border2);
  color:var(--txt);
  border-radius:var(--r2);
}

/* ---------- inputs ---------- */

input[type=text],
input[type=number]{
  font:inherit;
  font-size:14px;
  background:rgba(0,0,0,.25);
  border:1px solid var(--border2);
  border-radius:var(--r2);
  color:var(--txt);
  padding:10px 12px;
  outline:none;
  transition:border-color .15s,box-shadow .15s;
}

input[type=text]:focus,
input[type=number]:focus{
  border-color:var(--acc);
  box-shadow:0 0 0 3px rgba(99,102,241,.18);
}

input[type=text]{
  width:100%;
}

.field{
  display:flex;
  flex-direction:column;
  gap:5px;
}

.field label{
  font-size:12px;
  color:var(--dim);
  font-weight:500;
  padding-left:2px;
}

.row{
  display:flex;
  gap:10px;
  align-items:center;
  flex-wrap:wrap;
  margin:8px 0;
}

.row.between{
  justify-content:space-between;
}

/* ---------- models ---------- */

.models{
  display:flex;
  flex-direction:column;
  gap:8px;
  max-height:420px;
  overflow-y:auto;
  padding-right:4px;
}

.models::-webkit-scrollbar{
  width:8px;
}

.models::-webkit-scrollbar-thumb{
  background:rgba(255,255,255,.1);
  border-radius:4px;
}

.model{
  display:flex;
  gap:14px;
  align-items:center;
  padding:14px 16px;
  border-radius:12px;
  background:rgba(255,255,255,.02);
  border:1px solid var(--border);
  cursor:pointer;
  transition:all .15s;
}

.model:hover{
  border-color:var(--border2);
  background:rgba(255,255,255,.04);
}

.model.sel{
  border-color:var(--acc);
  background:
    linear-gradient(
      135deg,
      rgba(99,102,241,.10),
      rgba(139,92,246,.05)
    );
  box-shadow:0 0 0 3px rgba(99,102,241,.08);
}

.model-icon{
  flex:0 0 40px;
  width:40px;
  height:40px;
  border-radius:10px;
  background:rgba(99,102,241,.12);
  display:flex;
  align-items:center;
  justify-content:center;
  color:var(--acc2);
}

.model-icon svg{
  width:20px;
  height:20px;
}

.model-body{
  flex:1;
  min-width:0;
}

.model-name{
  font-weight:600;
  font-size:14px;
  margin-bottom:4px;
  word-break:break-word;
}

.model-path{
  color:var(--dim2);
  font-size:11.5px;
  word-break:break-all;
  font-family:ui-monospace,Consolas,monospace;
}

.model-side{
  color:var(--dim);
  font-size:12.5px;
  font-weight:600;
  white-space:nowrap;
}

.meta-row{
  display:flex;
  gap:6px;
  flex-wrap:wrap;
  margin-top:6px;
}

.meta{
  font-size:11px;
  padding:2px 8px;
  border-radius:6px;
  background:rgba(255,255,255,.05);
  color:var(--dim);
}

.meta.acc{
  background:rgba(99,102,241,.15);
  color:#c7c9ff;
}

/* ---------- progress ---------- */

.bar{
  height:8px;
  background:rgba(255,255,255,.06);
  border-radius:6px;
  overflow:hidden;
  margin:10px 0;
}

.bar > div{
  height:100%;
  width:0%;
  background:linear-gradient(90deg,var(--acc),var(--acc2));
  border-radius:6px;
  transition:width .3s;
  position:relative;
}

.bar > div::after{
  content:"";
  position:absolute;
  inset:0;
  background:
    linear-gradient(
      90deg,
      transparent,
      rgba(255,255,255,.4),
      transparent
    );
  animation:shim 1.4s linear infinite;
}

.bar.idle > div::after{
  display:none;
}

@keyframes shim{
  0%{
    transform:translateX(-100%);
  }

  100%{
    transform:translateX(100%);
  }
}

/* ---------- log ---------- */

.mono{
  font-family:ui-monospace,Consolas,"Courier New",monospace;
  font-size:12px;
  line-height:1.55;
  background:rgba(0,0,0,.35);
  border:1px solid var(--border);
  border-radius:var(--r2);
  padding:12px 14px;
  max-height:280px;
  overflow:auto;
  white-space:pre-wrap;
  word-break:break-word;
  color:#cbd5e1;
}

.mono::-webkit-scrollbar{
  width:8px;
}

.mono::-webkit-scrollbar-thumb{
  background:rgba(255,255,255,.1);
  border-radius:4px;
}

/* ---------- hints ---------- */

.hint{
  color:var(--dim);
  font-size:13px;
  line-height:1.5;
}

.hint code{
  background:rgba(255,255,255,.06);
  padding:1px 6px;
  border-radius:5px;
  font-family:ui-monospace,monospace;
  font-size:12px;
}

/* ---------- help modal ---------- */

.modal-bg{
  position:fixed;
  inset:0;
  background:rgba(4,7,15,.72);
  backdrop-filter:blur(6px);
  display:none;
  align-items:center;
  justify-content:center;
  padding:24px;
  z-index:100;
}

.modal-bg.on{
  display:flex;
}

.modal{
  background:linear-gradient(180deg,#141a2e,#0f1526);
  border:1px solid var(--border2);
  border-radius:18px;
  max-width:720px;
  width:100%;
  max-height:86vh;
  overflow:auto;
  padding:26px 28px;
  box-shadow:0 30px 80px -20px rgba(0,0,0,.8);
}

.modal::-webkit-scrollbar{
  width:8px;
}

.modal::-webkit-scrollbar-thumb{
  background:rgba(255,255,255,.1);
  border-radius:4px;
}

.modal h2{
  margin:0 0 4px;
  font-size:20px;
}

.modal h3{
  margin:20px 0 6px;
  font-size:14px;
  color:var(--acc2);
  letter-spacing:.3px;
}

.modal p,
.modal li{
  color:#c8d0e0;
  font-size:13.5px;
  line-height:1.6;
}

.modal ul{
  padding-left:22px;
  margin:6px 0;
}

.modal .close{
  position:sticky;
  top:0;
  float:right;
  margin:-6px -6px 0 0;
}

/* ---------- toast ---------- */

#toasts{
  position:fixed;
  right:18px;
  bottom:18px;
  display:flex;
  flex-direction:column;
  gap:8px;
  z-index:200;
  max-width:360px;
}

.toast{
  background:#1b2338;
  border:1px solid var(--border2);
  padding:12px 16px;
  border-radius:12px;
  box-shadow:0 14px 40px -12px rgba(0,0,0,.7);
  font-size:13.5px;
  line-height:1.4;
  animation:slide .25s ease;
  display:flex;
  gap:10px;
  align-items:flex-start;
}

.toast.err{
  border-color:rgba(239,68,68,.5);
  background:#2a1520;
}

.toast.ok{
  border-color:rgba(16,185,129,.45);
  background:#0f2a22;
}

.toast.warn{
  border-color:rgba(245,158,11,.45);
  background:#2a2110;
}

.toast svg{
  flex:0 0 16px;
  width:16px;
  height:16px;
  margin-top:1px;
}

@keyframes slide{
  from{
    opacity:0;
    transform:translateY(10px);
  }

  to{
    opacity:1;
    transform:translateY(0);
  }
}

.skeleton{
  height:56px;
  border-radius:12px;
  background:
    linear-gradient(
      90deg,
      rgba(255,255,255,.03),
      rgba(255,255,255,.07),
      rgba(255,255,255,.03)
    );
  background-size:200% 100%;
  animation:skel 1.4s ease infinite;
}

@keyframes skel{
  0%{
    background-position:200% 0;
  }

  100%{
    background-position:-200% 0;
  }
}

/* ---------- mobile ---------- */

@media (max-width:640px){
  .app{
    padding:18px 12px 60px;
  }

  .head{
    align-items:flex-start;
  }

  .brand h1{
    font-size:19px;
  }

  .brand p{
    font-size:12px;
  }

  .card{
    padding:16px;
  }

  .step{
    flex:1 1 calc(50% - 6px);
    justify-content:center;
    padding:8px 10px;
  }

  .model{
    align-items:flex-start;
  }

  .model-side{
    font-size:11px;
  }

  .modal{
    padding:20px 18px;
  }

  #toasts{
    left:12px;
    right:12px;
    bottom:12px;
    max-width:none;
  }
}
</style>
</head>
<body>

<div class="app">

<!-- ============ HEADER ============ -->

<header class="head">
  <div class="brand">
    <div class="brand-logo">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M12 2 4 7v10l8 5 8-5V7z"/>
        <path d="M12 22V12"/>
        <path d="M4 7l8 5 8-5"/>
      </svg>
    </div>

    <div>
      <h1>GGUF Launcher</h1>
      <p>Локальный запуск моделей через llama-server</p>
    </div>
  </div>

  <div class="head-right">
    <span class="chip" id="verChip">
      <span class="dot"></span>
      v—
    </span>

    <button
      class="icon"
      title="Справка"
      onclick="openHelp()"
      type="button"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <circle cx="12" cy="12" r="10"/>
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    </button>
  </div>
</header>

<!-- ============ STEPS ============ -->

<ol
  class="steps"
  style="list-style:none;padding:0"
>
  <li class="step active" id="step1">
    <span>1</span>
    Окружение
  </li>

  <li class="step" id="step2">
    <span>2</span>
    Поиск
  </li>

  <li class="step" id="step3">
    <span>3</span>
    Модели
  </li>

  <li class="step" id="step4">
    <span>4</span>
    Запуск
  </li>
</ol>

<!-- ============ STEP 1 ============ -->

<section class="card">
  <div class="card-head">
    <div class="card-title">
      <div>
        <div class="kicker">Шаг 1</div>
        <h2>Проверка системы</h2>
      </div>
    </div>
  </div>

  <div id="env">
    <div class="skeleton"></div>
  </div>

  <div
    id="installBox"
    style="display:none;margin-top:12px"
  >
    <div class="bar" id="instBarWrap">
      <div id="instBar"></div>
    </div>

    <div class="hint" id="instMsg"></div>
  </div>
</section>

<!-- ============ STEP 2 ============ -->

<section class="card">
  <div class="card-head">
    <div class="card-title">
      <div>
        <div class="kicker">Шаг 2</div>
        <h2>Где искать GGUF-файлы</h2>
      </div>
    </div>
  </div>

  <div
    class="hint"
    style="margin-bottom:8px"
  >
    Быстрый выбор диска:
  </div>

  <div class="row" id="disks"></div>
  <div id="knownDirs" style="margin:8px 0"></div>

  <div class="row">
    <div
      class="field"
      style="flex:1;min-width:240px"
    >
      <label>Путь к папке или диску</label>
      <input
        type="text"
        id="scanPath"
        placeholder="Например: C:\models или D:\"
      >
    </div>

    <button
      class="primary"
      onclick="startScan()"
      type="button"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      Сканировать
    </button>

    <button
      class="ghost"
      onclick="stopScan()"
      type="button"
    >
      Стоп
    </button>
  </div>

  <div
    class="hint"
    id="scanInfo"
    style="margin-top:8px"
  ></div>
</section>

<!-- ============ STEP 3 ============ -->

<section class="card">
  <div class="card-head">
    <div class="card-title">
      <div>
        <div class="kicker">Шаг 3</div>
        <h2>Найденные модели</h2>
      </div>
    </div>

    <div
      class="chip"
      id="modelsCount"
      style="display:none"
    >
      <span class="dot"></span>
      <span id="modelsCountN">0</span>
    </div>
  </div>

  <div id="models" class="hint">
    Ещё не сканировали.
  </div>
</section>

<!-- ============ STEP 4 ============ -->

<section class="card">
  <div class="card-head">
    <div class="card-title">
      <div>
        <div class="kicker">Шаг 4</div>
        <h2>Параметры и запуск</h2>
      </div>
    </div>
  </div>

  <div id="runInfo" class="hint">
    Сначала выберите модель.
  </div>

  <div
    class="row"
    id="runForm"
    style="display:none;align-items:flex-end"
  >
    <div class="field">
      <label>Контекст (токенов)</label>
      <input
        type="number"
        id="ctx"
        style="width:130px"
        min="512"
        max="1000000"
      >
    </div>

    <div class="field">
      <label>Слоёв на GPU (-ngl)</label>
      <input
        type="number"
        id="ngl"
        style="width:110px"
        min="0"
        max="999"
      >
    </div>

    <div
      class="field"
      style="flex:1;min-width:160px"
    >
      <label>Хост</label>
      <input
        type="text"
        id="host"
        value="127.0.0.1"
      >
    </div>
  </div>

  <div
    class="row"
    id="runBtns"
    style="display:none"
  >
    <button
      class="ok"
      onclick="run()"
      type="button"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <polygon points="5 3 19 12 5 21 5 3"/>
      </svg>
      Запустить сервер
    </button>

    <button
      class="ghost"
      onclick="stopSrv()"
      type="button"
    >
      Остановить
    </button>
  </div>

  <div
    id="runStatus"
    style="margin-top:6px"
  ></div>

  <div
    id="logWrap"
    style="display:none;margin-top:12px"
  >
    <div
      class="card-head"
      style="margin-bottom:8px"
    >
      <div
        class="hint"
        style="font-weight:600"
      >
        Журнал llama-server
      </div>

      <button
        class="icon"
        title="Скопировать"
        onclick="copyLog()"
        type="button"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <rect
            x="9"
            y="9"
            width="13"
            height="13"
            rx="2"
          />
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
        </svg>
      </button>
    </div>

    <div class="mono" id="logBox"></div>
  </div>
</section>

</div>

<!-- ============ HELP MODAL ============ -->

<div
  class="modal-bg"
  id="helpModal"
  onclick="if(event.target===this)closeHelp()"
>
  <div class="modal">
    <button
      class="icon close"
      onclick="closeHelp()"
      type="button"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>

    <h2>
      GGUF Launcher
      <span id="helpVersion"></span>
    </h2>

    <p class="hint">
      Локальный офлайн-инструмент для запуска GGUF-моделей
      через llama-server. Использует только стандартную библиотеку Python.
      Модели и данные не покидают ваш компьютер.
    </p>

    <h3>Что умеет</h3>

    <ul>
      <li>Проверяет Python, NVIDIA GPU, VRAM и доступную RAM.</li>
      <li>
        Автоматически устанавливает llama.cpp:
        CUDA-сборку при наличии NVIDIA GPU,
        иначе CPU-сборку.
      </li>
      <li>
        Сканирует папки и диски в поиске файлов
        <code>.gguf</code>.
      </li>
      <li>
        Читает метаданные GGUF без загрузки весов в память.
      </li>
      <li>
        Рекомендует контекст и количество слоёв
        <code>-ngl</code>.
      </li>
      <li>
        Запускает llama-server и открывает его веб-интерфейс.
      </li>
      <li>
        Записывает ошибки и диагностику в
        <code>reports.txt</code>.
      </li>
    </ul>

    <h3>Как пользоваться</h3>

    <p>
      Windows: положите
      <code>bootstrap.bat</code>,
      <code>launcher.py</code>,
      <code>gguf_core.py</code>
      и
      <code>gguf_ui.py</code>
      в одну папку и запустите
      <code>bootstrap.bat</code>.
    </p>

    <p>
      Linux/macOS:
      <code>python3 launcher.py</code>.
    </p>

    <p>
      Пройдите четыре шага:
      проверка окружения,
      поиск модели,
      выбор модели,
      запуск сервера.
    </p>

    <h3>Ключи командной строки</h3>

    <ul>
      <li><code>--help</code>, <code>-h</code> — справка</li>
      <li><code>--version</code> — версия приложения</li>
      <li>
        <code>--no-browser</code> —
        не открывать браузер автоматически
      </li>
    </ul>

    <h3>Частые вопросы</h3>

    <p>
      <b>Модель не влезает в VRAM.</b>
      Уменьшите контекст или значение
      <code>-ngl</code>.
      Значение <code>-ngl 0</code> включает CPU-режим.
    </p>

    <p>
      <b>llama-server не найден.</b>
      Нажмите кнопку автоматической установки
      или укажите папку с
      <code>llama-server.exe</code>.
    </p>

    <p>
      <b>Что-то завершилось с ошибкой.</b>
      Откройте файл
      <code>reports.txt</code>
      рядом с лаунчером.
    </p>

    <div
      class="row between"
      style="margin-top:16px"
    >
      <div class="hint" id="reportPath"></div>

      <button
        class="ghost"
        onclick="showReport()"
        type="button"
      >
        Показать журнал ошибок
      </button>
    </div>

    <div
      class="mono"
      id="reportBox"
      style="display:none;margin-top:10px"
    ></div>
  </div>
</div>

<div id="toasts"></div>

<script>
const $ = selector => document.querySelector(selector);
const $$ = selector => document.querySelectorAll(selector);

const state = {
  models: [],
  selected: null,
  scanPoll: null,
  logPoll: null,
  installPoll: null,
  lastScanDone: false,
};

/* ---------- utilities ---------- */

async function api(path, body){
  const options = body !== undefined
    ? {
        method:'POST',
        headers:{
          'Content-Type':'application/json'
        },
        body:JSON.stringify(body)
      }
    : undefined;

  const response = await fetch(path, options);

  let data;

  try {
    data = await response.json();
  } catch (_) {
    throw new Error('Сервер вернул некорректный ответ');
  }

  if (!response.ok){
    throw new Error(
      data.error || ('HTTP ошибка ' + response.status)
    );
  }

  return data;
}

function esc(value){
  return String(value == null ? '' : value).replace(
    /[&<>"']/g,
    character => ({
      '&':'&amp;',
      '<':'&lt;',
      '>':'&gt;',
      '"':'&quot;',
      "'":'&#39;'
    }[character])
  );
}

function fmtSize(bytes){
  const value = Number(bytes);

  if (!Number.isFinite(value) || value < 0){
    return '?';
  }

  return (value / 1073741824).toFixed(2) + ' ГБ';
}

const ICONS = {
  check:
    '<svg viewBox="0 0 24 24" fill="none" ' +
    'stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round">' +
    '<polyline points="20 6 9 17 4 12"></polyline>' +
    '</svg>',

  alert:
    '<svg viewBox="0 0 24 24" fill="none" ' +
    'stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round">' +
    '<circle cx="12" cy="12" r="10"></circle>' +
    '<line x1="12" y1="8" x2="12" y2="12"></line>' +
    '<line x1="12" y1="16" x2="12.01" y2="16"></line>' +
    '</svg>',

  info:
    '<svg viewBox="0 0 24 24" fill="none" ' +
    'stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round">' +
    '<circle cx="12" cy="12" r="10"></circle>' +
    '<line x1="12" y1="16" x2="12" y2="12"></line>' +
    '<line x1="12" y1="8" x2="12.01" y2="8"></line>' +
    '</svg>',

  cube:
    '<svg viewBox="0 0 24 24" fill="none" ' +
    'stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round">' +
    '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>' +
    '<polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>' +
    '<line x1="12" y1="22.08" x2="12" y2="12"></line>' +
    '</svg>',

  chip:
    '<svg viewBox="0 0 24 24" fill="none" ' +
    'stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round">' +
    '<rect x="4" y="4" width="16" height="16" rx="2"></rect>' +
    '<rect x="9" y="9" width="6" height="6"></rect>' +
    '<line x1="9" y1="1" x2="9" y2="4"></line>' +
    '<line x1="15" y1="1" x2="15" y2="4"></line>' +
    '<line x1="9" y1="20" x2="9" y2="23"></line>' +
    '<line x1="15" y1="20" x2="15" y2="23"></line>' +
    '<line x1="20" y1="9" x2="23" y2="9"></line>' +
    '<line x1="20" y1="14" x2="23" y2="14"></line>' +
    '<line x1="1" y1="9" x2="4" y2="9"></line>' +
    '<line x1="1" y1="14" x2="4" y2="14"></line>' +
    '</svg>'
};

/* ---------- toast ---------- */

function toast(message, kind){
  const type = kind || 'info';
  const element = document.createElement('div');

  element.className = 'toast ' + type;

  const icon = type === 'err'
    ? ICONS.alert
    : type === 'ok'
      ? ICONS.check
      : type === 'warn'
        ? ICONS.alert
        : ICONS.info;

  element.innerHTML =
    icon +
    '<div>' +
    esc(message) +
    '</div>';

  $('#toasts').appendChild(element);

  setTimeout(() => {
    element.style.opacity = '0';
    element.style.transform = 'translateY(8px)';
    element.style.transition = 'all .3s';
  }, 4200);

  setTimeout(() => {
    element.remove();
  }, 4700);
}

/* ---------- steps ---------- */

function setStep(number, done){
  const element = document.getElementById('step' + number);

  if (!element){
    return;
  }

  if (done){
    element.classList.add('done');
    element.classList.remove('active');
  } else {
    element.classList.add('active');
    element.classList.remove('done');
  }

  for (let index = 1; index <= 4; index++){
    if (index > number){
      document
        .getElementById('step' + index)
        .classList.remove('active','done');
    }
  }
}

function markDone(number){
  const element = document.getElementById('step' + number);

  if (!element){
    return;
  }

  element.classList.add('done');
  element.classList.remove('active');
}

/* ---------- help modal ---------- */

function openHelp(){
  $('#helpModal').classList.add('on');
}

function closeHelp(){
  $('#helpModal').classList.remove('on');
}

async function showReport(){
  const box = $('#reportBox');

  if (box.style.display !== 'none'){
    box.style.display = 'none';
    return;
  }

  try {
    const result = await api('/api/reports/tail');

    box.textContent =
      result.lines && result.lines.length
        ? result.lines.join('')
        : '(журнал пуст)';

    box.style.display = 'block';
  } catch (error){
    toast(error.message, 'err');
  }
}
/* ---------- status ---------- */

async function loadStatus(){
  let status;

  try {
    status = await api('/api/status');
  } catch (error){
    toast('Не удалось получить статус: ' + error.message, 'err');
    return null;
  }

  $('#verChip').innerHTML =
    '<span class="dot"></span>v' + esc(status.version);

  $('#helpVersion').textContent = 'v' + esc(status.version);

  if (status.report_path){
    $('#reportPath').textContent =
      'Журнал: ' + status.report_path;
  }

  const chips = [];

  chips.push(
    chip(
      'Python ' + status.python_short,
      'ok',
      ICONS.check
    )
  );

  if (status.gpu){
    chips.push(
      chip(
        'GPU: ' + status.gpu.name,
        'ok',
        ICONS.chip
      )
    );

    chips.push(
      chip(
        'VRAM свободно: ' +
        Math.round(status.gpu.vram_free_mb / 1024) +
        ' ГБ',
        '',
        ICONS.chip
      )
    );
  } else {
    chips.push(
      chip(
        'NVIDIA GPU не найден',
        'warn',
        ICONS.alert
      )
    );
  }

  if (status.ram_gb){
    chips.push(
      chip(
        'RAM свободно: ' + status.ram_gb + ' ГБ',
        '',
        ICONS.info
      )
    );
  }

  chips.push(
    chip(
      status.llama.found
        ? 'llama.cpp: найден'
        : 'llama.cpp: не найден',
      status.llama.found ? 'ok' : 'err',
      status.llama.found
        ? ICONS.check
        : ICONS.alert
    )
  );

  let extra = '';

  if (status.llama.found){
    extra =
      '<div class="hint" style="margin-top:8px">' +
      '<code>' + esc(status.llama.exe) + '</code>' +
      '</div>';

    markDone(1);
  } else {
    extra =
      '<div class="row" style="margin-top:10px">' +
        '<button ' +
          'class="primary" ' +
          'onclick="installLlama()" ' +
          'type="button">' +
          'Установить llama.cpp автоматически' +
        '</button>' +

        '<div ' +
          'class="field" ' +
          'style="flex:1;min-width:240px">' +
          '<label>Или укажите путь к папке llama.cpp</label>' +
          '<input ' +
            'type="text" ' +
            'id="llamaDir" ' +
            'placeholder="C:\\llama.cpp">' +
        '</div>' +

        '<button ' +
          'class="ghost" ' +
          'onclick="setLlamaDir()" ' +
          'type="button">' +
          'Указать' +
        '</button>' +
      '</div>';
  }

  $('#env').innerHTML =
    '<div class="chips">' +
    chips.join('') +
    '</div>' +
    extra;

  const installation = status.install;

  if (
    installation.active ||
    installation.stage === 'done' ||
    installation.stage === 'error'
  ){
    $('#installBox').style.display = 'block';
    $('#instBar').style.width =
      String(installation.pct || 0) + '%';
    $('#instMsg').textContent =
      installation.message || '';

    $('#instMsg').style.color =
      installation.error ? 'var(--err)' : '';

    if (installation.stage === 'done'){
      markDone(1);
    }
  } else {
    $('#installBox').style.display = 'none';
  }

  if (
    status.server &&
    status.server.running &&
    status.server.url
  ){
    showRunning(status.server.url, false);
    markDone(4);
  }

  if (!state.scanPoll){
    state.scanPoll = setInterval(pollScan, 1500);
  }

  if (!state.logPoll){
    state.logPoll = setInterval(pollLog, 2000);
  }

  return status;
}

function chip(text, className, icon){
  return (
    '<span class="chip ' +
    (className || '') +
    '">' +
    (icon || '<span class="dot"></span>') +
    '<span>' + esc(text) + '</span>' +
    '</span>'
  );
}

/* ---------- llama.cpp installation ---------- */

async function installLlama(){
  try {
    const result = await api('/api/install', {});

    if (result.error){
      toast(result.error, 'err');
      return;
    }

    $('#installBox').style.display = 'block';
    $('#instBar').classList.remove('idle');

    toast('Началась установка llama.cpp', 'info');

    if (!state.installPoll){
      pollInstall();
    }
  } catch (error){
    toast(
      'Не удалось начать установку: ' +
      error.message,
      'err'
    );
  }
}

async function pollInstall(){
  try {
    const installation = await api('/api/install');

    $('#installBox').style.display = 'block';
    $('#instBar').style.width =
      String(installation.pct || 0) + '%';
    $('#instMsg').textContent =
      installation.message || '';

    $('#instMsg').style.color =
      installation.error ? 'var(--err)' : '';

    if (installation.active){
      state.installPoll = setTimeout(() => {
        state.installPoll = null;
        pollInstall();
      }, 1500);
      return;
    }

    if (installation.stage === 'done'){
      state.installPoll = null;
      toast('llama.cpp установлен', 'ok');
      await loadStatus();
      return;
    }

    if (installation.stage === 'error'){
      state.installPoll = null;
      toast(
        installation.error || 'Ошибка установки',
        'err'
      );
      return;
    }

    state.installPoll = null;
  } catch (error){
    state.installPoll = null;
    toast(
      'Ошибка проверки установки: ' +
      error.message,
      'err'
    );
  }
}

async function setLlamaDir(){
  const input = $('#llamaDir');

  if (!input){
    toast('Поле пути недоступно', 'err');
    return;
  }

  const directory = input.value.trim();

  if (!directory){
    toast('Введите путь к папке llama.cpp', 'warn');
    return;
  }

  try {
    const result = await api(
      '/api/config',
      {llama_dir:directory}
    );

    if (result.error){
      toast(result.error, 'err');
      return;
    }

    const status = await loadStatus();

    if (status && status.llama.found){
      toast('llama-server найден', 'ok');
    } else {
      toast(
        'llama-server не найден по указанному пути',
        'err'
      );
    }
  } catch (error){
    toast(
      'Не удалось сохранить путь: ' +
      error.message,
      'err'
    );
  }
}

/* ---------- disks and known folders ---------- */

async function loadDisks(){
  try {
    const result = await api('/api/disks');
    const buttons = [];

    (result.disks || []).forEach(disk => {
      const free =
        disk.free_gb != null
          ? ' · ' + disk.free_gb + ' ГБ свободно'
          : '';

      buttons.push(
        '<button ' +
          'class="ghost disk-btn" ' +
          'data-path="' +
          encodeURIComponent(disk.path) +
          '" ' +
          'type="button">' +
          esc(disk.path) +
          esc(free) +
        '</button>'
      );
    });

    $('#disks').innerHTML =
      buttons.join('') ||
      '<span class="hint">Диски не найдены</span>';

    $$('.disk-btn').forEach(button => {
      button.addEventListener('click', function(){
        $('#scanPath').value =
          decodeURIComponent(
            this.getAttribute('data-path') || ''
          );

        startScan();
      });
    });

    const knownFolders = (result.known || []).map(path => {
      return (
        '<div class="hint">' +
          'Найдена папка с моделями: ' +
          '<a ' +
            'href="#" ' +
            'class="known-dir" ' +
            'data-path="' +
            encodeURIComponent(path) +
            '">' +
            esc(path) +
          '</a>' +
        '</div>'
      );
    });

    $('#knownDirs').innerHTML =
      knownFolders.join('');

    $$('.known-dir').forEach(link => {
      link.addEventListener('click', function(event){
        event.preventDefault();

        $('#scanPath').value =
          decodeURIComponent(
            this.getAttribute('data-path') || ''
          );
      });
    });
  } catch (error){
    $('#disks').innerHTML =
      '<span class="hint">Не удалось получить список дисков</span>';

    toast(
      'Ошибка загрузки дисков: ' +
      error.message,
      'err'
    );
  }
}

/* ---------- scanning ---------- */

async function startScan(){
  const path = $('#scanPath').value.trim();

  if (!path){
    toast('Укажите папку или диск', 'warn');
    return;
  }

  try {
    const result = await api(
      '/api/scan',
      {path:path}
    );

    if (result.error){
      toast(result.error, 'err');
      $('#scanInfo').textContent =
        result.error;
      return;
    }

    state.lastScanDone = false;
    state.selected = null;
    state.models = [];

    $('#models').innerHTML =
      '<div class="hint">' +
      'Сканирование выполняется...' +
      '</div>';

    $('#modelsCount').style.display = 'none';
    $('#runInfo').textContent =
      'Сначала выберите модель.';
    $('#runForm').style.display = 'none';
    $('#runBtns').style.display = 'none';
    $('#runStatus').innerHTML = '';
    $('#logWrap').style.display = 'none';

    $('#scanInfo').textContent =
      'Сканирую...';

    setStep(2);
  } catch (error){
    toast(
      'Ошибка запуска сканирования: ' +
      error.message,
      'err'
    );
  }
}

async function stopScan(){
  try {
    const result = await api(
      '/api/scan/stop',
      {}
    );

    if (result.error){
      toast(result.error, 'err');
      return;
    }

    $('#scanInfo').textContent =
      'Остановка сканирования...';
  } catch (error){
    toast(
      'Ошибка остановки сканирования: ' +
      error.message,
      'err'
    );
  }
}

async function pollScan(){
  try {
    const status = await api('/api/scan');

    if (status.running){
      $('#scanInfo').textContent =
        'Ищу... найдено: ' +
        status.count +
        ' · сейчас: ' +
        (status.current || 'подготовка');

      return;
    }

    if (status.error){
      $('#scanInfo').textContent =
        'Ошибка: ' + status.error;

      toast(status.error, 'err');
      return;
    }

    if (!status.done || state.lastScanDone){
      return;
    }

    state.lastScanDone = true;

    if (status.count > 0){
      await renderModels();
      markDone(2);
    } else {
      $('#models').innerHTML =
        '<div class="hint">' +
        'GGUF-модели не найдены.' +
        '</div>';

      $('#modelsCount').style.display = 'none';

      $('#scanInfo').textContent =
        'Готово. Модели не найдены.';
    }
  } catch (error){
    $('#scanInfo').textContent =
      'Ошибка связи с лаунчером';

    console.warn('Scan polling error:', error);
  }
}

/* ---------- models ---------- */

async function renderModels(){
  try {
    const result = await api('/api/scan_results');

    state.models = result.models || [];

    if (!state.models.length){
      $('#models').innerHTML =
        '<div class="hint">' +
        'GGUF-модели не найдены.' +
        '</div>';

      return;
    }

    $('#modelsCount').style.display = '';
    $('#modelsCountN').textContent =
      String(state.models.length);

    const html = state.models.map((model, index) => {
      const parts = String(model.path || '')
        .split(/[\\\/]/);

      const name = parts[parts.length - 1] || model.path;

      return (
        '<div ' +
          'class="model" ' +
          'id="m' + index + '" ' +
          'onclick="selectModel(' + index + ')">' +

          '<div class="model-icon">' +
            ICONS.cube +
          '</div>' +

          '<div class="model-body">' +
            '<div class="model-name">' +
              esc(name) +
            '</div>' +

            '<div class="model-path">' +
              esc(model.path) +
            '</div>' +
          '</div>' +

          '<div class="model-side">' +
            fmtSize(model.size) +
          '</div>' +
        '</div>'
      );
    }).join('');

    $('#models').innerHTML =
      '<div class="models">' +
      html +
      '</div>';

    $('#scanInfo').textContent =
      'Готово. Найдено моделей: ' +
      state.models.length;

    setStep(3);
  } catch (error){
    toast(
      'Ошибка загрузки моделей: ' +
      error.message,
      'err'
    );
  }
}

async function selectModel(index){
  const model = state.models[index];

  if (!model){
    toast('Модель не найдена в списке', 'err');
    return;
  }

  state.selected = model;

  $$('.model').forEach(element => {
    element.classList.remove('sel');
  });

  const element = document.getElementById('m' + index);

  if (element){
    element.classList.add('sel');
  }

  $('#runInfo').innerHTML =
    '<div class="hint">Анализирую модель...</div>';

  try {
    const result = await api(
      '/api/analyze',
      {path:model.path}
    );

    if (result.error){
      $('#runInfo').textContent =
        'Ошибка анализа: ' + result.error;

      toast(
        'Ошибка анализа: ' + result.error,
        'err'
      );

      return;
    }

    const gpu = result.gpu;

    const gpuText = gpu
      ? 'GPU ' +
        esc(gpu.name) +
        ', свободно ' +
        Math.round(gpu.vram_free_mb / 1024) +
        ' ГБ'
      : 'NVIDIA GPU не найден — расчёт только на CPU';

    const information = [];

    information.push(
      '<div class="chips">'
    );

    information.push(
      chip(
        'архитектура: ' + result.arch,
        '',
        ICONS.info
      )
    );

    information.push(
      chip(
        'квант: ' + result.quant,
        'ok',
        ICONS.info
      )
    );

    information.push(
      chip(
        'контекст модели: ' +
        (result.model_ctx || '?'),
        '',
        ICONS.info
      )
    );

    information.push(
      chip(
        'размер: ' + result.size_gb + ' ГБ',
        '',
        ICONS.info
      )
    );

    information.push('</div>');

    information.push(
      '<div class="hint" style="margin-top:8px">' +
        gpuText +
        ' · рекомендация: ' +
        '<b>контекст ' +
        result.rec.ctx +
        '</b>, ' +
        '<b>-ngl ' +
        result.rec.ngl +
        '</b>' +
        (
          result.rec.full_gpu
            ? ' (полностью помещается в VRAM)'
            : ' (частично на GPU)'
        ) +
      '</div>'
    );

    $('#runInfo').innerHTML =
      information.join('');

    $('#ctx').value = result.rec.ctx;
    $('#ngl').value = result.rec.ngl;

    $('#runForm').style.display = 'flex';
    $('#runBtns').style.display = 'flex';

    setStep(4);
  } catch (error){
    $('#runInfo').textContent =
      'Ошибка связи с лаунчером: ' +
      error.message;

    toast(
      'Ошибка анализа модели: ' +
      error.message,
      'err'
    );
  }
}
/* ---------- server ---------- */

function getRunValues(){
  const context = Number.parseInt($('#ctx').value, 10);
  const gpuLayers = Number.parseInt($('#ngl').value, 10);
  const host = $('#host').value.trim();

  if (!Number.isInteger(context) || context < 512 || context > 1000000){
    throw new Error(
      'Контекст должен быть от 512 до 1000000 токенов'
    );
  }

  if (
    !Number.isInteger(gpuLayers) ||
    gpuLayers < 0 ||
    gpuLayers > 999
  ){
    throw new Error(
      'Количество GPU-слоёв должно быть от 0 до 999'
    );
  }

  if (!host){
    throw new Error('Укажите хост');
  }

  return {
    ctx: context,
    ngl: gpuLayers,
    host: host
  };
}

async function run(){
  if (!state.selected){
    toast('Сначала выберите модель', 'warn');
    return;
  }

  let values;

  try {
    values = getRunValues();
  } catch (error){
    toast(error.message, 'warn');
    return;
  }

  const button = document.querySelector(
    '#runBtns button.ok'
  );

  if (button){
    button.disabled = true;
  }

  try {
    const result = await api(
      '/api/run',
      {
        path: state.selected.path,
        ctx: values.ctx,
        ngl: values.ngl,
        host: values.host
      }
    );

    if (result.error){
      toast(result.error, 'err');

      $('#runStatus').innerHTML =
        chip(
          result.error,
          'err',
          ICONS.alert
        );

      return;
    }

    if (!result.url){
      toast(
        'Сервер запущен, но адрес не получен',
        'warn'
      );

      return;
    }

    showRunning(result.url, true);
    toast('Сервер запущен', 'ok');
  } catch (error){
    toast(
      'Не удалось запустить сервер: ' +
      error.message,
      'err'
    );

    $('#runStatus').innerHTML =
      chip(
        error.message,
        'err',
        ICONS.alert
      );
  } finally {
    if (button){
      button.disabled = false;
    }
  }
}

function showRunning(url, openBrowser){
  const safeUrl = esc(url);

  $('#runStatus').innerHTML =
    '<a ' +
      'class="btn ok" ' +
      'href="' + safeUrl + '" ' +
      'target="_blank" ' +
      'rel="noopener noreferrer">' +
      'Открыть чат → ' +
      safeUrl +
    '</a>';

  $('#logWrap').style.display = 'block';

  markDone(4);

  if (openBrowser){
    setTimeout(() => {
      window.open(url, '_blank', 'noopener');
    }, 700);
  }
}

async function stopSrv(){
  try {
    const result = await api('/api/stop', {});

    if (result.error){
      toast(result.error, 'err');
      return;
    }

    $('#runStatus').innerHTML = '';
    $('#logWrap').style.display = 'none';
    $('#logBox').textContent = '';

    toast('Сервер остановлен', 'info');
  } catch (error){
    toast(
      'Не удалось остановить сервер: ' +
      error.message,
      'err'
    );
  }
}

/* ---------- server log ---------- */

async function pollLog(){
  try {
    const result = await api('/api/log');
    const box = $('#logBox');

    if (result.lines && result.lines.length){
      box.textContent =
        result.lines.slice(-80).join('\n');

      box.scrollTop = box.scrollHeight;
    }

    if (
      !result.running &&
      $('#logWrap').style.display !== 'none' &&
      result.lines &&
      result.lines.length
    ){
      const lastLine =
        result.lines[result.lines.length - 1] || '';

      if (
        lastLine.includes('process exited') &&
        !$('#runStatus').textContent.includes('запущен')
      ){
        toast(
          'llama-server завершил работу',
          'warn'
        );
      }
    }
  } catch (error){
    console.warn('Log polling error:', error);
  }
}

async function copyLog(){
  const box = $('#logBox');
  const text = box.textContent.trim();

  if (!text){
    toast('Журнал пуст', 'warn');
    return;
  }

  if (
    navigator.clipboard &&
    typeof navigator.clipboard.writeText === 'function'
  ){
    try {
      await navigator.clipboard.writeText(text);
      toast('Журнал скопирован', 'ok');
      return;
    } catch (_) {
      // Use the fallback below.
    }
  }

  const area = document.createElement('textarea');

  area.value = text;
  area.style.position = 'fixed';
  area.style.left = '-9999px';
  area.style.top = '0';

  document.body.appendChild(area);
  area.focus();
  area.select();

  try {
    const copied = document.execCommand('copy');

    if (copied){
      toast('Журнал скопирован', 'ok');
    } else {
      toast('Не удалось скопировать журнал', 'err');
    }
  } catch (_) {
    toast('Не удалось скопировать журнал', 'err');
  } finally {
    area.remove();
  }
}

/* ---------- keyboard shortcuts ---------- */

document.addEventListener('keydown', event => {
  if (event.key === 'Escape'){
    closeHelp();
  }

  if (
    event.key === 'Enter' &&
    document.activeElement === $('#scanPath')
  ){
    startScan();
  }
});

/* ---------- initialization ---------- */

async function init(){
  await loadStatus();
  await loadDisks();
}

init().catch(error => {
  console.error('Initialization error:', error);
  toast(
    'Ошибка запуска интерфейса: ' + error.message,
    'err'
  );
});
</script>
</body>
</html>
'''
