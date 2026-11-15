"""
Start server:   uv run server.py [port]         (default 8765)
Remove a user:  uv run server.py deluser NAME   (frees the name; they can register again)
List users:     uv run server.py users
Users register themselves the first time they connect (name + token, stored as a hash).
Set PYVERN_ADMIN_TOKEN to a secret of at least 20 characters and set the client's
token in token.json to the same value to connect with admin privileges. Anyone with
this secret can connect as any valid username, so keep it private and use a trusted or
encrypted connection. Admin commands include /admin <user>, /role <user> <admin|user>,
/private <channel> <password>, and /cooldown <seconds>. Locked channels are read-only
for non-admins.
Status page:    http://localhost:<port>/
"""
import asyncio
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import time
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import websockets

USERS_FILE = Path(__file__).with_name("users.json")
CHANNELS_FILE = Path(__file__).with_name("channels.json")
SETTINGS_FILE = Path(__file__).with_name("settings.json")
NAME_RE = re.compile(r"[A-Za-z0-9_-]{1,20}")
CHAN_RE = re.compile(r"[a-z0-9_-]{1,20}")
DEFAULT_CHANNEL = "general"
ADMIN_TOKEN = os.environ.get("PYVERN_ADMIN_TOKEN", "")


clients = {}
locked_channels = set()
private_channels = {}
cooldown_seconds = 0
START = time.time()

PAGE = """<!doctype html>
<meta charset="utf-8">
<title>Chat status</title>
<body style="font-family:sans-serif;max-width:480px;margin:40px auto">
<h2>Chat server: <span id="state">checking...</span></h2>
<p>Uptime: <span id="up">-</span> | Users online: <span id="count">0</span></p>
<div id="channels"></div>
<script>
async function refresh() {
  const state = document.getElementById("state");
  try {
    const d = await (await fetch("status", {cache: "no-store"})).json();
    state.textContent = "ONLINE"; state.style.color = "green";
    document.getElementById("up").textContent = Math.floor(d.uptime) + "s";
    document.getElementById("count").textContent = d.online;
    const privateChannels = new Set(d.private_channels);
    document.getElementById("channels").replaceChildren(
      ...Object.entries(d.channels).map(([ch, users]) => {
        const div = document.createElement("div");
        const h = document.createElement("h3");
        h.textContent = (privateChannels.has(ch) ? "🔒 " : "") + "#" + ch + " (" + users.length + ")";
        const ul = document.createElement("ul");
        users.forEach(u => {
          const li = document.createElement("li");
          li.textContent = u;
          ul.appendChild(li);
        });
        div.append(h, ul);
        return div;
      }));
  } catch (e) {
    state.textContent = "OFFLINE"; state.style.color = "red";
  }
}
refresh(); setInterval(refresh, 3000);
</script>
"""


# ---------- users & tokens (only SHA-256) ----------
def load_users():
    try:
        return json.loads(USERS_FILE.read_text())
    except FileNotFoundError:
        return {}


def save_users(users):
    USERS_FILE.write_text(json.dumps(users, indent=2))
    try:
        os.chmod(USERS_FILE, 0o600)
    except OSError:
        pass


def load_private_channels():
    try:
        return json.loads(CHANNELS_FILE.read_text())
    except FileNotFoundError:
        return {}


def save_private_channels(channels):
    CHANNELS_FILE.write_text(json.dumps(channels, indent=2))
    try:
        os.chmod(CHANNELS_FILE, 0o600)
    except OSError:
        pass


def load_cooldown():
    try:
        settings = json.loads(SETTINGS_FILE.read_text())
    except FileNotFoundError:
        return 0
    value = settings.get("cooldown_seconds", 0)
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"Invalid cooldown_seconds in {SETTINGS_FILE}")
    return value


def save_cooldown(seconds):
    SETTINGS_FILE.write_text(json.dumps({"cooldown_seconds": seconds}, indent=2))
    try:
        os.chmod(SETTINGS_FILE, 0o600)
    except OSError:
        pass


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def hash_channel_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000).hex()


def is_admin_token(token):
    return bool(ADMIN_TOKEN) and hmac.compare_digest(token, ADMIN_TOKEN)


