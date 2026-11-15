
"""Chat client. Run:  uv run chat.py   (or: pip install websockets colorama && python chat.py)"""
import asyncio
import atexit
import json
import os
import re
import secrets
import shutil
import signal
import sys
import threading
import time
from collections import deque
from pathlib import Path
from urllib.parse import quote

import websockets
from colorama import Back, Fore, Style, just_fix_windows_console
from websockets.exceptions import ConnectionClosed, InvalidStatus

just_fix_windows_console()

DEFAULT_SERVER = "0.0.0.0:8765"
TOKEN_FILE = Path(__file__).with_name("token.json")
NAME_RE = re.compile(r"[A-Za-z0-9_-]{1,20}")

ESC = "\033"
RST = Style.RESET_ALL
NAME_COLORS = [Fore.LIGHTCYAN_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTMAGENTA_EX,
               Fore.LIGHTBLUE_EX, Fore.LIGHTRED_EX]

BANNER = '''
  ▄▄▄▄▄▄     ▄▄▄       ▄▄▄         ▄▄▄▄▄▄▄   ▄▄▄▄▄▄      ▄▄     ▄▄▄
 █▀██▀▀▀█▄  █▀██  ██  █▀██  ██▀▀  █▀██▀▀▀   █▀██▀▀▀█▄    ██▄   ██▀
   ██▄▄▄█▀    ██  ██    ██  ██      ██        ██▄▄▄█▀    ███▄  ██
   ██▀▀▀      ██  ██    ██  ██      ████      ██▀▀█▄     ██ ▀█▄██
 ▄ ██         ██  ██    ██▄ ██      ██      ▄ ██  ██     ██   ▀██
 ▀██▀         ▀█████▄    ▀███▀      ▀█████  ▀██▀  ▀██▀ ▀██▀    ██
              ▄   ██
              ▀████▀
'''


def ask(label):
    print(label)
    return input("> ").strip()


def load_identity():
    """Load saved identity or create one."""
    try:
        d = json.loads(TOKEN_FILE.read_text())
        if d.get("server") and d.get("name") and d.get("token"):
            return d, False
    except (FileNotFoundError, ValueError):
        pass
    server = DEFAULT_SERVER or ask("server (IP:port or wss://host)")
    name = ask("name")
    while not NAME_RE.fullmatch(name):
        print("1-20 characters: letters, numbers, _ or -")
        name = ask("name")
    d = {"server": server, "name": name, "token": secrets.token_urlsafe(24)}
    TOKEN_FILE.write_text(json.dumps(d, indent=2))
    try:
        os.chmod(TOKEN_FILE, 0o600)
    except OSError:
        pass
    return d, True


def safe(text):
    """Remove terminal control characters."""
    return "".join(ch for ch in str(text) if ch.isprintable())


class UI:
    def __init__(self, name):
        self.name = name
        self.channel = None
        self.color = sys.stdout.isatty()
        self.fancy = self.color and sys.stdin.isatty()
        self.active = False
        self.history = deque(maxlen=300)
        self.rows, self.cols = 24, 80

    def _w(self, s):
        sys.stdout.write(s)
        sys.stdout.flush()

    def c(self, text, *codes):
        return "".join(codes) + text + RST if self.color else text

    def start(self):
        if self.fancy:
            self.active = True
            self.layout()

    def layout(self):
        size = shutil.get_terminal_size((80, 24))
        self.cols, self.rows = size.columns, max(size.lines, 10)
        R = self.rows
        self._w(f"{ESC}[2J{ESC}[r{self._header()}{ESC}[2;{R - 3}r")
        for line in list(self.history)[-(R - 4):]:
            self._w(f"{ESC}[{R - 3};1H\n{line}")

    def on_resize(self):
        if self.active:
            self.layout()
            self.prompt()

    def stop(self):
        if self.active:
            self.active = False
            self._w(f"{ESC}[r{ESC}[{self.rows - 2};1H{ESC}[J{RST}")

    def _header(self):
        left = f" #{self.channel} " if self.channel else " connecting... "
        right = f" {self.name} · /help · /exit "
        pad = max(1, self.cols - len(left) - len(right))
        text = (left + " " * pad + right)[: self.cols]
        return f"{ESC}[1;1H{Back.BLUE}{Fore.WHITE}{Style.BRIGHT}{text}{RST}"

    def prompt(self):
        if not self.active:
            return
        R = self.rows
        self._w(
            f"{ESC}[{R - 2};1H{ESC}[2K{Style.DIM}{'─' * self.cols}{RST}"
            f"{ESC}[{R - 1};1H{ESC}[2K{Style.BRIGHT}{Fore.LIGHTGREEN_EX}{self.name}:{RST}"
            f"{ESC}[{R};1H{ESC}[2K> "
        )

    def set_channel(self, channel):
        self.channel = channel
        if self.active:
            self._w(f"{ESC}7{self._header()}{ESC}8")
        else:
            self.add_line(self.c(f"-- you are in #{channel} --", Style.DIM))

    def add_line(self, text):
        self.history.append(text)
        if self.active:
            self._w(f"{ESC}7{ESC}[{self.rows - 3};1H\n{text}{ESC}8")
        else:
            print(text, flush=True)

    def stamp(self, ts):
        return self.c(time.strftime("%H:%M", time.localtime(ts)), Style.DIM)

    def chat(self, ts, name, text, own=False):
        name, text = safe(name), safe(text)
        color = Fore.LIGHTGREEN_EX if own else NAME_COLORS[sum(map(ord, name)) % len(NAME_COLORS)]
        who = self.c("You" if own else name, Style.BRIGHT, color)
        self.add_line(f"{self.stamp(ts)} {who}: {text}")

    def system(self, ts, text):
        self.add_line(f"{self.stamp(ts)} {self.c(safe(text), Fore.YELLOW)}")


