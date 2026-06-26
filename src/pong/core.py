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
import sys
import threading
import time
import random


# ── Globals ─────────────────────────────────────────
_DIAG = (f"{platform.system()} {platform.release()}"
         f" | {platform.machine()}"
         f" | Py {platform.python_version()}")

# ── Constants ───────────────────────────────────────
PADDLE_WIDTH = 1
BALL_SPEED = 1
WIN_SCORE = 5
DEFAULT_PORT = 9999
TICK = 0.04


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

    def update(self, left_up, left_down, right_up, right_down):
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

        if self.ball_x <= self.left_x + PADDLE_WIDTH:
            if self.left_y <= self.ball_y < self.left_y + self.paddle_h:
                self.ball_dir_x = 1
            elif self.ball_x <= 0:
                self.right_score += 1
                self._reset_ball()

        if self.ball_x >= self.right_x - PADDLE_WIDTH:
            if self.right_y <= self.ball_y < self.right_y + self.paddle_h:
                self.ball_dir_x = -1
            elif self.ball_x >= self.width - 1:
                self.left_score += 1
                self._reset_ball()

        if self.left_score >= WIN_SCORE:
            return "left"
        if self.right_score >= WIN_SCORE:
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
        }


# ── Render ──────────────────────────────────────────
def render(stdscr, state, left_score, right_score, winner=None, side=None, info=None):
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
        try:
            stdscr.addstr(h - 1, 2, f"You: {side}", curses.color_pair(3))
        except:
            pass

    if info:
        try:
            stdscr.addstr(h // 2 - 2, w // 2 - len(info) // 2, info,
                          curses.color_pair(3))
        except:
            pass

    stdscr.refresh()


# ── Singleplayer ───────────────────────────────────
def play_singleplayer(stdscr):
    sh, sw = stdscr.getmaxyx()
    game = GameState(sw, sh)

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
        render(stdscr, game.to_dict(), game.left_score, game.right_score, winner)

        if winner:
            stdscr.nodelay(0)
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


# ── Server ─────────────────────────────────────────
class Player:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
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
        self.alive = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def add(self, player):
        with self.lock:
            side = "left" if len(self.players) == 0 else "right"
            player.side = side
            self.players.append(player)
        player.send({"type": "assign", "player": side})

    def remove(self, player):
        with self.lock:
            if player in self.players:
                self.players.remove(player)
            self.inputs.get(player.side, set()).clear()

    def handle_input(self, player, msg):
        with self.lock:
            self.inputs[player.side] = set(msg.get("keys", []))

    def _loop(self):
        while self.alive:
            time.sleep(TICK)
            with self.lock:
                if len(self.players) < 2:
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