def login(name, token):
    """Authenticate a registered token or allow the configured admin token."""
    if not NAME_RE.fullmatch(name) or len(token) < 20:
        return False
    is_admin = is_admin_token(token)
    users = load_users()  # re-read each time so deluser works without a restart
    rec = users.get(name)
    if rec is None:
        if name.lower() in {n.lower() for n in users}:
            return False  # too close to an existing name
        users[name] = {
            "token_hash": hash_token(token),
            "created": time.strftime("%Y-%m-%d %H:%M"),
            "role": "user",
        }
        save_users(users)
        print(f"* registered new user {name}")
        return True
    return is_admin or hmac.compare_digest(rec["token_hash"], hash_token(token))


def user_is_admin(name, token):
    if is_admin_token(token):
        return True
    users = load_users()
    user = next((record for username, record in users.items()
                 if username.casefold() == name.casefold()), {})
    return user.get("role", "user") == "admin"


def cli_deluser(name):
    users = load_users()
    if users.pop(name, None) is None:
        sys.exit(f"No such user '{name}'")
    save_users(users)
    print(f"Removed {name}. Their token no longer works for new connections.")


def cli_users():
    for name, rec in load_users().items():
        print(f"{name}  (created {rec.get('created', '?')})")


# ---------- chat ----------
def clean(text, limit=500):
    return "".join(ch for ch in text if ch.isprintable())[:limit].strip()


def channel_map():
    chans = {DEFAULT_CHANNEL: []}
    for channel in private_channels:
        chans.setdefault(channel, [])
    for info in clients.values():
        if not info.get("invis"):
            chans.setdefault(info["channel"], []).append(info["name"])
    return {c: sorted(n) for c, n in sorted(chans.items())}


def frame(kind, **kw):
    """Everything sent to clients is JSON: {"t": type, "ts": epoch seconds, ...}."""
    return json.dumps({"t": kind, "ts": time.time(), **kw})


def notify(channel, kind, exclude=None, **kw):
    targets = [c for c, i in clients.items() if i["channel"] == channel and c is not exclude]
    websockets.broadcast(targets, frame(kind, **kw))