async def chat(ws, ui):
    loop = asyncio.get_running_loop()
    ui.start()
    atexit.register(ui.stop)
    if hasattr(signal, "SIGWINCH"):
        loop.add_signal_handler(signal.SIGWINCH, ui.on_resize)
    for line in BANNER.strip("\n").splitlines():
        ui.add_line(ui.c(line, Fore.CYAN))
    ui.add_line(ui.c("Connected. Type a message, /help for commands, /exit to quit.", Style.DIM))
    ui.prompt()

    lines = asyncio.Queue()

    def reader():
        while True:
            line = sys.stdin.readline()
            loop.call_soon_threadsafe(lines.put_nowait, line or None)
            if not line:
                return

    threading.Thread(target=reader, daemon=True).start()

    def handle(raw):
        try:
            f = json.loads(raw)
        except ValueError:
            ui.system(time.time(), raw)
            return
        ts = f.get("ts") or time.time()
        kind = f.get("t")
        if kind == "chat":
            ui.chat(ts, f.get("name", "?"), f.get("text", ""))
        elif kind == "channel":
            ui.set_channel(safe(f.get("channel", "")))
        else:
            ui.system(ts, f.get("text", ""))

    async def receive():
        async for raw in ws:
            handle(raw)

    recv = asyncio.create_task(receive())
    reason = "Bye."
    try:
        while True:
            get = asyncio.create_task(lines.get())
            done, _ = await asyncio.wait({get, recv}, return_when=asyncio.FIRST_COMPLETED)
            if get not in done:
                get.cancel()
                reason = "Disconnected from server."
                break
            line = get.result()
            if line is None:
                break
            line = line.strip()
            if line in ("/exit", "/quit"):
                break
            if line == "/token":
                token = json.loads(TOKEN_FILE.read_text())["token"]
                ui.add_line(ui.c(f"Your token: {token}", Fore.YELLOW))
                ui.prompt()
                continue
            if line:
                await ws.send(line)
                if not line.startswith("/"):
                    ui.chat(time.time(), ui.name, line, own=True)
            ui.prompt()
    finally:
        recv.cancel()
        await asyncio.gather(recv, return_exceptions=True)
        ui.stop()
    print(reason)


async def main():
    ident, fresh = load_identity()
    addr = DEFAULT_SERVER or ident["server"]
    base = addr if addr.startswith(("ws://", "wss://")) else f"ws://{addr}"
    url = f"{base.rstrip('/')}/?name={quote(ident['name'])}"
    try:
        async with websockets.connect(
            url, additional_headers={"Authorization": f"Bearer {ident['token']}"}, ping_interval=20
        ) as ws:
            await chat(ws, UI(ident["name"]))
    except InvalidStatus as e:
        if e.response.status_code != 401:
            print(f"Server replied with HTTP {e.response.status_code}")
        elif fresh:
            TOKEN_FILE.unlink(missing_ok=True)
            print("That name is taken. Run again and pick another.")
        else:
            print("Server rejected this name/token. Delete token.json to start over with a new name.")
    except ConnectionClosed:
        print("Disconnected.")
    except OSError as e:
        if fresh:
            TOKEN_FILE.unlink(missing_ok=True)
        print(f"Can't connect: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        pass