#!/usr/bin/env python3
"""
Pong — Singleplayer & Multiplayer over LAN with rooms.
Terminal UI menu — no flags needed.
"""

import curses
import json
import os
import platform
import socket
import subprocess
import sys
import threading
import time
import random
from http.server import HTTPServer, BaseHTTPRequestHandler


# ── Globals ─────────────────────────────────────────
_DIAG = (f"{platform.system()} {platform.release()}"
         f" | {platform.machine()}"
         f" | Py {platform.python_version()}")
_SAVE_DIR = os.path.expanduser("~/.pong")
_SAVE_PATH = os.path.join(_SAVE_DIR, "save.json")

# ── Constants ───────────────────────────────────────
PADDLE_WIDTH = 1
BALL_SPEED = 1
WIN_SCORE = 5
DEFAULT_PORT = 9999
DISCOVERY_PORT = 10000
DISCOVERY_INTERVAL = 3
TICK = 0.04

ROOM_TEMPLATES = [
    "Classic", "Rally", "Speed", "Tournament", "Practice",
    "Sudden Death", "Challenge", "Arena", "Grand Slam", "Showdown",
]

FILTERED_WORDS = [
    "fuck", "shit", "ass", "bitch", "damn", "cunt", "dick", "piss",
    "bastard", "cock", "nigger", "faggot", "slut", "whore",
]