async def command(ws, info, text):
    cmd, _, arg = text.partition(" ")
    arg = arg.strip().lstrip("#")
    name, old = info["name"], info["channel"]
    if cmd == "/join":
        parts = text.split(maxsplit=2)
        channel = parts[1].lstrip("#").lower() if len(parts) > 1 else ""
        password = parts[2] if len(parts) > 2 else ""
        if not CHAN_RE.fullmatch(channel):
            await ws.send(frame("sys", text="Channel names: 1-20 chars, a-z 0-9 _ -"))
        elif channel == old:
            await ws.send(frame("sys", text=f"You're already in #{old}"))
        elif channel in private_channels and not info["admin"] and not hmac.compare_digest(
            hash_channel_password(password, bytes.fromhex(private_channels[channel]["salt"])),
            private_channels[channel]["password_hash"],
        ):
            await ws.send(frame("sys", text=f"Password required to join #{channel}. Usage: /join {channel} <password>"))
        else:
            if not info.get("invis"):
                notify(old, "sys", exclude=ws, text=f"* {name} left #{old}")
            info["channel"] = channel
            if not info.get("invis"):
                notify(channel, "sys", exclude=ws, text=f"* {name} joined #{channel}")
            await ws.send(frame("channel", channel=channel))
            await ws.send(frame("sys", text=f"You joined #{channel}"))
    elif cmd == "/channels":
        listing = ", ".join(
            f"{'🔒 ' if c in private_channels else ''}#{c} ({len(u)})"
            for c, u in channel_map().items()
        )
        await ws.send(frame("sys", text="Channels: " + listing))
    elif cmd == "/users":
        await ws.send(frame("sys", text=f"In #{old}: " + ", ".join(channel_map().get(old, []))))
    elif cmd == "/invis":
        if not info["admin"]:
            await ws.send(frame("sys", text="Admin only."))
        elif info.get("invis"):
            info["invis"] = False
            notify(old, "sys", exclude=ws, text=f"* {name} joined #{old}")
            await ws.send(frame("sys", text="You are now visible."))
        else:
            info["invis"] = True
            await ws.send(frame("sys", text="You are now invisible."))
    elif cmd == "/private":
        parts = text.split(maxsplit=2)
        channel = parts[1].lstrip("#").lower() if len(parts) > 1 else ""
        password = parts[2] if len(parts) > 2 else ""
        if not CHAN_RE.fullmatch(channel) or not password:
            await ws.send(frame("sys", text="Usage: /private <channel> <password>"))
            return
        existing = private_channels.get(channel)
        if existing and not info["admin"] and existing.get("owner") != name:
            await ws.send(frame("sys", text=f"Only the owner of #{channel} or an admin can change its password."))
            return
        if not existing and not info["admin"] and channel in channel_map():
            await ws.send(frame("sys", text=f"#{channel} already exists. Choose a new channel name."))
            return
        salt = secrets.token_bytes(16)
        private_channels[channel] = {
            "salt": salt.hex(),
            "password_hash": hash_channel_password(password, salt),
            "owner": existing.get("owner", name) if existing else name,
        }
        save_private_channels(private_channels)
        await ws.send(frame("sys", text=f"#{channel} is now password-protected."))
    elif cmd == "/public":
        channel = arg.lower()
        existing = private_channels.get(channel)
        if not CHAN_RE.fullmatch(channel):
            await ws.send(frame("sys", text="Usage: /public <channel>"))
        elif existing is None:
            await ws.send(frame("sys", text=f"#{channel} is not password-protected."))
        elif not info["admin"] and existing.get("owner") != name:
            await ws.send(frame("sys", text=f"Only the owner of #{channel} or an admin can make it public."))
        else:
            del private_channels[channel]
            save_private_channels(private_channels)
            await ws.send(frame("sys", text=f"#{channel} is now public."))
    elif cmd in {"/kick", "/lock", "/unlock", "/role", "/admin", "/cooldown"}:
        if not info["admin"]:
            await ws.send(frame("sys", text="Admin only."))
        elif cmd == "/kick":
            target_name = arg.casefold()
            targets = [
                target for target, target_info in clients.items()
                if target_info["channel"] == old
                and target_info["name"].casefold() == target_name
            ]
            if not target_name:
                await ws.send(frame("sys", text="Usage: /kick <user>"))
            elif not targets:
                await ws.send(frame("sys", text=f"No user named {arg} is in #{old}"))
            else:
                shown = clients[targets[0]]["name"]
                notify(old, "sys", text=f"* {shown} was kicked by {name}")
                for target in targets:
                    await target.close(code=1008, reason="Kicked by admin")
        elif cmd in {"/role", "/admin"}:
            parts = text.split()
            usage = "Usage: /admin <user>" if cmd == "/admin" else "Usage: /role <user> <admin|user>"
            if (cmd == "/admin" and len(parts) != 2) or (cmd == "/role" and len(parts) != 3):
                await ws.send(frame("sys", text=usage))
                return
            target_arg = parts[1]
            role = "admin" if cmd == "/admin" else parts[2].lower()
            if not NAME_RE.fullmatch(target_arg) or role not in {"admin", "user"}:
                await ws.send(frame("sys", text=usage))
                return
            users = load_users()
            target_name = next((user for user in users if user.casefold() == target_arg.casefold()), None)
            if target_name is None:
                await ws.send(frame("sys", text=f"No registered user named {target_arg}."))
                return
            users[target_name]["role"] = role
            save_users(users)
            for target_info in clients.values():
                if target_info["name"].casefold() == target_name.casefold():
                    target_info["admin"] = role == "admin"
                    if role != "admin" and target_info.get("invis"):
                        target_info["invis"] = False
                        notify(target_info["channel"], "sys", text=f"* {target_name} joined #{target_info['channel']}")
            await ws.send(frame("sys", text=f"{target_name} is now {role}."))
        elif cmd == "/cooldown":
            value = arg.lower()
            if value in {"off", "0", "0s"}:
                seconds = 0
            else:
                match = re.fullmatch(r"([0-9]+)s", value)
                if not match or int(match.group(1)) > 3600:
                    await ws.send(frame("sys", text="Usage: /cooldown <0s|1s-3600s|off>"))
                    return
                seconds = int(match.group(1))
            global cooldown_seconds
            cooldown_seconds = seconds
            save_cooldown(seconds)
            await ws.send(frame("sys", text=f"Non-admin message cooldown set to {seconds}s."))
        else:
            channel = (arg or old).lower()
            if not CHAN_RE.fullmatch(channel):
                await ws.send(frame("sys", text="Channel names: 1-20 chars, a-z 0-9 _ -"))
            elif cmd == "/lock":
                locked_channels.add(channel)
                notify(channel, "sys", text=f"* #{channel} is now read-only (locked by {name})")
            else:
                locked_channels.discard(channel)
                notify(channel, "sys", text=f"* #{channel} is unlocked by {name}")
    else:
        commands = "Commands: /join <channel> [password], /private <channel> <password>, /public <channel>, /channels, /users, /exit, /token (show your token)"
        if info["admin"]:
            commands += ", /invis, /kick <user>, /lock [channel], /unlock [channel], /admin <user>, /role <user> <admin|user>, /cooldown <0s|1s-3600s|off>"
        await ws.send(frame("sys", text=commands))


