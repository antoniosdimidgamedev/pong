# Pong

Classic Pong for the terminal. Player vs CPU with three difficulty levels, local two-player on one keyboard, or multiplayer over LAN with room-based matchmaking, in-game chat, a web dashboard, and automatic server discovery. No dependencies beyond Python 3.6+ and curses. Runs on Linux, macOS, and Termux.

## Features

- **Player vs CPU** — three difficulty levels (Easy, Medium, Hard) with adaptive AI that tracks the ball, reacts with human-like delay, and has configurable paddle speed and accuracy
- **Save / Load** — press `S` during a CPU game to save your progress to `~/.pong/save.json`; resume later from **Play > Singleplayer > Load Game**
- **Local two-player** — two players share one keyboard (W/S vs arrow keys)
- **LAN multiplayer** — built-in TCP server with automatic IP detection, UDP broadcast discovery, and a server browser
- **Room templates** — pick from 10 preset room names (Classic, Rally, Speed, Tournament, Practice, Sudden Death, Challenge, Arena, Grand Slam, Showdown) or create a new one
- **Web dashboard** — live HTTP dashboard showing server status, active rooms with scores and player names, and recent events; viewable from any browser on the LAN
- **Server management screen** — when hosting, a curses interface shows rooms, connected players, live scores, and a real-time event log; hosts can join their own games locally
- **Kick players** — from the host screen, press Enter on a room to see its players, navigate to a player, and press `k` to kick them
- **Custom player names** — prompted on join; displayed in-game, in chat, in the management screen, and in the web dashboard
- **Custom server names** — configure a name before starting; broadcast in UDP discovery and shown in the server browser
- **In-game chat** — press `/` to open chat input, type your message, press Enter to send, Esc to cancel
- **Chat history** — last 100 messages stored server-side and sent to late-joining players
- **Chat filter** — common profanity is automatically censored server-side before reaching other players
- **Terminal UI** — full curses interface with menus, IP input, a room selector, and a server browser with auto-discovery
- **Diagnostics** — OS, kernel, architecture, and Python version shown at the bottom of every menu
- **Portable** — pure Python, no pip installs, works wherever Python and curses do
- **No dependencies** — pure Python stdlib, no pip install required

## Quick start

```bash
git clone https://github.com/antoniosdimidgamedev/pong.git
cd pong
python3 pong.py
```



## How to play

### Menu

```
 Pong                         Play                              Singleplayer
  > Play                 >     Singleplayer >              >      New Game >
    How to Play                Multiplayer >                      Load Game      (if save exists)
    Quit                                                          Player vs CPU >
                                                                   Easy / Medium / Hard
                                                                  Player vs Player
```

Use arrow keys to navigate, Enter to select, Q or Esc to go back.

### Controls

| Mode | Player | Paddle up | Paddle down | Special | Quit |
|---|---|---|---|---|---|
| Two-player | Left (W/S) | `W` | `S` | — | `Q` |
| Two-player | Right (arrows) | `↑` | `↓` | — | `Q` |
| vs CPU | You (W/S) | `W` | `S` | `S` save | `Q` |
| Multiplayer | Left (W/S) | `W` | `S` | `/` chat | `Q` |
| Multiplayer | Right (arrows) | `↑` | `↓` | `/` chat | `Q` |

### Rules

First to 5 points wins. After a point the ball resets to center and launches toward the player who was scored on.

### Game screen

```
  <Alice>                   3-2                   <Bob>
   |                                              |
   |                     :                        |
   |                O    :                        |
   |                     :                        |
   |                     :                        |
   |                     :                    |
   |                     :                        |
   |                     :                        |
   |                     :                  |
   |                :                        |
   |                     :                        |
   |                                              |
   |                                              |
   1:  <Alice> won! (5-3)                   2:
   ____________________chat_______________________
   <left>  nice shot!
   <right> thanks!
```

The center line marks the court. `O` is the ball. `|` on each side are the paddles. The score is displayed at the top, player names at the corners, and recent chat messages at the bottom.

### Chat (Multiplayer only)

Press `/` to enter chat mode. The prompt appears at the bottom of the screen. Type your message and press Enter to send. Press Esc to cancel. Chat messages from both players are shown in the bottom few lines of the game screen. If you join a room with existing chat history, the last 100 messages are replayed to you.

### Save / Load (CPU only)

Press `S` during a CPU game to save your progress. The current score, paddle positions, ball state, and difficulty are written to `~/.pong/save.json`. On the next launch, select **Play > Singleplayer > Load Game** to resume. The save is erased automatically when the game ends (someone wins) or can be discarded by starting a fresh game.

## Player vs CPU

Select **Play > Player vs CPU** then choose a difficulty:

- **Easy** — slow paddle, delayed reactions, frequently misses. Good for beginners.
- **Medium** — moderate tracking speed, occasional jitter. A fair opponent.
- **Hard** — fast paddle, minimal delay, tracks the ball tightly. Difficult to beat.

The CPU paddle only chases the ball when it is moving toward it. When the ball moves away, the CPU drifts back to center. This makes the AI feel more natural and less robotic.

## LAN multiplayer

