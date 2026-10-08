#!/usr/bin/env python3
"""Превью ссылки на главную (og-image.png, 1200×630): имя и коллаж «стикеров» проектов на клетчатом фоне.
Рендер — headless Chrome (CHROME в окружении или стандартный путь macOS), шрифты из Google Fonts.
Запуск из корня репозитория: python3 tools/build_og.py
"""
import os
import subprocess
import tempfile

CHROME = os.environ.get('CHROME', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')

HTML = '''<!doctype html><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Onest:wght@400..800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}html,body{margin:0}
body{position:relative;width:1200px;height:630px;overflow:hidden;font-family:"Onest",Helvetica,Arial,sans-serif;color:#111;
  background-color:#f6f5f0;
  background-image:linear-gradient(rgba(0,0,0,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(0,0,0,.07) 1px,transparent 1px);
  background-size:30px 30px}
.tag{position:absolute;left:64px;top:56px;padding:8px 16px;background:#111;color:#d4f56a;font-family:"JetBrains Mono",monospace;font-weight:700;font-size:23px;border-radius:10px}
h1{position:absolute;left:60px;top:116px;margin:0;font-weight:800;font-size:132px;line-height:.92;letter-spacing:-.05em}
h1 span{background:linear-gradient(transparent 62%,#d4f56a 62%,#d4f56a 94%,transparent 94%)}
.sub{position:absolute;left:64px;top:410px;max-width:560px;font-size:40px;line-height:1.18;font-weight:600;letter-spacing:-.02em}
.sub b{background:#ffdd2d;padding:0 .12em;border-radius:6px}
.foot{position:absolute;left:64px;bottom:44px;font-family:"JetBrains Mono",monospace;font-weight:700;font-size:25px}
.st{position:absolute;border:4px solid #111;border-radius:26px;box-shadow:9px 9px 0 #111;padding:22px 26px}
.st h3{margin:0;font-weight:800;font-size:40px;letter-spacing:-.03em;line-height:1}
.st p{margin:8px 0 0;font-size:22px;font-weight:500}
.em{position:absolute;font-size:92px;line-height:1;filter:drop-shadow(5px 5px 0 rgba(0,0,0,.18))}
</style>
<div class="tag">vmaiorov-collab.github.io</div>
<h1>Вячеслав<br><span>Майоров</span></h1>
<div class="sub">конспекты, <b>игры</b> и приложения</div>
<div class="foot">@MayorovTLF · github.com/vmaiorov-collab</div>

<div class="st" style="left:700px;top:40px;width:270px;background:#ffdd2d;transform:rotate(-6deg)"><h3>Т-Банк</h3><p>13 занятий</p>
 <div style="display:flex;gap:8px;margin-top:14px">%CHIPS_T%</div></div>
<div class="st" style="left:930px;top:96px;width:240px;background:#e4d6ff;transform:rotate(5deg)"><h3>Яндекс Кружок</h3><p>15 занятий</p>
 <div style="display:flex;gap:8px;margin-top:14px">%CHIPS_Y%</div></div>

<div class="st" style="left:690px;top:260px;width:176px;height:176px;background:#ffd3b0;transform:rotate(4deg);padding:14px">
 <svg viewBox="0 0 120 120" width="136" height="136"><g stroke="#111" stroke-width="5" stroke-linecap="round" fill="none">
  <path d="M40 8v104M80 8v104M8 40h104M8 80h104"/>
  <path d="M14 14l20 20M34 14l-20 20" stroke="#e8423a"/><path d="M86 14l20 20M106 14l-20 20" stroke="#e8423a"/><path d="M50 90l20 20M70 90l-20 20" stroke="#e8423a"/>
  <circle cx="60" cy="60" r="11" stroke="#2f6fe0"/><circle cx="20" cy="100" r="11" stroke="#2f6fe0"/></g></svg></div>

<div class="st" style="left:896px;top:306px;width:262px;height:188px;background:#111;transform:rotate(-4deg);padding:0;overflow:hidden">
 <svg viewBox="0 0 270 196" width="262" height="188"><defs><filter id="g"><feGaussianBlur stdDeviation="4"/></filter></defs>
  <path d="M30 150 H110 V70 H190 V120 H240" fill="none" stroke="#7cff6b" stroke-width="16" stroke-linecap="round" stroke-linejoin="round" filter="url(#g)" opacity=".7"/>
  <path d="M30 150 H110 V70 H190 V120 H240" fill="none" stroke="#7cff6b" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="240" cy="120" r="9" fill="#fff"/><circle cx="244" cy="117" r="3" fill="#111"/>
  <circle cx="60" cy="40" r="11" fill="#ff4fa3"/><text x="18" y="184" fill="#7cff6b" font-family="JetBrains Mono,monospace" font-weight="700" font-size="20">NEON SNAKE</text></svg></div>

<div class="em" style="left:690px;top:490px;transform:rotate(-8deg)">🧩</div>
<div class="em" style="left:810px;top:508px;transform:rotate(6deg)">📅</div>
<div class="em" style="left:935px;top:500px;transform:rotate(-5deg)">🧠</div>
<div class="em" style="left:1058px;top:500px;transform:rotate(9deg)">🗂️</div>
'''
chip = lambda t, bg: f'<span style="background:{bg};border:3px solid #111;border-radius:999px;padding:3px 12px;font-weight:700;font-size:20px">{t}</span>'
html = (HTML.replace('%CHIPS_T%', chip('C', '#fff') + chip('BS', '#fff') + chip('X', '#fff'))
            .replace('%CHIPS_Y%', chip('A', '#fff') + chip("B'", '#fff') + chip('C', '#fff')))
with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as f:
    f.write(html)
    path = f.name
subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--virtual-time-budget=9000',
                '--window-size=1200,630', '--screenshot=og-image.png', f'file://{path}'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
os.unlink(path)
print('готово: og-image.png')