async def handler(ws):
    name = ws.username
    info = {"name": name, "channel": DEFAULT_CHANNEL, "admin": ws.is_admin, "invis": False}
    clients[ws] = info
    print(f"+ {name} connected" + (" (admin)" if info["admin"] else ""))
    await ws.send(frame("channel", channel=DEFAULT_CHANNEL))
    await ws.send(frame("sys", text=f"Logged in as {name}. Type /help for commands."))
    if info["admin"]:
        await ws.send(frame("sys", text="Admin access enabled."))
    if not info["invis"]:
        notify(DEFAULT_CHANNEL, "sys", exclude=ws, text=f"* {name} joined #{DEFAULT_CHANNEL}")
    try:
        async for raw in ws:
            if not isinstance(raw, str):
                continue
            text = clean(raw)
            if not text:
                continue
            if text.startswith("/"):
                await command(ws, info, text)
            else:
                if info["channel"] in locked_channels and not info["admin"]:
                    await ws.send(frame("sys", text=f"#{info['channel']} is locked; only admins can chat."))
                    continue
                now = time.monotonic()
                remaining = cooldown_seconds - (now - info.get("last_message", 0))
                if not info["admin"] and remaining > 0:
                    await ws.send(frame("sys", text=f"Please wait {remaining:.1f}s before sending another message."))
                    continue
                info["last_message"] = now
                notify(info["channel"], "chat", exclude=ws, name=name, text=text)
    except websockets.ConnectionClosed:
        pass
    finally:
        clients.pop(ws, None)
        if not info.get("invis"):
            notify(info["channel"], "sys", text=f"* {name} left #{info['channel']}")
        print(f"- {name} disconnected")


def http_route(connection, request):
    if request.headers.get("Upgrade", "").lower() == "websocket":
        name = parse_qs(urlparse(request.path).query).get("name", [""])[0]
        auth = request.headers.get("Authorization", "")
        token = auth[7:].strip() if auth.startswith("Bearer ") else ""
        if not login(name, token):
            return connection.respond(HTTPStatus.UNAUTHORIZED, "Name taken or wrong token\n")
        connection.username = name
        connection.is_admin = user_is_admin(name, token)
        return None
    if request.path.split("?")[0] == "/status":
        body = json.dumps({"uptime": time.time() - START,
                           "online": sum(not info.get("invis") for info in clients.values()),
                           "channels": channel_map(), "private_channels": sorted(private_channels)})
        ctype = "application/json"
    else:
        body, ctype = PAGE, "text/html; charset=utf-8"
    response = connection.respond(HTTPStatus.OK, body)
    response.headers["Content-Type"] = ctype
    return response


async def serve(port):
    global private_channels, cooldown_seconds
    private_channels = load_private_channels()
    cooldown_seconds = load_cooldown()
    async with websockets.serve(handler, "0.0.0.0", port,
                                process_request=http_route, max_size=4096):
        print(f"Server on port {port} | status page: http://localhost:{port}/")
        await asyncio.Future()


if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if len(a) == 2 and a[0] == "deluser":
            cli_deluser(a[1])
        elif a == ["users"]:
            cli_users()
        elif not a or (len(a) == 1 and a[0].isdigit()):
            asyncio.run(serve(int(a[0]) if a else 8765))
        else:
            print(__doc__)
    except KeyboardInterrupt:
        pass