No internet required. Works over any local network (Wi-Fi, Ethernet, mobile hotspot).

### Host

1. Run `python3 pong.py`
2. Select **Play > Multiplayer > Host Server**
3. Configure your server:
   - `p` — change the game port (default 9999)
   - `n` — set a custom server name (defaults to your hostname)
   - `w` — set the web dashboard port (default 8080)
4. Press `s` to start
5. Share the displayed IP address, or let other players find your server via automatic discovery

The management screen shows active rooms, connected players, live scores, and a real-time event log:

```
 Pong — Server: My Server
 IP: 192.168.1.100:9999   Web: http://192.168.1.100:8080   Uptime: 0h 2m 34s

 Active Rooms:
   > Classic  (2/2 PLAYING)  2-3  [Alice, Bob]
     Rally    (1/2)  [Charlie]

 Recent Events:
   [10:32] Room 'Classic' created
   [10:33] Alice (left) joined 'Classic'
   [10:34] Bob (right) joined 'Classic'

 j  join locally   k  kick player   q  stop server
```

From here you can:
- Press `j` to join your own server as a local client — play on 127.0.0.1, then return to the management screen when the game ends
- Press Enter on a room to see its player list, navigate with arrows, and press `k` to kick a player
- Press `q` to stop the server and go back to the menu

### Join

1. Run `python3 pong.py`
2. Select **Play > Multiplayer > Join Server**
3. An auto-discovery screen scans the LAN for servers broadcasting on UDP port 10000
4. Pick a detected server or select **[Enter IP Manually]** to type an address
5. Enter your display name when prompted
6. A room browser appears — pick an open room, a template name, or select **[New Game]** to create one
7. The match starts automatically once both players are in the same room

### Rooms

Rooms let multiple pairs play on the same server. Each room holds up to 2 players. When browsing, active rooms show their player count (`0/2`, `1/2`) or `FULL`. The room selector also shows 10 template names you can pick from to quickly start a themed game. Selecting **[New Game]** generates a random room name.

### Server browser

When joining, the server browser listens for UDP broadcast packets on port 10000. Any pong server on the LAN sends an announcement every 3 seconds containing its IP, port, and name. Detected servers appear in a list with live updates. Press `r` to rescan.

## Web dashboard

When hosting, pong starts a lightweight HTTP server that serves a live dashboard:

```
http://<server-ip>:8080
```

The dashboard shows:
- Server name, IP, and game port
- Uptime and total player count
- A table of active rooms showing status (waiting / playing / full), player names, current score, and room uptime
- An event log with timestamps

The page auto-refreshes every 2 seconds via a `/status` JSON endpoint. No external web server or dependencies needed — it is built into the game.

## Files

```
pong/
├── pong.py              # entry point (just launches src/pong/core.py)
├── LICENSE
├── README.md
├── SHA256SUMS              # integrity hash for src/pong/core.py
├── setup.sh              # dependency checker
├── description.txt       # short GitHub description
└── src/
    └── pong/
        ├── __init__.py    # exports main()
        └── core.py        # the entire game (~1760 lines)
```

Everything lives in one Python file (`src/pong/core.py`). The root `pong.py` is a tiny launcher. `setup.sh` is optional.

## Requirements

- **Python 3.6+** — check with `python3 --version`
- **curses** — built into Python on Linux, macOS, and Termux

### Termux

```bash
pkg install python ncurses
python3 pong.py
```

### Linux / macOS

curses ships with the system Python. No extra setup needed.

```bash
python3 pong.py
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `curses.error` on launch | Ensure TERM is set: `export TERM=xterm-256color` (pong does this automatically, but some shells override it) |
| No servers found (Join) | Check both machines are on the same LAN / Wi-Fi. Verify the host's firewall allows inbound TCP on the game port (default 9999) and UDP on port 10000. On Linux: `sudo ufw allow 9999/tcp; sudo ufw allow 10000/udp`. |
| `Connection refused` | The server must be started **before** the client tries to join. Verify the IP and port are correct. |
| Web dashboard not loading | Confirm the web port (default 8080) is not blocked. Check with `curl http://<server-ip>:8080/status`. The dashboard binds to `0.0.0.0`, so any device on the LAN can reach it. |
| CPU game doesn't save | Ensure `~/.pong/` is writable. The save file is `~/.pong/save.json`. Press `S` during a CPU game — a confirmation message appears. |
| Screen flickering | The menu only redraws on input. If you see flicker, your terminal may emulate escape sequences slowly. Try a lighter terminal emulator (e.g. Alacritty, Kitty) or set `TERM=vt100`. |
| Termux — keyboard issues | Termux's extra keys toggle may interfere with arrow keys. Use Volume-up + Q/W for arrows, or install a terminal with proper arrow key support. |
| Termux — no curses | Run `pkg install ncurses` and ensure Python is installed via `pkg install python`, not a third-party build. |

## Integrity verification

The game automatically verifies its own SHA256 hash against `SHA256SUMS` every time it starts. If the file has been tampered with or corrupted, the game refuses to run:

```
$ python3 pong.py
Integrity check FAILED for src/pong/core.py.
  Expected: abc123...
  Actual:   def456...
The file has been modified or corrupted. Refusing to run.
Re-download from: https://github.com/antoniosdimidgamedev/pong
```

You can also verify manually with:

```bash
sha256sum -c SHA256SUMS
```

## Setup script

```bash
chmod +x setup.sh
./setup.sh
```

Checks Python version, curses availability, and terminal size, then prints instructions.

## Architecture

### Thread model

```
main thread                        threads
┌──────────────────┐         ┌───────────────────┐
│ main_menu        │── spawn │→ game_loop (per client)
│ server_mgmt      │── spawn │→ _run_server (TCP accept)
│ play_vs_cpu      │── spawn │→ Room._loop (per room)
│ play_singleplayer│── spawn │→ _discovery_broadcaster (UDP)
│ play_client      │── spawn │→ _start_web_dashboard (HTTP)
└──────────────────┘         └───────────────────┘
```

- **Main thread** runs the curses UI (menus, management screen, game rendering).
- **_run_server** — single thread that accepts incoming TCP connections and spawns a handler thread per client.
- **Room._loop** — one per room; runs at 25 fps, reads input sets, updates `GameState`, and broadcasts state to both players.
- **_handle_client** — one per connected player; parses incoming JSON messages and dispatches to the room.
- **_discovery_broadcaster** — sends a UDP broadcast packet every 3 seconds announcing the server.
- **_start_web_dashboard** — minimal `http.server.HTTPServer` serving JSON status and auto-refreshing HTML.

### Game loop (server-side)

Each room's `_loop` runs continuously at `TICK` (0.04s ≈ 25 fps):

1. If fewer than 2 players present, set `playing = False` and skip.
2. Read input sets (`{"left": {"w"}, "right": {"up", "down"}}`) collected by handler threads.
3. Call `GameState.update()` which moves the ball, checks paddle collisions, and detects scoring.
4. Serialize the resulting state to a dict and broadcast as `{"type": "state", …}` to both players (or `{"type": "win", "winner": …}` on game end).
5. After a win, pause 2 seconds, reset the ball, and continue.

### Protocol: message types

All messages are line-delimited JSON over TCP. Each object is sent as a single line terminated by `\n`.

#### Client → Server

| Type | Fields | Purpose |
|---|---|---|
| `list_rooms` | — | Request the list of active rooms |
| `join` | `room`, `player_name` | Join (or create) a room with a display name |
| `input` | `keys` | Send the set of currently pressed keys |
| `chat` | `text` | Send a chat message (filtered server-side) |

#### Server → Client

| Type | Fields | Purpose |
|---|---|---|
| `room_list` | `rooms` | Response to `list_rooms`: array of `{name, players}` |
| `assign` | `player`, `name`, `opponent` | Tells the client their side, name, and opponent's name |
| `state` | ball/position fields | Current game state snapshot |
| `win` | `winner`, scores | Game over — `winner` is `"left"` or `"right"` |
| `chat` | `from`, `text` | A chat message from another player |
| `chat_history` | `messages` | Replay of recent chat history on join |
| `error` | `msg` | Server error message |

### Discovery protocol

- **Transport:** UDP broadcast on port 10000.
- **Frequency:** every 3 seconds.
- **Payload:** `{"type": "pong_announce", "port": <tcp_port>, "name": "<server_name>"}`
- **Client:** binds to port 10000, collects announcements into a list, deduplicates by IP+port, displays in the server browser.

### CPU AI

Each game tick, `cpu_inputs()` evaluates:

- **Ball direction** — only chase when the ball is moving toward the CPU paddle (or is very close).
- **Distance threshold** — if the ball is within N units of the paddle center, stop moving (avoids jitter).
- **Paddle speed** — how many pixels per tick the CPU paddle can move (Easy: 1, Medium: 2, Hard: 3).
- **Jitter** — random chance to skip a tick, simulating human reaction delay (Easy: 30%, Medium: 10%, Hard: 2%).

### Save file format

Stored in `~/.pong/save.json`:

```json
{
  "mode": "cpu",
  "difficulty": "medium",
  "left_score": 3,
  "right_score": 2,
  "left_y": 8,
  "right_y": 12,
  "ball_x": 42.5,
  "ball_y": 10.0,
  "ball_dir_x": 1,
  "ball_dir_y": -1,
  "width": 80,
  "height": 24
}
```

Only CPU games can be saved. The save is automatically deleted when a game ends or a new game starts.

### Curses rendering

- `stdscr.nodelay(1)` — non-blocking `getch()` for game loops (25 fps tick regardless of input).
- `stdscr.nodelay(0)` — blocking `getch()` for menus (only redraws on key press, no flicker).
- Colors: cyan (pair 1) for highlights, red (pair 2) for left paddle, white (pair 3) for text.
- Diagnostics line (`_DIAG`) drawn at the bottom of every screen: OS, kernel, architecture, Python version.

## License

MIT. Do whatever you want with it.

[![Star History](https://api.star-history.com/svg?repos=antoniosdimidgamedev/pong&type=Date)](https://star-history.com/#antoniosdimidgamedev/pong&Date)