def start_server(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(1)
    try:
        sock.bind((host, port))
    except OSError as e:
        print(f"Cannot bind to {host}:{port} — {e}")
        sys.exit(1)
    sock.listen(10)
    rooms = {}
    rooms_lock = threading.Lock()

    ip = get_local_ip()
    print(f"Pong server running on {host}:{port}")
    print(f"Local IP: {ip}")
    print(f"Join from another machine: python3 pong.py")
    print("(then select Join Server and enter the IP)")
    print()
    print("Waiting for connections...")
    print("Press Ctrl+C to stop the server.")

    while True:
        try:
            conn, addr = sock.accept()
        except socket.timeout:
            continue
        except:
            break
        threading.Thread(target=_handle_client, args=(conn, addr, rooms, rooms_lock), daemon=True).start()


def _handle_client(conn, addr, rooms, rooms_lock):
    player = None
    room = None

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
                    room = rooms[room_name]

                if len(room.players) >= 2:
                    send_msg(conn, {"type": "error", "msg": "Room is full"})
                    continue

                player = Player(conn, addr)
                room.add(player)
                break

            else:
                send_msg(conn, {"type": "error", "msg": f"Unknown: {t}"})

        while True:
            msg = recv_msg(conn)
            if msg is None:
                return
            if msg.get("type") == "input":
                room.handle_input(player, msg)

    finally:
        if room and player:
            room.remove(player)
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

    def pump():
        nonlocal buf, state, winner, side, waiting
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
                elif t == "state":
                    state = msg
                    winner = None
                    waiting = False
                elif t == "win":
                    state = msg
                    winner = msg.get("winner")
                    waiting = False
                elif t == "error":
                    raise Exception(msg.get("msg", "Server error"))

    stdscr.nodelay(1)
    try:
        while True:
            pump()

            key = stdscr.getch()
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
                       winner, side, info)

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
    send_msg(sock, {"type": "join", "room": room_name})
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
    selected = 0

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
        for idx, (name, full) in enumerate(entries):
            marker = " >" if idx == selected and not full else "  "
            status = "FULL" if full else "open"
            pair = curses.color_pair(1) if idx == selected and not full else curses.color_pair(3)
            try:
                stdscr.addstr(y, w // 2 - 12, f"{marker}  {name}  ({status})", pair)
            except:
                pass
            y += 1

        if y < h - 3:
            marker = " >" if selected == len(entries) else "  "
            try:
                stdscr.addstr(y, w // 2 - 12, f"{marker}  [New Game]",
                              curses.color_pair(1) if selected == len(entries) else curses.color_pair(3))
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
            selected = (selected - 1) % (len(entries) + 1)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % (len(entries) + 1)
        elif key in (ord('\n'), ord(' ')):
            if selected < len(entries):
                name, full = entries[selected]
                if full:
                    continue
                return name
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
            return value if value else None
        elif key in (27,):
            curses.curs_set(0)
            return None
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            value = value[:-1]
        elif 32 <= key <= 126:
            value += chr(key)


def show_server_screen(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    port = DEFAULT_PORT
    port_str = str(port)

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        try:
            stdscr.addstr(1, w // 2 - 10, " Pong — Host Server ",
                          curses.color_pair(1) | curses.A_BOLD)
        except:
            pass

        ip = get_local_ip()
        lines = [
            f"IP:  {ip}",
            f"Port: {port_str}",
            "",
            "Others join by selecting Join Server",
            f"and entering the IP above.",
        ]
        for i, line in enumerate(lines):
            try:
                stdscr.addstr(3 + i, w // 2 - 15, line, curses.color_pair(3))
            except:
                pass

        try:
            stdscr.addstr(h - 2, w // 2 - 18,
                          "s  start server   p  edit port   q  back",
                          curses.color_pair(3))
        except:
            pass

        stdscr.refresh()

        key = stdscr.getch()
        if key == ord('q') or key == ord('Q'):
            return None
        elif key == ord('s') or key == ord('S'):
            return port
        elif key == ord('p') or key == ord('P'):
            curses.curs_set(1)
            val = port_str
            while True:
                stdscr.clear()
                try:
                    stdscr.addstr(1, w // 2 - 10, "Edit Port",
                                  curses.color_pair(1) | curses.A_BOLD)
                except:
                    pass
                try:
                    stdscr.addstr(3, w // 2 - 10, f"Port: {val}")
                except:
                    pass
                try:
                    stdscr.move(3, w // 2 - 10 + 6 + len(val))
                except:
                    pass
                stdscr.refresh()
                k = stdscr.getch()
                if k == ord('\n'):
                    if val.isdigit() and 1 <= int(val) <= 65535:
                        port_str = val
                        port = int(val)
                    break
                elif k in (27,):
                    break
                elif k in (curses.KEY_BACKSPACE, 127, 8):
                    val = val[:-1]
                elif 48 <= k <= 57:
                    val += chr(k)
            curses.curs_set(0)
            stdscr.nodelay(1)


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


def multiplayer_submenu(stdscr):
    while True:
        choice = menu_loop(stdscr, " Multiplayer ", ["Host Server", "Join Server"])

        if choice == 0:
            result = show_server_screen(stdscr)
            if result is not None:
                curses.endwin()
                start_server("0.0.0.0", result)
                return True

        elif choice == 1:
            host = input_dialog(stdscr, " Join Server ",
                                "Server IP:", "")
            if host is not None:
                play_client(stdscr, host, DEFAULT_PORT)

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

    while True:
        choice = menu_loop(stdscr, " Pong ", [
            ["Play", "Singleplayer"],
            "How to Play",
            "Quit",
        ])

        if choice == 0:
            sub = menu_loop(stdscr, " Play ", ["Singleplayer", "Multiplayer"])
            if sub == 0:
                play_singleplayer(stdscr)
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