def _filter_chat(text):
    lowered = text.lower()
    for word in FILTERED_WORDS:
        idx = lowered.find(word)
        if idx != -1:
            censored = word[0] + "*" * (len(word) - 2) + word[-1]
            text = text[:idx] + censored + text[idx + len(word):]
            lowered = text.lower()
    return text


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pong Server Dashboard</title>
<style>
 *{margin:0;padding:0;box-sizing:border-box}
 body{font-family:system-ui,sans-serif;background:#111;color:#e0e0e0;padding:20px}
 h1{color:#0ff;margin-bottom:2px}
 .sub{color:#888;font-size:.9em;margin-bottom:20px}
 .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
 .card{background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:16px}
 .card h2{color:#0ff;font-size:1em;margin-bottom:12px}
 table{width:100%;border-collapse:collapse}
 th{text-align:left;color:#888;font-size:.8em;text-transform:uppercase;padding:4px 8px;border-bottom:1px solid #333}
 td{padding:6px 8px;border-top:1px solid #222}
 .badge{display:inline-block;padding:1px 6px;border-radius:3px;font-size:.75em;font-weight:600}
 .badge-play{background:#0a3;color:#fff}
 .badge-wait{background:#640;color:#fa0}
 .badge-full{background:#a00;color:#fff}
 .score{font-weight:700;color:#0ff}
 .ev{color:#aaa;font-size:.85em;padding:2px 0}
 .ev time{color:#555;margin-right:8px}
 .ft{margin-top:24px;color:#444;font-size:.8em}
</style></head><body>
<h1>&#9616;&nbsp;Pong Server</h1>
<div class="sub" id="info">Connecting...</div>
<div class="cards">
 <div class="card"><h2>&#9654;&nbsp;Rooms</h2><div id="rooms"><p style="color:#666">No rooms</p></div></div>
 <div class="card"><h2>&#9881;&nbsp;Server</h2>
  <table><tr><th>Property</th><th>Value</th></tr>
   <tr><td>Status</td><td><span class="badge badge-play">Running</span></td></tr>
   <tr><td>Players</td><td id="players">0</td></tr>
   <tr><td>Uptime</td><td id="uptime">--</td></tr>
  </table></div>
</div>
<div class="card" style="margin-top:16px"><h2>&#9776;&nbsp;Events</h2><div id="events"><p style="color:#666">None yet</p></div></div>
<div class="ft" id="footer"></div>
<script>
function fmt(s){let h=Math.floor(s/3600),m=Math.floor((s%3600)/60),s2=s%60;return h+'h '+m+'m '+s2+'s'}
function badge(txt,cls){return '<span class="badge badge-'+cls+'">'+txt+'</span>'}
async function load(){try{
 const r=await fetch('/status'),d=await r.json();
 document.getElementById('info').textContent=d.name+' | '+d.ip+':'+d.port+' | Web: http://'+d.ip+':'+d.web_port;
 let rh=d.rooms.map(r=>{
  let pn=r.player_names.join(', ')||'&mdash;';
  let st=r.playing?badge('play','play'):badge('wait','wait');
  if(r.full)st=badge('full','full');
  let sc=(r.playing||r.left_score||r.right_score)?'<span class="score">'+r.left_score+'–'+r.right_score+'</span>':'&mdash;';
  let up=fmt(r.uptime);
  return '<tr><td>'+(r.players>0?'&#9679; ':'')+r.name+'</td><td>'+st+'</td><td>'+r.players+'/2</td><td style="color:#aaa">'+pn+'</td><td>'+sc+'</td><td style="color:#555">'+up+'</td></tr>'}).join('');
 if(!rh)rh='<tr><td colspan="6" style="color:#666">No rooms</td></tr>';
 document.getElementById('rooms').innerHTML='<table><tr><th>Room</th><th>Status</th><th>Players</th><th>Names</th><th>Score</th><th>Uptime</th></tr>'+rh+'</table>';
 document.getElementById('players').textContent=d.total_players;
 document.getElementById('uptime').textContent=fmt(d.uptime);
 let eh=d.events.map(e=>'<div class="ev"><time>'+e.time+'</time>'+e.msg+'</div>').join('');
 document.getElementById('events').innerHTML=eh||'<p style="color:#666">None yet</p>';
 document.getElementById('footer').textContent='Updated: '+new Date().toLocaleTimeString();
}catch(e){}setTimeout(load,2000)}load();
</script></body></html>"""


# ── Game State ──────────────────────────────────────
class GameState:
    def __init__(self, width=80, height=24):
        self.width = width
        self.height = height
        self.reset()

    def reset(self):
        self.paddle_h = max(4, self.height // 6)
        self.left_x = 2
        self.right_x = self.width - 3
        self.left_y = self.height // 2 - self.paddle_h // 2
        self.right_y = self.height // 2 - self.paddle_h // 2
        self.ball_x = float(self.width // 2)
        self.ball_y = float(self.height // 2)
        self.ball_dir_x = 1
        self.ball_dir_y = 1
        self.left_score = 0
        self.right_score = 0
        self.sound = None

    def _pulse(self, snd):
        self.sound = snd

    def update(self, left_up, left_down, right_up, right_down):
        self.sound = None
        if left_up:
            self.left_y = max(1, self.left_y - 1)
        if left_down:
            self.left_y = min(self.height - self.paddle_h - 1, self.left_y + 1)
        if right_up:
            self.right_y = max(1, self.right_y - 1)
        if right_down:
            self.right_y = min(self.height - self.paddle_h - 1, self.right_y + 1)

        self.ball_x += self.ball_dir_x * BALL_SPEED
        self.ball_y += self.ball_dir_y * BALL_SPEED

        if self.ball_y <= 1 or self.ball_y >= self.height - 2:
            self.ball_dir_y *= -1
            self.ball_y = max(1.0, min(self.ball_y, float(self.height - 2)))
            self._pulse("wall")

        if self.ball_x <= self.left_x + PADDLE_WIDTH:
            if self.left_y <= self.ball_y < self.left_y + self.paddle_h:
                self.ball_dir_x = 1
                self._pulse("paddle")
            elif self.ball_x <= 0:
                self.right_score += 1
                self._pulse("score")
                self._reset_ball()

        if self.ball_x >= self.right_x - PADDLE_WIDTH:
            if self.right_y <= self.ball_y < self.right_y + self.paddle_h:
                self.ball_dir_x = -1
                self._pulse("paddle")
            elif self.ball_x >= self.width - 1:
                self.left_score += 1
                self._pulse("score")
                self._reset_ball()

        if self.left_score >= WIN_SCORE:
            self._pulse("win")
            return "left"
        if self.right_score >= WIN_SCORE:
            self._pulse("win")
            return "right"
        return None

    def _reset_ball(self):
        self.ball_x = float(self.width // 2)
        self.ball_y = float(self.height // 2)
        self.ball_dir_x = -self.ball_dir_x
        self.ball_dir_y = 1 if self.ball_dir_y > 0 else -1

    def to_dict(self):
        return {
            "ball_x": self.ball_x,
            "ball_y": self.ball_y,
            "left_y": self.left_y,
            "right_y": self.right_y,
            "paddle_h": self.paddle_h,
            "width": self.width,
            "height": self.height,
            "sound": self.sound,
        }


# ── Save / Load ─────────────────────────────────────
def save_game(data):
    try:
        os.makedirs(_SAVE_DIR, exist_ok=True)
        with open(_SAVE_PATH, "w") as f:
            json.dump(data, f)
    except:
        pass


def load_game():
    try:
        with open(_SAVE_PATH) as f:
            return json.load(f)
    except:
        return None


def clear_save():
    try:
        os.remove(_SAVE_PATH)
    except:
        pass


def has_save():
    return os.path.isfile(_SAVE_PATH)


# ── CPU AI ──────────────────────────────────────────
def cpu_inputs(game, difficulty, tick):
    if game.ball_dir_x < 0 and abs(game.ball_x - game.right_x) > 15:
        return []
    target = game.ball_y
    center = game.right_y + game.paddle_h / 2
    diff = target - center
    configs = {
        "easy": {"thresh": 3.0, "speed": 1, "jitter": 0.3},
        "medium": {"thresh": 1.5, "speed": 2, "jitter": 0.1},
        "hard": {"thresh": 0.5, "speed": 3, "jitter": 0.02},
    }
    cfg = configs.get(difficulty, configs["medium"])
    if random.random() < cfg["jitter"]:
        return []
    if abs(diff) < cfg["thresh"]:
        return []
    keys = []
    if diff > 0:
        for _ in range(cfg["speed"]):
            keys.append("down")
    else:
        for _ in range(cfg["speed"]):
            keys.append("up")
    return keys


# ── Render ──────────────────────────────────────────
def render(stdscr, state, left_score, right_score, winner=None, side=None, info=None, chat_msgs=None, chat_input=None, pname="", opponent=""):
    stdscr.clear()
    w = state["width"]
    h = state["height"]
    mid_x = w // 2

    ball_x = int(state["ball_x"])
    ball_y = int(state["ball_y"])
    left_y = int(state["left_y"])
    right_y = int(state["right_y"])
    paddle_h = int(state["paddle_h"])

    for y in range(1, h - 1):
        if y % 2 == 0:
            try:
                stdscr.addch(y, mid_x, ':', curses.color_pair(3))
            except:
                pass

    text = f"{left_score}   {right_score}"
    try:
        stdscr.addstr(1, mid_x - len(text) // 2, text,
                      curses.color_pair(1) | curses.A_BOLD)
    except:
        pass

    for i in range(paddle_h):
        if 0 < left_y + i < h - 1:
            try:
                stdscr.addch(left_y + i, 2, '|', curses.color_pair(2))
            except:
                pass
        if 0 < right_y + i < h - 1:
            try:
                stdscr.addch(right_y + i, w - 3, '|', curses.color_pair(1))
            except:
                pass

    if 0 < ball_y < h - 1 and 0 < ball_x < w - 1:
        try:
            stdscr.addch(ball_y, ball_x, 'O', curses.color_pair(3))
        except:
            pass

    if winner:
        msg = f"{winner.capitalize()} wins! ({left_score}-{right_score})"
        try:
            stdscr.addstr(h // 2, w // 2 - len(msg) // 2, msg,
                          curses.color_pair(1) | curses.A_BOLD)
        except:
            pass
        try:
            stdscr.addstr(h // 2 + 1, w // 2 - 12,
                          "Press any key to continue", curses.color_pair(3))
        except:
            pass

    if side:
        lbl = pname if pname else side
        try:
            stdscr.addstr(0, 2, f"<{lbl}>", curses.color_pair(1))
        except:
            pass
        if opponent:
            try:
                stdscr.addstr(0, w - len(opponent) - 4, f"<{opponent}>",
                              curses.color_pair(2))
            except:
                pass

    if info:
        try:
            stdscr.addstr(h // 2 - 2, w // 2 - len(info) // 2, info,
                          curses.color_pair(3))
        except:
            pass

    if chat_msgs:
        y = h - 4
        for frm, txt in chat_msgs[-4:]:
            if y < 0:
                break
            try:
                line = f"<{frm}> {txt}"
                if len(line) >= w:
                    line = line[:w - 1]
                stdscr.addstr(y, 0, line, curses.color_pair(3))
            except:
                pass
            y += 1

    if chat_input is not None:
        try:
            line = f"/{chat_input}"
            if len(line) >= w:
                line = line[:w - 1]
            stdscr.addstr(h - 1, 0, line, curses.color_pair(1))
        except:
            pass

    stdscr.refresh()


# ── Sounds ─────────────────────────────────────────
def beep(event="paddle"):
    try:
        sys.stdout.write("\a")
        sys.stdout.flush()
        if event == "win":
            time.sleep(0.15)
            sys.stdout.write("\a")
            sys.stdout.flush()
            time.sleep(0.15)
            sys.stdout.write("\a")
            sys.stdout.flush()
        elif event == "score":
            time.sleep(0.08)
            sys.stdout.write("\a")
            sys.stdout.flush()
    except:
        pass


# ── Singleplayer ───────────────────────────────────
def play_singleplayer(stdscr):
    sh, sw = stdscr.getmaxyx()
    game = GameState(sw, sh)
    stdscr.nodelay(1)

    while True:
        sh, sw = stdscr.getmaxyx()
        game.width = sw
        game.height = sh
        game.right_x = sw - 3
        game.paddle_h = max(4, sh // 6)

        key = stdscr.getch()
        lu = key in (ord('w'), ord('W'))
        ld = key in (ord('s'), ord('S'))
        ru = key == curses.KEY_UP
        rd = key == curses.KEY_DOWN

        if key in (ord('q'), ord('Q')):
            break

        winner = game.update(lu, ld, ru, rd)
        if game.sound:
            beep(game.sound)
        render(stdscr, game.to_dict(), game.left_score, game.right_score, winner)

        if winner:
            stdscr.nodelay(0)
            stdscr.getch()
            break

        time.sleep(TICK)


# ── CPU Game ────────────────────────────────────────
def play_vs_cpu(stdscr, difficulty):
    sh, sw = stdscr.getmaxyx()
    game = GameState(sw, sh)
    stdscr.nodelay(1)
    saved = load_game()
    if saved and saved.get("mode") == "cpu" and saved.get("difficulty") == difficulty:
        game.left_score = saved.get("left_score", 0)
        game.right_score = saved.get("right_score", 0)
        game.left_y = saved.get("left_y", game.left_y)
        game.right_y = saved.get("right_y", game.right_y)
        game.ball_x = saved.get("ball_x", game.ball_x)
        game.ball_y = saved.get("ball_y", game.ball_y)
        game.ball_dir_x = saved.get("ball_dir_x", game.ball_dir_x)
        game.ball_dir_y = saved.get("ball_dir_y", game.ball_dir_y)

    tick = 0
    while True:
        sh, sw = stdscr.getmaxyx()
        game.width = sw
        game.height = sh
        game.right_x = sw - 3
        game.paddle_h = max(4, sh // 6)

        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            save_game({
                "mode": "cpu", "difficulty": difficulty,
                "left_score": game.left_score, "right_score": game.right_score,
                "left_y": game.left_y, "right_y": game.right_y,
                "ball_x": game.ball_x, "ball_y": game.ball_y,
                "ball_dir_x": game.ball_dir_x, "ball_dir_y": game.ball_dir_y,
                "width": game.width, "height": game.height,
            })
            break

        if key == ord('s') or key == ord('S'):
            sh, sw = stdscr.getmaxyx()
            stdscr.nodelay(0)
            clear_save()
            stdscr.addstr(sh // 2, sw // 2 - 10, "Progress saved.")
            stdscr.addstr(sh // 2 + 1, sw // 2 - 14, "Press any key to continue.")
            limit_msg = None
            stdscr.refresh()
            stdscr.getch()
            stdscr.nodelay(1)
            continue

        lu = key in (ord('w'), ord('W'))
        ld = key in (ord('s'), ord('S'))
        cpu = cpu_inputs(game, difficulty, tick)
        ru = "up" in cpu
        rd = "down" in cpu

        winner = game.update(lu, ld, ru, rd)
        if game.sound:
            beep(game.sound)
        render(stdscr, game.to_dict(), game.left_score, game.right_score, winner)
        tick += 1

        if winner:
            stdscr.nodelay(0)
            clear_save()
            stdscr.getch()
            break

        time.sleep(TICK)


# ── Networking ─────────────────────────────────────
def send_msg(conn, msg):
    try:
        conn.sendall((json.dumps(msg) + "\n").encode())
    except:
        pass


def recv_msg(conn):
    buf = b""
    while True:
        try:
            c = conn.recv(1)
        except:
            return None
        if not c:
            return None
        if c == b"\n":
            try:
                return json.loads(buf.decode())
            except:
                return None
        buf += c


# ── Discovery ─────────────────────────────────────
def _discovery_broadcaster(udp_port, tcp_port, name, stop):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.settimeout(1)
    while not stop.is_set():
        try:
            payload = json.dumps({
                "type": "pong_announce",
                "port": tcp_port,
                "name": name,
            })
            s.sendto(payload.encode(), ("255.255.255.255", udp_port))
        except:
            pass
        stop.wait(DISCOVERY_INTERVAL)
    s.close()


def start_discovery(tcp_port, name="Pong Server"):
    stop = threading.Event()
    t = threading.Thread(target=_discovery_broadcaster,
                         args=(DISCOVERY_PORT, tcp_port, name, stop), daemon=True)
    t.start()
    return stop


# ── Web Dashboard ──────────────────────────────────
def _start_web_dashboard(rooms, rooms_lock, events, events_lock, start_time,
                         name, ip, port, web_port, stop_event):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self._html()
            elif self.path == '/status':
                self._json()
            else:
                self.send_error(404)

        def _html(self):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())

        def _json(self):
            with rooms_lock:
                rlist = [r.info() for r in rooms.values()]
            with events_lock:
                elist = [{"time": e[0], "msg": e[1]} for e in events[-30:]]
            data = {
                "name": name, "ip": ip, "port": port, "web_port": web_port,
                "uptime": int(time.time() - start_time),
                "total_players": sum(r["players"] for r in rlist),
                "rooms": rlist, "events": elist,
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        def log_message(self, *a):
            pass

    httpd = HTTPServer(("", web_port), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    stop_event.wait()
    httpd.shutdown()


# ── Server ─────────────────────────────────────────
def _make_server_sock(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(1)
    try:
        sock.bind((host, port))
    except OSError:
        return None
    sock.listen(10)
    return sock


class Player:
    def __init__(self, conn, addr, name=""):
        self.conn = conn
        self.addr = addr
        self.name = name or f"Player_{addr[0].rsplit('.',1)[-1]}"
        self.side = None

    def send(self, msg):
        send_msg(self.conn, msg)


class Room:
    def __init__(self, name):
        self.name = name
        self.players = []
        self.lock = threading.Lock()
        self.game = GameState()
        self.inputs = {"left": set(), "right": set()}
        self.chat_history = []
        self.alive = True
        self.created_at = time.time()
        self.playing = False
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def info(self):
        with self.lock:
            return {
                "name": self.name,
                "players": len(self.players),
                "full": len(self.players) >= 2,
                "player_names": [p.name for p in self.players],
                "player_sides": {p.name: p.side for p in self.players},
                "playing": self.playing,
                "left_score": self.game.left_score,
                "right_score": self.game.right_score,
                "uptime": int(time.time() - self.created_at),
            }

    def add(self, player):
        with self.lock:
            side = "left" if len(self.players) == 0 else "right"
            player.side = side
            self.players.append(player)
        other = [p.name for p in self.players if p != player]
        player.send({"type": "assign", "player": side, "name": player.name,
                      "opponent": other[0] if other else ""})
        if self.chat_history:
            player.send({"type": "chat_history", "messages": self.chat_history[-100:]})

    def remove(self, player):
        with self.lock:
            if player in self.players:
                self.players.remove(player)
            self.inputs.get(player.side, set()).clear()

    def handle_input(self, player, msg):
        with self.lock:
            self.inputs[player.side] = set(msg.get("keys", []))

    def handle_chat(self, player, msg):
        lbl = player.name if player.name else player.side
        text = _filter_chat(msg.get("text", ""))
        entry = {"from": lbl, "text": text}
        self.chat_history.append(entry)
        if len(self.chat_history) > 100:
            self.chat_history.pop(0)
        relay = {"type": "chat", "from": entry["from"], "text": entry["text"]}
        with self.lock:
            for p in self.players:
                p.send(relay)

    def _loop(self):
        while self.alive:
            time.sleep(TICK)
            with self.lock:
                was_playing = self.playing
                self.playing = len(self.players) >= 2

                if not self.playing:
                    if was_playing:
                        self.game.reset()
                        self.inputs["left"].clear()
                        self.inputs["right"].clear()
                    continue

                winner = self.game.update(
                    "w" in self.inputs.get("left", set()),
                    "s" in self.inputs.get("left", set()),
                    "up" in self.inputs.get("right", set()),
                    "down" in self.inputs.get("right", set()),
                )

                state = self.game.to_dict()
                state["left_score"] = self.game.left_score
                state["right_score"] = self.game.right_score

                if winner:
                    state["type"] = "win"
                    state["winner"] = winner
                    for p in self.players:
                        p.send(state)
                    time.sleep(2)
                    self.game.reset()
                    self.inputs["left"].clear()
                    self.inputs["right"].clear()
                else:
                    state["type"] = "state"
                    for p in self.players:
                        p.send(state)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def _run_server(sock, rooms, rooms_lock, events, events_lock, stop_event):
    while not stop_event.is_set():
        try:
            conn, addr = sock.accept()
        except socket.timeout:
            continue
        except:
            break
        threading.Thread(target=_handle_client,
                         args=(conn, addr, rooms, rooms_lock, events, events_lock),
                         daemon=True).start()


def start_server(host, port):
    sock = _make_server_sock(host, port)
    if sock is None:
        print(f"Cannot bind to {host}:{port}")
        sys.exit(1)

    ip = get_local_ip()
    rooms = {}
    rooms_lock = threading.Lock()
    events = []
    events_lock = threading.Lock()
    stop_event = threading.Event()

    print(f"Pong server running on {host}:{port}")
    print(f"Local IP: {ip}")
    print()
    print("Waiting for connections...")
    print("Press Ctrl+C to stop the server.")
    print()

    stop_disc = start_discovery(port, socket.gethostname())
    try:
        _run_server(sock, rooms, rooms_lock, events, events_lock, stop_event)
    except KeyboardInterrupt:
        pass
    stop_event.set()
    stop_disc.set()
    sock.close()


def _handle_client(conn, addr, rooms, rooms_lock, events, events_lock):
    player = None
    room = None

    def log(msg):
        t = time.strftime("%H:%M")
        with events_lock:
            events.append((t, msg))
            if len(events) > 100:
                events.pop(0)

    try:
        while True:
            msg = recv_msg(conn)
            if not msg:
                return

            t = msg.get("type")

            if t == "list_rooms":
                with rooms_lock:
                    rlist = [{"name": name, "players": len(r.players)}
                             for name, r in rooms.items()]
                send_msg(conn, {"type": "room_list", "rooms": rlist})

            elif t == "join":
                room_name = msg.get("room", "default")
                with rooms_lock:
                    if room_name not in rooms:
                        rooms[room_name] = Room(room_name)
                        log(f"Room '{room_name}' created")
                    room = rooms[room_name]

                if len(room.players) >= 2:
                    send_msg(conn, {"type": "error", "msg": "Room is full"})
                    continue

                pname = msg.get("player_name", "")
                player = Player(conn, addr, pname)
                room.add(player)
                log(f"{player.name} ({player.side}) joined '{room_name}'")
                break

            else:
                send_msg(conn, {"type": "error", "msg": f"Unknown: {t}"})

        while True:
            msg = recv_msg(conn)
            if msg is None:
                return
            t = msg.get("type")
            if t == "input":
                room.handle_input(player, msg)
            elif t == "chat":
                room.handle_chat(player, msg)

    finally:
        if room and player:
            was = player.side
            room.remove(player)
            log(f"{player.name} ({was}) left '{room.name}'")
        try:
            conn.close()
        except:
            pass


# ── Client Game Loop ──────────────────────────────
def game_loop(stdscr, sock):
    side = None
    state = None
    winner = None
    waiting = True
    buf = ""
    chat_log = []
    chat_mode = False
    chat_buf = ""
    pname = ""
    opponent = ""

    prev_sound = None

    def pump():
        nonlocal buf, state, winner, side, waiting, chat_log, pname, opponent, prev_sound
        while True:
            try:
                data = sock.recv(4096)
            except (BlockingIOError, socket.timeout):
                return
            if not data:
                raise ConnectionError("Server disconnected")
            buf += data.decode()
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                if not line.strip():
                    continue
                try:
                    msg = json.loads(line)
                except:
                    continue
                t = msg.get("type")
                if t == "assign":
                    side = msg["player"]
                    pname = msg.get("name", "")
                    opponent = msg.get("opponent", "")
                elif t == "state":
                    snd = msg.get("sound")
                    if snd and not prev_sound:
                        beep(snd)
                    prev_sound = snd
                    state = msg
                    winner = None
                    waiting = False
                elif t == "win":
                    state = msg
                    winner = msg.get("winner")
                    waiting = False
                elif t == "chat_history":
                    for entry in msg.get("messages", []):
                        chat_log.append((entry.get("from", "?"), entry.get("text", "")))
                    if len(chat_log) > 100:
                        chat_log[:] = chat_log[-100:]
                elif t == "chat":
                    frm = msg.get("from", "?")
                    txt = msg["text"]
                    chat_log.append((frm, txt))
                    if len(chat_log) > 100:
                        chat_log.pop(0)
                elif t == "error":
                    raise Exception(msg.get("msg", "Server error"))

    stdscr.nodelay(1)
    try:
        while True:
            pump()

            key = stdscr.getch()

            if chat_mode:
                if key == ord('\n'):
                    if chat_buf.strip():
                        send_msg(sock, {"type": "chat", "text": chat_buf})
                    chat_buf = ""
                    chat_mode = False
                    stdscr.nodelay(1)
                elif key in (27,):
                    chat_buf = ""
                    chat_mode = False
                    stdscr.nodelay(1)
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    chat_buf = chat_buf[:-1]
                elif 32 <= key <= 126:
                    chat_buf += chr(key)
                if state:
                    render(stdscr, state,
                           state.get("left_score", 0),
                           state.get("right_score", 0),
                           winner, side, chat_msgs=chat_log,
                           chat_input=chat_buf,
                           pname=pname, opponent=opponent)
                time.sleep(TICK)
                continue

            if key == ord('/'):
                chat_mode = True
                chat_buf = "/"
                stdscr.nodelay(0)
                continue

            if key in (ord('q'), ord('Q')):
                break

            keys = []
            if side == "left":
                if key in (ord('w'), ord('W')):
                    keys.append("w")
                if key in (ord('s'), ord('S')):
                    keys.append("s")
            elif side == "right":
                if key == curses.KEY_UP:
                    keys.append("up")
                if key == curses.KEY_DOWN:
                    keys.append("down")

            send_msg(sock, {"type": "input", "keys": keys})

            if state:
                info = "Waiting for opponent..." if waiting else None
                render(stdscr, state,
                       state.get("left_score", 0),
                       state.get("right_score", 0),
                       winner, side, info,
                       chat_msgs=chat_log,
                       pname=pname, opponent=opponent)

            if winner:
                stdscr.nodelay(0)
                stdscr.getch()
                stdscr.nodelay(1)
                winner = None
                send_msg(sock, {"type": "input", "keys": []})

            time.sleep(TICK)

    except Exception as e:
        sh, sw = stdscr.getmaxyx()
        stdscr.clear()
        stdscr.addstr(sh // 2, sw // 2 - 15, f"Disconnected: {e}")
        stdscr.refresh()
        stdscr.nodelay(0)
        stdscr.getch()


def play_client(stdscr, host, port):
    name = input_dialog(stdscr, " Your Name ", "Name:", default="")
    if name is None:
        return
    name = name.strip() or f"Player_{random.randint(100, 999)}"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    try:
        sock.connect((host, port))
    except Exception as e:
        sh, sw = stdscr.getmaxyx()
        stdscr.addstr(sh // 2, sw // 2 - 12, f"Could not connect to {host}:{port}")
        stdscr.addstr(sh // 2 + 1, sw // 2 - 12, str(e))
        stdscr.refresh()
        stdscr.getch()
        return

    send_msg(sock, {"type": "list_rooms"})
    resp = recv_msg(sock)
    if not resp or resp.get("type") != "room_list":
        sh, sw = stdscr.getmaxyx()
        stdscr.addstr(sh // 2, sw // 2 - 15, "Failed to get room list")
        stdscr.refresh()
        stdscr.getch()
        sock.close()
        return

    room_name = show_room_selector(stdscr, host, resp.get("rooms", []))
    if room_name is None:
        sock.close()
        return

    sock.setblocking(0)
    send_msg(sock, {"type": "join", "room": room_name, "player_name": name})
    game_loop(stdscr, sock)
    try:
        sock.close()
    except:
        pass


# ── Terminal UI Menus ──────────────────────────────
def draw_menu(stdscr, title, items, selected):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    try:
        stdscr.addstr(1, w // 2 - len(title) // 2, title,
                      curses.color_pair(1) | curses.A_BOLD)
    except:
        pass

    for i, item in enumerate(items):
        y = 3 + i
        if y >= h - 2:
            break
        marker = " >" if i == selected else "  "
        sub = " >" if isinstance(item, list) else "   "
        label = item[0] if isinstance(item, list) else item
        pair = curses.color_pair(1) if i == selected else curses.color_pair(3)
        try:
            stdscr.addstr(y, w // 2 - 15, f"{marker}  {label}{sub}", pair)
        except:
            pass

    try:
        stdscr.addstr(h - 2, w // 2 - 20,
                      "arrows  enter select  q back",
                      curses.color_pair(3))
    except:
        pass

    try:
        diag = _DIAG
        if len(diag) >= w:
            diag = "..." + diag[-(w - 3):]
        stdscr.addstr(h - 1, w // 2 - len(diag) // 2, diag,
                      curses.color_pair(3))
    except:
        pass

    stdscr.refresh()


def menu_loop(stdscr, title, items):
    selected = 0
    while True:
        draw_menu(stdscr, title, items, selected)
        key = stdscr.getch()
        if key == -1:
            return -2
        if key in (ord('q'), ord('Q'), 27):
            return -1
        elif key == curses.KEY_UP:
            selected = (selected - 1) % len(items)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(items)
        elif key in (ord('\n'), ord(' ')):
            return selected


def show_room_selector(stdscr, host, rooms):
    curses.curs_set(0)
    stdscr.keypad(1)

    entries = [(r["name"], r["players"] >= 2) for r in rooms]
    templates = ROOM_TEMPLATES[:]
    total = len(entries) + len(templates) + 1
    sel = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        title = f" Pong — Rooms at {host} "
        try:
            stdscr.addstr(1, w // 2 - len(title) // 2, title,
                          curses.color_pair(1) | curses.A_BOLD)
        except:
            pass

        y = 3

        try:
            stdscr.addstr(y, w // 2 - 12, "Active rooms:",
                          curses.color_pair(3))
        except:
            pass
        y += 1

        for idx, (name, full) in enumerate(entries):
            marker = " >" if sel == idx and not full else "  "
            status = "FULL" if full else "open"
            pair = curses.color_pair(1) if sel == idx and not full else curses.color_pair(3)
            try:
                stdscr.addstr(y, w // 2 - 12, f"{marker}  {name}  ({status})", pair)
            except:
                pass
            y += 1

        y += 1
        base = len(entries) + 1

        try:
            stdscr.addstr(y, w // 2 - 12, "Templates:",
                          curses.color_pair(3))
        except:
            pass
        y += 1

        for idx, name in enumerate(templates):
            i = base + idx
            marker = " >" if sel == i else "  "
            pair = curses.color_pair(1) if sel == i else curses.color_pair(3)
            try:
                stdscr.addstr(y, w // 2 - 12, f"{marker}  {name}", pair)
            except:
                pass
            y += 1

        y += 1
        new_idx = base + len(templates)

        marker = " >" if sel == new_idx else "  "
        try:
            stdscr.addstr(y, w // 2 - 12, f"{marker}  [New Game]",
                          curses.color_pair(1) if sel == new_idx else curses.color_pair(3))
        except:
            pass

        try:
            stdscr.addstr(h - 2, w // 2 - 20,
                          "arrows   enter select   q back",
                          curses.color_pair(3))
        except:
            pass

        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord('q'), ord('Q'), 27):
            return None
        elif key == curses.KEY_UP:
            sel = (sel - 1) % total
        elif key == curses.KEY_DOWN:
            sel = (sel + 1) % total
        elif key in (ord('\n'), ord(' ')):
            if sel < len(entries):
                name, full = entries[sel]
                if full:
                    continue
                return name
            elif sel < base + len(templates):
                return templates[sel - base]
            else:
                return f"room_{random.randint(1000, 9999)}"


def input_dialog(stdscr, title, prompt, default=""):
    curses.curs_set(1)
    stdscr.nodelay(0)
    value = default

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        try:
            stdscr.addstr(1, w // 2 - len(title) // 2, title,
                          curses.color_pair(1) | curses.A_BOLD)
        except:
            pass

        try:
            stdscr.addstr(3, w // 2 - 15, f"{prompt} {value}")
        except:
            pass

        try:
            stdscr.addstr(h - 2, w // 2 - 20,
                          "enter confirm   esc back",
                          curses.color_pair(3))
        except:
            pass

        try:
            stdscr.move(3, w // 2 - 15 + len(prompt) + 1 + len(value))
        except:
            pass

        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord('\n'),):
            curses.curs_set(0)
            return value
        elif key in (27,):
            curses.curs_set(0)
            return None
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            value = value[:-1]
        elif 32 <= key <= 126:
            value += chr(key)


def show_server_screen(stdscr):
    curses.curs_set(0)
    stdscr.clear()

    port = DEFAULT_PORT
    port_str = str(port)
    sname = socket.gethostname()
    web_port = 8080
    web_str = str(web_port)
    editing = None  # "port", "name", "web", None

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()

        try:
            stdscr.addstr(1, w // 2 - 10, " Pong — Host Server ",
                          curses.color_pair(1) | curses.A_BOLD)
        except:
            pass

        ip = get_local_ip()
        label = sname if sname else "(unnamed)"
        lines = [
            f"IP:  {ip}",
            f"Port: {port_str}",
            f"Name: {label}",
            f"Web port: {web_str}",
            "",
            "Others join by selecting Join Server",
            f"and entering the IP above.",
            "",
            f"Web dashboard: http://{ip}:{web_str}",
        ]
        for i, line in enumerate(lines):
            try:
                stdscr.addstr(3 + i, w // 2 - 15, line, curses.color_pair(3))
            except:
                pass

        try:
            stdscr.addstr(h - 2, w // 2 - 22,
                          "s  start   p  port   n  name   w  web port   q  back",
                          curses.color_pair(3))
        except:
            pass

        stdscr.refresh()

        key = stdscr.getch()
        if key == ord('q') or key == ord('Q'):
            return None
        elif key == ord('s') or key == ord('S'):
            return {"port": port, "name": sname if sname else "Pong Server",
                    "web_port": web_port}
        elif key == ord('p') or key == ord('P'):
            editing = "port"
        elif key == ord('n') or key == ord('N'):
            editing = "name"
        elif key == ord('w') or key == ord('W'):
            editing = "web"

        if editing:
            val = port_str if editing == "port" else (sname if editing == "name" else web_str)
            title = {"port": "Game Port", "name": "Server Name", "web": "Web Dashboard Port"}[editing]
            prompt = {"port": "Port:", "name": "Name:", "web": "Web Port:"}[editing]
            curses.curs_set(1)
            while True:
                h, w = stdscr.getmaxyx()
                stdscr.clear()
                try:
                    stdscr.addstr(1, w // 2 - len(title) // 2, title,
                                  curses.color_pair(1) | curses.A_BOLD)
                except:
                    pass
                try:
                    stdscr.addstr(3, w // 2 - 10, f"{prompt} {val}")
                except:
                    pass
                try:
                    stdscr.move(3, w // 2 - 10 + len(prompt) + 1 + len(val))
                except:
                    pass
                try:
                    stdscr.addstr(h - 2, w // 2 - 20,
                                  "enter confirm   esc back",
                                  curses.color_pair(3))
                except:
                    pass
                stdscr.refresh()
                k = stdscr.getch()
                if k == ord('\n'):
                    if editing == "port" and val.isdigit() and 1 <= int(val) <= 65535:
                        port_str = val
                        port = int(val)
                    elif editing == "name":
                        sname = val
                    elif editing == "web" and val.isdigit() and 1 <= int(val) <= 65535:
                        web_str = val
                        web_port = int(val)
                    break
                elif k in (27,):
                    break
                elif k in (curses.KEY_BACKSPACE, 127, 8):
                    val = val[:-1]
                elif 32 <= k <= 126:
                    val += chr(k)
            curses.curs_set(0)
            stdscr.nodelay(1)
            editing = None


def show_how_to_play(stdscr):
    stdscr.nodelay(0)
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    lines = [
        (1, "How to Play", curses.color_pair(1) | curses.A_BOLD),
        (2, "", 0),
        (3, "Controls", curses.A_BOLD),
        (4, "  Left paddle:  W / S", curses.color_pair(3)),
        (5, "  Right paddle: Up Arrow / Down Arrow", curses.color_pair(3)),
        (6, "  Quit:         Q", curses.color_pair(3)),
        (7, "", 0),
        (8, "Multiplayer (LAN)", curses.A_BOLD),
        (9, "  Left player (host):  W / S", curses.color_pair(3)),
        (10, "  Right player (join): Up Arrow / Down Arrow", curses.color_pair(3)),
        (11, "", 0),
        (12, "Rules", curses.A_BOLD),
        (13, "  First to 5 points wins.", curses.color_pair(3)),
        (14, "", 0),
        (15, "Press any key to return.", curses.color_pair(3)),
    ]
    for y, text, attr in lines:
        try:
            stdscr.addstr(y, w // 2 - 20, text, attr)
        except:
            pass

    stdscr.refresh()
    stdscr.getch()


def server_browser(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    discovered = []
    lock = threading.Lock()

    def listener():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(1)
        try:
            s.bind(("", DISCOVERY_PORT))
        except:
            return
        while True:
            try:
                data, addr = s.recvfrom(1024)
                msg = json.loads(data.decode())
                if msg.get("type") == "pong_announce":
                    entry = (addr[0], msg.get("port", DEFAULT_PORT), msg.get("name", "?"))
                    with lock:
                        for e in discovered:
                            if e[0] == entry[0] and e[1] == entry[1]:
                                break
                        else:
                            discovered.append(entry)
                            if len(discovered) > 50:
                                discovered.pop(0)
            except:
                pass
    t = threading.Thread(target=listener, daemon=True)
    t.start()

    sel = 0
    last_count = -1
    dirty = True

    while True:
        with lock:
            count = len(discovered)
        changed = count != last_count
        if changed:
            sel = min(sel, count)
            last_count = count
            dirty = True

        key = stdscr.getch()
        if key != -1:
            dirty = True
            if key in (ord('q'), ord('Q'), 27):
                return None
            elif key == curses.KEY_UP:
                sel = max(0, sel - 1)
            elif key == curses.KEY_DOWN:
                sel = min(count + 1, sel + 1)
            elif key == ord('r') or key == ord('R'):
                with lock:
                    discovered.clear()
                sel = 0
            elif key in (ord('\n'), ord(' ')):
                if sel < count:
                    with lock:
                        ip, p, _ = discovered[sel]
                    return ip, p
                elif sel == count:
                    ip = input_dialog(stdscr, " Join Server ", "Server IP:", "")
                    if ip:
                        return ip, DEFAULT_PORT
                else:
                    return None

        if not dirty:
            time.sleep(0.05)
            continue
        dirty = False

        h, w = stdscr.getmaxyx()
        stdscr.clear()

        title = " Server Browser "
        try:
            stdscr.addstr(1, w // 2 - len(title) // 2, title,
                          curses.color_pair(1) | curses.A_BOLD)
        except:
            pass

        try:
            status = f" Scanning... ({count} server(s) found)" if count > 0 else " Scanning... (no servers yet)"
            stdscr.addstr(3, w // 2 - 20, status, curses.color_pair(3))
        except:
            pass

        y = 5
        with lock:
            for idx, (ip, p, name) in enumerate(discovered):
                if y >= h - 4:
                    break
                marker = " >" if sel == idx else "  "
                pair = curses.color_pair(1) if sel == idx else curses.color_pair(3)
                try:
                    stdscr.addstr(y, w // 2 - 20, f"{marker}  {ip}:{p}  ({name})", pair)
                except:
                    pass
                y += 1

        y += 1
        man_idx = count
        marker = " >" if sel == man_idx else "  "
        try:
            stdscr.addstr(y, w // 2 - 20, f"{marker}  [Enter IP Manually]",
                          curses.color_pair(1) if sel == man_idx else curses.color_pair(3))
        except:
            pass

        y += 1
        back_idx = count + 1
        marker = " >" if sel == back_idx else "  "
        try:
            stdscr.addstr(y, w // 2 - 20, f"{marker}  [Back]",
                          curses.color_pair(1) if sel == back_idx else curses.color_pair(3))
        except:
            pass

        try:
            stdscr.addstr(h - 2, w // 2 - 20,
                          "arrows  enter select  r rescan  q back",
                          curses.color_pair(3))
        except:
            pass

        try:
            diag = _DIAG
            if len(diag) >= w:
                diag = "..." + diag[-(w - 3):]
            stdscr.addstr(h - 1, w // 2 - len(diag) // 2, diag, curses.color_pair(3))
        except:
            pass

        stdscr.refresh()
        time.sleep(0.05)


# ── Server Management Screen ──────────────────────
def server_management_screen(stdscr, config):
    port = config["port"]
    name = config.get("name", "Pong Server")
    web_port = config.get("web_port", 8080)

    sock = _make_server_sock("0.0.0.0", port)
    if sock is None:
        sh, sw = stdscr.getmaxyx()
        stdscr.addstr(sh // 2, sw // 2 - 12, f"Cannot bind to port {port}")
        stdscr.getch()
        return

    ip = get_local_ip()
    rooms = {}
    rooms_lock = threading.Lock()
    events = []
    events_lock = threading.Lock()
    stop_event = threading.Event()
    start_time = time.time()

    stop_disc = start_discovery(port, name)

    t = threading.Thread(target=_run_server,
                         args=(sock, rooms, rooms_lock, events, events_lock, stop_event),
                         daemon=True)
    t.start()

    threading.Thread(target=_start_web_dashboard,
                     args=(rooms, rooms_lock, events, events_lock, start_time,
                           name, ip, port, web_port, stop_event),
                     daemon=True).start()

    curses.curs_set(0)
    stdscr.nodelay(1)
    sel_room = 0
    sel_player = -1
    dirty = True

    while not stop_event.is_set():
        with rooms_lock:
            rlist = list(rooms.items())

        key = stdscr.getch()
        if key != -1:
            dirty = True
            if key == ord('q') or key == ord('Q'):
                break
            elif key == ord('j') or key == ord('J'):
                sock.setblocking(0)
                try:
                    play_client(stdscr, "127.0.0.1", port)
                except:
                    pass
                sock.setblocking(0)
                stdscr.nodelay(1)
                curses.curs_set(0)
                dirty = True
            elif key == ord('k') or key == ord('K'):
                if sel_player >= 0 and rlist:
                    rn, rm = rlist[sel_room]
                    with rooms_lock:
                        ps = rm.players[:]
                    if 0 <= sel_player < len(ps):
                        target = ps[sel_player]
                        with rooms_lock:
                            log(f"{target.name} kicked by host")
                            try:
                                target.conn.close()
                            except:
                                pass
                    sel_player = -1
            elif key == curses.KEY_UP:
                if sel_player >= 0:
                    with rooms_lock:
                        pcount = len(rlist[sel_room][1].players) if rlist else 0
                    sel_player = (sel_player - 1) % max(1, pcount)
                elif rlist:
                    sel_room = (sel_room - 1) % len(rlist)
            elif key == curses.KEY_DOWN:
                if sel_player >= 0:
                    with rooms_lock:
                        pcount = len(rlist[sel_room][1].players) if rlist else 0
                    sel_player = (sel_player + 1) % max(1, pcount)
                elif rlist:
                    sel_room = (sel_room + 1) % len(rlist)
            elif key in (ord('\n'), ord(' ')):
                if rlist:
                    if sel_player >= 0:
                        sel_player = -1
                    else:
                        sel_player = 0
            elif key == 27:
                if sel_player >= 0:
                    sel_player = -1
            elif key == ord('r') or key == ord('R'):
                pass

            if rlist and sel_player >= 0:
                rn, rm = rlist[sel_room]
                with rooms_lock:
                    pcount = len(rm.players)
                sel_player = min(sel_player, max(0, pcount - 1)) if pcount > 0 else -1

        if not dirty:
            time.sleep(0.05)
            continue
        dirty = False

        h, w = stdscr.getmaxyx()
        stdscr.clear()

        y = 1
        title = f" Pong — Server: {name} "
        try:
            stdscr.addstr(y, w // 2 - len(title) // 2, title,
                          curses.color_pair(1) | curses.A_BOLD)
        except:
            pass
        y += 2

        upt = int(time.time() - start_time)
        info = (f"IP: {ip}:{port}   "
                f"Web: http://{ip}:{web_port}   "
                f"Uptime: {upt // 3600}h {(upt % 3600) // 60}m {upt % 60}s")
        try:
            stdscr.addstr(y, w // 2 - len(info) // 2, info, curses.color_pair(3))
        except:
            pass
        y += 2

        try:
            stdscr.addstr(y, w // 2 - 15, "Active Rooms:", curses.A_BOLD)
        except:
            pass
        y += 1

        if not rlist:
            try:
                stdscr.addstr(y, w // 2 - 12, "(no rooms yet)", curses.color_pair(3))
            except:
                pass
            y += 1
            sel_room = 0
        else:
            sel_room = min(sel_room, len(rlist) - 1) if sel_room >= len(rlist) else sel_room
            for idx, (rn, rm) in enumerate(rlist):
                ri = rm.info()
                marker = " >" if idx == sel_room and sel_player < 0 else "  "
                players = ri["players"]
                pnames = ", ".join(ri["player_names"])
                status = f"{players}/2" + (" FULL" if ri["full"] else "")
                if ri["playing"]:
                    status += " PLAYING"
                score = ""
                if ri["playing"] or ri["left_score"] or ri["right_score"]:
                    score = f"  {ri['left_score']}-{ri['right_score']}"
                pair = curses.color_pair(1) if (idx == sel_room and sel_player < 0) else curses.color_pair(3)
                line = f"{marker}  {rn}  ({status}){score}"
                if pnames:
                    line += f"  [{pnames}]"
                try:
                    stdscr.addstr(y, w // 2 - 15, line[:w - 2], pair)
                except:
                    pass
                y += 1

                if idx == sel_room and sel_player >= 0:
                    with rooms_lock:
                        ps = rm.players[:]
                    for pi, p in enumerate(ps):
                        pm = " >" if pi == sel_player else "  "
                        pp = curses.color_pair(1) if pi == sel_player else curses.color_pair(3)
                        try:
                            stdscr.addstr(y, w // 2 - 11, f"{pm}  {p.name}  ({p.side})", pp)
                        except:
                            pass
                        y += 1

        y += 1
        with events_lock:
            recent = events[-max(0, h - y - 4):]

        try:
            stdscr.addstr(y, w // 2 - 15, "Recent Events:", curses.A_BOLD)
        except:
            pass
        y += 1
        for tstr, msg in recent[-max(0, h - y - 2):]:
            line = f"  [{tstr}] {msg}"
            try:
                stdscr.addstr(y, w // 2 - 15, line[:w - 2], curses.color_pair(3))
            except:
                pass
            y += 1

        hints = "j join  k kick  q stop"
        if sel_player >= 0:
            hints = "k kick player  esc back"
        try:
            stdscr.addstr(h - 2, w // 2 - len(hints) // 2, hints, curses.color_pair(3))
        except:
            pass

        try:
            diag = _DIAG
            if len(diag) >= w:
                diag = "..." + diag[-(w - 3):]
            stdscr.addstr(h - 1, w // 2 - len(diag) // 2, diag, curses.color_pair(3))
        except:
            pass

        stdscr.refresh()
        time.sleep(0.05)

    stop_event.set()
    stop_disc.set()
    sock.close()


def multiplayer_submenu(stdscr):
    while True:
        choice = menu_loop(stdscr, " Multiplayer ", ["Host Server", "Join Server"])

        if choice == 0:
            config = show_server_screen(stdscr)
            if config is not None:
                server_management_screen(stdscr, config)

        elif choice == 1:
            host = server_browser(stdscr)
            if host is not None:
                play_client(stdscr, host[0], host[1])

        else:
            break

    return False


# ── Main Menu ─────────────────────────────────────
def main_menu(stdscr):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.curs_set(0)
    stdscr.keypad(1)
    stdscr.timeout(5000)

    IDLE_SECS = 30
    idle = 0

    def rickroll():
        curses.def_prog_mode()
        curses.endwin()
        try:
            subprocess.call(["curl", "-s", "ASCII.live/can-you-hear-me"],
                            timeout=60)
        except:
            pass
        curses.reset_prog_mode()
        curses.doupdate()

    while True:
        choice = menu_loop(stdscr, " Pong ", [
            ["Play", "Singleplayer"],
            "How to Play",
            "Quit",
        ])

        if choice == -2:
            idle += 5
            if idle >= IDLE_SECS:
                rickroll()
                idle = 0
            continue

        idle = 0

        if choice == 0:
            sub = menu_loop(stdscr, " Play ", ["Singleplayer", "Multiplayer"])
            if sub == 0:
                sp_items = ["New Game"]
                if has_save():
                    sp_items.append(["Load Game", "continue saved"])
                sp = menu_loop(stdscr, " Singleplayer ", sp_items)
                if sp == 0:
                    ng = menu_loop(stdscr, " New Game ", [
                        ["Player vs CPU", "Easy / Medium / Hard"],
                        ["Player vs Player", "local 2-player"],
                    ])
                    if ng == 0:
                        diff = menu_loop(stdscr, " CPU Difficulty ",
                                         ["Easy", "Medium", "Hard"])
                        if diff >= 0:
                            play_vs_cpu(stdscr, ["easy", "medium", "hard"][diff])
                    elif ng == 1:
                        play_singleplayer(stdscr)
                elif sp == 1 and has_save():
                    saved = load_game()
                    diff = saved.get("difficulty", "medium") if saved else "medium"
                    play_vs_cpu(stdscr, diff)
            elif sub == 1:
                if multiplayer_submenu(stdscr):
                    return

        elif choice == 1:
            show_how_to_play(stdscr)

        else:
            break


def main():
    os.environ.setdefault("TERM", "xterm-256color")
    try:
        curses.wrapper(main_menu)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
